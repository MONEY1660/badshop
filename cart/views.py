from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import Cart, CartItem
from .services import CartService
from catalog.models import Product
from orders.services import OrderService


@login_required
def cart_detail(request):
    """
    Shopping cart detail view displaying items, thumbnail, price, quantity,
    subtotal, and real-time stock verification (FR-30, FR-31, FR-32, FR-33).
    """
    cart = CartService.get_or_create_cart(request.user)
    items = cart.items.select_related("product", "product__brand").all()

    # Verify inventory availability (FR-32)
    has_sufficient_stock, stock_errors = CartService.validate_cart_stock(cart)

    # Server-side calculation using Decimal strictly (NFR-06)
    subtotal = cart.subtotal
    shipping_fee = OrderService.calculate_shipping_fee(subtotal) if items else Decimal("0.00")
    total_amount = subtotal + shipping_fee

    # Free shipping progress
    free_shipping_threshold = OrderService.FREE_SHIPPING_THRESHOLD
    remaining_for_free_shipping = max(Decimal("0.00"), free_shipping_threshold - subtotal)
    free_shipping_progress = min(100, int((subtotal / free_shipping_threshold) * 100)) if subtotal > 0 else 0

    context = {
        "cart": cart,
        "items": items,
        "subtotal": subtotal,
        "shipping_fee": shipping_fee,
        "total_amount": total_amount,
        "has_sufficient_stock": has_sufficient_stock,
        "stock_errors": stock_errors,
        "free_shipping_threshold": free_shipping_threshold,
        "remaining_for_free_shipping": remaining_for_free_shipping,
        "free_shipping_progress": free_shipping_progress,
    }
    return render(request, "cart/cart_detail.html", context)


@login_required
def cart_add(request):
    """
    Add product to shopping cart (FR-28, FR-19).
    """
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        try:
            quantity = int(request.POST.get("quantity", 1))
        except (ValueError, TypeError):
            quantity = 1

        if not product_id:
            messages.error(request, "ไม่พบรหัสสินค้าที่ต้องการเพิ่ม")
            return redirect("catalog:product_list")

        try:
            item = CartService.add_to_cart(request.user, product_id, quantity)
            messages.success(request, f"เพิ่ม '{item.product.name}' จำนวน {quantity} ชิ้น ลงตะกร้าแล้ว")
        except Product.DoesNotExist:
            messages.error(request, "ไม่พบสินค้าที่ระบุ หรือสินค้าปิดจำหน่ายแล้ว")
        except ValueError as e:
            messages.error(request, str(e))

    return redirect("cart:cart_detail")


@login_required
def cart_update(request, item_id):
    """
    Update item quantity in cart or remove if quantity <= 0 (FR-29).
    """
    if request.method == "POST":
        action = request.POST.get("action")  # 'increase', 'decrease', or 'set'
        cart = CartService.get_or_create_cart(request.user)
        item = get_object_or_404(CartItem, id=item_id, cart=cart)

        try:
            if action == "increase":
                new_qty = item.quantity + 1
            elif action == "decrease":
                new_qty = item.quantity - 1
            else:
                new_qty = int(request.POST.get("quantity", item.quantity))

            CartService.update_quantity(request.user, item.id, new_qty)
            messages.success(request, f"อัปเดตจำนวนสินค้า '{item.product.name}' เรียบร้อยแล้ว")
        except ValueError as e:
            messages.error(request, str(e))

    return redirect("cart:cart_detail")


@login_required
def cart_remove(request, item_id):
    """
    Remove an item completely from cart (FR-29).
    """
    if request.method == "POST":
        cart = CartService.get_or_create_cart(request.user)
        item = CartItem.objects.filter(id=item_id, cart=cart).first()
        if item:
            product_name = item.product.name
            CartService.remove_item(request.user, item_id)
            messages.success(request, f"ลบ '{product_name}' ออกจากตะกร้าเรียบร้อยแล้ว")

    return redirect("cart:cart_detail")


@login_required
def cart_proceed_checkout(request):
    """
    Validate inventory before proceeding to checkout screen (FR-32).
    """
    cart = CartService.get_or_create_cart(request.user)
    if not cart.items.exists():
        messages.error(request, "ไม่มีสินค้าในตะกร้า ไม่สามารถดำเนินการสั่งซื้อได้")
        return redirect("cart:cart_detail")

    is_valid, errors = CartService.validate_cart_stock(cart)
    if not is_valid:
        for err in errors:
            messages.error(request, f"สต็อกไม่เพียงพอ: {err}")
        return redirect("cart:cart_detail")

    # In Phase 4 this routes to orders:checkout
    # For now in Phase 3, confirm success validation
    messages.info(request, "ตรวจสอบสต็อกสินค้าเรียบร้อย พร้อมดำเนินการสั่งซื้อในขั้นตอนถัดไป (เฟส 4)")
    return redirect("cart:cart_detail")
