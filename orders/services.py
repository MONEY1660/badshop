import random
from datetime import datetime
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import Order, OrderItem, OrderStatus, PaymentStatus, OrderStatusLog, StockMovement, StockMovementType
from catalog.models import Product
from cart.models import Cart


class OrderService:
    """
    Business logic for order processing, atomic inventory deduction,
    idempotency enforcement, audit logging, and cancellations.
    """

    SHIPPING_FEE_STANDARD = Decimal("50.00")
    FREE_SHIPPING_THRESHOLD = Decimal("1500.00")

    @classmethod
    def calculate_shipping_fee(cls, subtotal: Decimal) -> Decimal:
        """
        Free shipping for orders >= 1,500 THB, otherwise 50 THB.
        Always calculated strictly on server using Decimal (NFR-06).
        """
        if subtotal >= cls.FREE_SHIPPING_THRESHOLD:
            return Decimal("0.00")
        return cls.SHIPPING_FEE_STANDARD

    @classmethod
    def generate_order_number(cls) -> str:
        """
        Generate guaranteed unique order number in format BD-YYYYMMDD-XXXX (FR-37).
        """
        date_str = timezone.now().strftime("%Y%m%d")
        # Try finding the sequential count for today
        today_prefix = f"BD-{date_str}-"
        count_today = Order.objects.filter(order_number__startswith=today_prefix).count()
        candidate = f"{today_prefix}{count_today + 1:04d}"
        
        # In case of concurrency/gaps, loop until unique
        while Order.objects.filter(order_number=candidate).exists():
            rnd_suffix = random.randint(1000, 9999)
            candidate = f"{today_prefix}{rnd_suffix:04d}"
        return candidate

    @classmethod
    @transaction.atomic
    def create_order_from_cart(cls, user, address, idempotency_token: str, customer_notes: str = "") -> Order:
        """
        Atomically create an order from current cart, deduct stock with row locks,
        check idempotency, and create audit logs (FR-34, FR-35, FR-37, FR-38, FR-41, NFR-06, NFR-07).
        """
        if not idempotency_token:
            raise ValueError("จำเป็นต้องมี Idempotency token เพื่อป้องกันการสั่งซื้อซ้ำ")

        # 1. Check for duplicate order via idempotency token (NFR-07)
        existing_order = Order.objects.filter(idempotency_token=idempotency_token).first()
        if existing_order:
            return existing_order

        # 2. Get user's cart and lock items
        try:
            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            raise ValueError("ไม่พบตะกร้าสินค้า")

        cart_items = list(cart.items.select_related("product").all())
        if not cart_items:
            raise ValueError("ไม่มีสินค้าในตะกร้า ไม่สามารถสั่งซื้อได้")

        # Lock products in deterministic order to avoid deadlocks
        product_ids = sorted([item.product_id for item in cart_items])
        locked_products = {
            p.id: p for p in Product.objects.select_for_update().filter(id__in=product_ids)
        }

        # 3. Verify stock availability and validate active status
        for item in cart_items:
            product = locked_products.get(item.product_id)
            if not product or not product.is_active:
                raise ValueError(f"สินค้า '{item.product.name}' ไม่อยู่ในสถานะพร้อมจำหน่าย")
            if product.stock < item.quantity:
                raise ValueError(
                    f"สินค้า '{product.name}' มีคงเหลือ {product.stock} ชิ้น ไม่เพียงพอกับจำนวนที่ต้องการ ({item.quantity} ชิ้น)"
                )

        # 4. Calculate server-side financials using Decimal strictly
        subtotal = Decimal("0.00")
        for item in cart_items:
            product = locked_products[item.product_id]
            subtotal += product.price * item.quantity

        shipping_fee = cls.calculate_shipping_fee(subtotal)
        total_amount = subtotal + shipping_fee

        # 5. Format address snapshot string
        address_snapshot = (
            f"ผู้รับ: {address.recipient_name}\n"
            f"เบอร์โทร: {address.phone_number}\n"
            f"ที่อยู่: {address.address_line} ต./แขวง {address.subdistrict} "
            f"อ./เขต {address.district} จ.{address.province} {address.postal_code}"
        )

        order_number = cls.generate_order_number()

        # 6. Create Order record
        order = Order.objects.create(
            order_number=order_number,
            user=user,
            recipient_name=address.recipient_name,
            phone_number=address.phone_number,
            shipping_address=address_snapshot,
            status=OrderStatus.PENDING_PAYMENT,
            payment_status=PaymentStatus.PENDING,
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            total_amount=total_amount,
            customer_notes=customer_notes.strip(),
            idempotency_token=idempotency_token,
        )

        # 7. Create OrderItems & Deduct Stock with StockMovement tracking (FR-41)
        for item in cart_items:
            product = locked_products[item.product_id]
            item_subtotal = product.price * item.quantity

            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                product_brand=product.brand.name,
                unit_price=product.price,
                quantity=item.quantity,
                subtotal=item_subtotal,
            )

            # Deduct inventory atomically
            product.stock -= item.quantity
            product.save(update_fields=["stock", "updated_at"])

            # Record stock movement
            StockMovement.objects.create(
                product=product,
                movement_type=StockMovementType.DEDUCT_ORDER,
                quantity=-item.quantity,
                remaining_stock=product.stock,
                order=order,
                created_by=user,
                note=f"ตัดสต็อกสำหรับคำสั่งซื้อ {order.order_number}",
            )

        # 8. Create initial OrderStatusLog (NFR-11)
        OrderStatusLog.objects.create(
            order=order,
            from_status="NONE",
            to_status=OrderStatus.PENDING_PAYMENT,
            changed_by=user,
            note="สร้างคำสั่งซื้อสำเร็จ (รอชำระเงิน)",
        )

        # 9. Clear user's cart items
        cart.items.all().delete()

        return order

    @classmethod
    @transaction.atomic
    def cancel_order(cls, order: Order, user, reason: str = "") -> Order:
        """
        Cancel an order and atomically restore stock (FR-46, FR-41).
        Enforces customer cancellation business rules:
        - Customer can only cancel their own order while PENDING_PAYMENT or AWAITING_VERIFICATION.
        - Staff can cancel anytime unless already cancelled.
        """
        is_staff = getattr(user, "is_staff", False)
        if not is_staff and order.user != user:
            raise PermissionError("คุณไม่มีสิทธิ์ในการยกเลิกคำสั่งซื้อนี้")

        if not is_staff and not order.can_be_cancelled:
            raise ValueError("คำสั่งซื้อนี้กำลังเตรียมสินค้าหรือจัดส่งแล้ว ไม่สามารถยกเลิกผ่านระบบได้")

        if order.status == OrderStatus.CANCELLED:
            raise ValueError("คำสั่งซื้อนี้ถูกยกเลิกไปแล้ว")

        old_status = order.status

        # Lock products and restore stock
        order_items = list(order.items.select_related("product").all())
        product_ids = sorted([item.product_id for item in order_items if item.product_id])
        locked_products = {
            p.id: p for p in Product.objects.select_for_update().filter(id__in=product_ids)
        }

        for item in order_items:
            if item.product_id and item.product_id in locked_products:
                product = locked_products[item.product_id]
                product.stock += item.quantity
                product.save(update_fields=["stock", "updated_at"])

                StockMovement.objects.create(
                    product=product,
                    movement_type=StockMovementType.RESTORE_CANCEL,
                    quantity=item.quantity,
                    remaining_stock=product.stock,
                    order=order,
                    created_by=user,
                    note=f"คืนสต็อกจากการยกเลิกคำสั่งซื้อ {order.order_number}",
                )

        order.status = OrderStatus.CANCELLED
        order.save(update_fields=["status", "updated_at"])

        OrderStatusLog.objects.create(
            order=order,
            from_status=old_status,
            to_status=OrderStatus.CANCELLED,
            changed_by=user,
            note=f"ยกเลิกคำสั่งซื้อ: {reason or 'ลูกค้ายกเลิก'}",
        )

        return order

    @classmethod
    @transaction.atomic
    def update_order_status(cls, order: Order, new_status: str, changed_by=None, note: str = "") -> Order:
        """
        Update order status with audit log (FR-53, NFR-11).
        If changing to CANCELLED, restores inventory.
        """
        if order.status == new_status:
            return order

        old_status = order.status

        # If transitioning to CANCELLED, restore inventory
        if new_status == OrderStatus.CANCELLED and old_status != OrderStatus.CANCELLED:
            return cls.cancel_order(order, changed_by, reason=note or "เจ้าหน้าที่เปลี่ยนสถานะเป็นยกเลิก")

        order.status = new_status
        order.save(update_fields=["status", "updated_at"])

        OrderStatusLog.objects.create(
            order=order,
            from_status=old_status,
            to_status=new_status,
            changed_by=changed_by,
            note=note,
        )
        return order

    @classmethod
    @transaction.atomic
    def update_payment_status(cls, order: Order, new_payment_status: str, changed_by=None, note: str = "") -> Order:
        """
        Update payment status and create audit log (FR-53, NFR-11).
        """
        if order.payment_status == new_payment_status:
            return order

        old_payment = order.payment_status
        order.payment_status = new_payment_status

        # If payment marked as PAID and order still PENDING_PAYMENT, move order status to PREPARING
        if new_payment_status == PaymentStatus.PAID and order.status == OrderStatus.PENDING_PAYMENT:
            order.status = OrderStatus.PREPARING

        order.save(update_fields=["payment_status", "status", "updated_at"])

        OrderStatusLog.objects.create(
            order=order,
            from_status=f"PAYMENT_{old_payment}",
            to_status=f"PAYMENT_{new_payment_status}",
            changed_by=changed_by,
            note=note or f"อัปเดตสถานะการชำระเงินเป็น {order.get_payment_status_display()}",
        )
        return order
