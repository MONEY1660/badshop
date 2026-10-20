from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import Cart, CartItem, default_cart_expiry
from catalog.models import Product


class CartService:
    """
    Business logic for shopping cart operations.
    """

    @staticmethod
    def get_or_create_cart(user):
        cart, created = Cart.objects.get_or_create(
            user=user,
            defaults={"expires_at": default_cart_expiry()},
        )
        # If cart has expired, clear items and renew expiry date
        if cart.is_expired:
            cart.items.all().delete()
            cart.expires_at = default_cart_expiry()
            cart.save()
        return cart

    @staticmethod
    @transaction.atomic
    def add_to_cart(user, product_id, quantity=1):
        cart = CartService.get_or_create_cart(user)
        product = Product.objects.select_for_update().get(id=product_id, is_active=True)

        if quantity <= 0:
            raise ValueError("จำนวนสินค้าต้องมากกว่า 0")

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": quantity},
        )
        if not created:
            new_qty = item.quantity + quantity
            if new_qty > product.stock:
                raise ValueError(f"สินค้าคงเหลือมีเพียง {product.stock} ชิ้น ไม่สามารถเพิ่มได้")
            item.quantity = new_qty
            item.save()
        else:
            if quantity > product.stock:
                raise ValueError(f"สินค้าคงเหลือมีเพียง {product.stock} ชิ้น ไม่สามารถเพิ่มได้")

        # Refresh cart expiry on modification
        cart.expires_at = default_cart_expiry()
        cart.save(update_fields=["expires_at", "updated_at"])
        return item

    @staticmethod
    @transaction.atomic
    def update_quantity(user, item_id, quantity):
        cart = CartService.get_or_create_cart(user)
        item = CartItem.objects.select_for_update().select_related("product").get(id=item_id, cart=cart)

        if quantity <= 0:
            item.delete()
            return None

        if quantity > item.product.stock:
            raise ValueError(f"สินค้า '{item.product.name}' มีคงเหลือเพียง {item.product.stock} ชิ้น")

        item.quantity = quantity
        item.save()
        cart.expires_at = default_cart_expiry()
        cart.save(update_fields=["expires_at", "updated_at"])
        return item

    @staticmethod
    def remove_item(user, item_id):
        cart = CartService.get_or_create_cart(user)
        CartItem.objects.filter(id=item_id, cart=cart).delete()

    @staticmethod
    def validate_cart_stock(cart):
        """
        Verify all items in cart have sufficient stock (FR-32).
        Returns (is_valid, list_of_errors).
        """
        errors = []
        for item in cart.items.select_related("product").all():
            if not item.product.is_active:
                errors.append(f"สินค้า '{item.product.name}' ปิดจำหน่ายแล้ว")
            elif item.quantity > item.product.stock:
                errors.append(f"สินค้า '{item.product.name}' มีคงเหลือ {item.product.stock} ชิ้น (ในตะกร้ามี {item.quantity} ชิ้น)")
        return len(errors) == 0, errors
