from decimal import Decimal
from django.conf import settings
from django.db import models
from django.db.models import Q
from core.models import TimeStampedModel
from catalog.models import Product


class OrderStatus(models.TextChoices):
    PENDING_PAYMENT = "PENDING_PAYMENT", "รอชำระเงิน"
    AWAITING_VERIFICATION = "AWAITING_VERIFICATION", "รอตรวจสอบ"
    PREPARING = "PREPARING", "กำลังเตรียมสินค้า"
    SHIPPED = "SHIPPED", "จัดส่งแล้ว"
    CANCELLED = "CANCELLED", "ยกเลิก"


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "รอชำระเงิน"
    PAID = "PAID", "ชำระเงินเรียบร้อย"
    FAILED = "FAILED", "การชำระเงินล้มเหลว"
    REFUNDED = "REFUNDED", "คืนเงินแล้ว"


class StockMovementType(models.TextChoices):
    DEDUCT_ORDER = "DEDUCT_ORDER", "ตัดสต็อกจากการสั่งซื้อ"
    RESTORE_CANCEL = "RESTORE_CANCEL", "คืนสต็อกจากการยกเลิกคำสั่งซื้อ"
    MANUAL_IN = "MANUAL_IN", "รับสินค้าเข้าสต็อก (Manual)"
    MANUAL_OUT = "MANUAL_OUT", "ตัดสินค้าออกจากสต็อก (Manual)"
    ADJUSTMENT = "ADJUSTMENT", "ปรับยอดสต็อกให้ตรงกับความจริง"


class Order(TimeStampedModel):
    order_number = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
        verbose_name="หมายเลขคำสั่งซื้อ",
        help_text="เช่น BD-20261020-0001",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="สมาชิกผู้สั่งซื้อ",
    )
    # Address snapshot at the time of order placement
    recipient_name = models.CharField(max_length=150, verbose_name="ชื่อผู้รับสินค้า")
    phone_number = models.CharField(max_length=20, verbose_name="เบอร์โทรศัพท์ผู้รับ")
    shipping_address = models.TextField(verbose_name="ที่อยู่จัดส่งสินค้าฉบับสมบูรณ์")

    # Status tracking
    status = models.CharField(
        max_length=30,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING_PAYMENT,
        db_index=True,
        verbose_name="สถานะคำสั่งซื้อ",
    )
    payment_status = models.CharField(
        max_length=30,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
        verbose_name="สถานะการชำระเงิน",
    )

    # Server-calculated financials
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="ยอดรวมสินค้า (บาท)",
    )
    shipping_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="ค่าจัดส่ง (บาท)",
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="ยอดชำระสุทธิ (บาท)",
    )

    # Tracking & Delivery
    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="หมายเลขติดตามพัสดุ (Tracking Number)",
    )
    customer_notes = models.TextField(
        blank=True,
        verbose_name="หมายเหตุจากลูกค้า",
    )
    admin_notes = models.TextField(
        blank=True,
        verbose_name="บันทึกภายในสำหรับเจ้าหน้าที่",
    )

    # Idempotency token to prevent duplicate order submission (NFR-07)
    idempotency_token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name="โทเค็นป้องกันการสั่งซื้อซ้ำ",
    )

    class Meta:
        verbose_name = "คำสั่งซื้อ"
        verbose_name_plural = "คำสั่งซื้อทั้งหมด"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(subtotal__gte=0),
                name="order_subtotal_gte_0",
            ),
            models.CheckConstraint(
                condition=Q(total_amount__gte=0),
                name="order_total_amount_gte_0",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.order_number} ({self.get_status_display()})"

    @property
    def can_be_cancelled(self):
        """
        Orders can only be cancelled by customer if still in PENDING_PAYMENT or AWAITING_VERIFICATION.
        Once PREPARING or SHIPPED, cannot be cancelled online by customer.
        """
        return self.status in [OrderStatus.PENDING_PAYMENT, OrderStatus.AWAITING_VERIFICATION]


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="คำสั่งซื้อ",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        verbose_name="สินค้าอ้างอิง",
    )
    # Snapshots at the time of purchase (FR-38)
    product_name = models.CharField(max_length=200, verbose_name="ชื่อสินค้า (Snapshot)")
    product_brand = models.CharField(max_length=100, verbose_name="ยี่ห้อสินค้า (Snapshot)")
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="ราคาต่อหน่วยขณะสั่งซื้อ",
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="จำนวน",
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="ราคารวมรายการ (บาท)",
    )

    class Meta:
        verbose_name = "รายการสินค้าในคำสั่งซื้อ"
        verbose_name_plural = "รายการสินค้าในคำสั่งซื้อทั้งหมด"
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="order_item_quantity_gt_0",
            ),
            models.CheckConstraint(
                condition=Q(subtotal__gte=0),
                name="order_item_subtotal_gte_0",
            ),
        ]

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"


class OrderStatusLog(TimeStampedModel):
    """
    Audit log for every status transition and payment status change (NFR-11).
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="status_logs",
        verbose_name="คำสั่งซื้อ",
    )
    from_status = models.CharField(max_length=50, verbose_name="สถานะเดิม")
    to_status = models.CharField(max_length=50, verbose_name="สถานะใหม่")
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="ผู้ดำเนินการเปลี่ยนสถานะ",
    )
    note = models.TextField(blank=True, verbose_name="บันทึกข้อความ / เหตุผล")

    class Meta:
        verbose_name = "ประวัติการเปลี่ยนสถานะคำสั่งซื้อ (Audit Log)"
        verbose_name_plural = "ประวัติการเปลี่ยนสถานะคำสั่งซื้อทั้งหมด"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order.order_number}: {self.from_status} -> {self.to_status}"


class StockMovement(TimeStampedModel):
    """
    Tracks inventory changes: deductions on order, restores on cancellation, manual updates.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="stock_movements",
        verbose_name="สินค้า",
    )
    movement_type = models.CharField(
        max_length=30,
        choices=StockMovementType.choices,
        verbose_name="ประเภทการเคลื่อนไหว",
    )
    quantity = models.IntegerField(
        verbose_name="จำนวนที่เปลี่ยน (+เข้า, -ออก)",
        help_text="ติดลบเมื่อตัดสต็อก, เป็นบวกเมื่อรับเข้าหรือคืนสต็อก",
    )
    remaining_stock = models.IntegerField(
        verbose_name="สต็อกคงเหลือหลังการเคลื่อนไหว",
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
        verbose_name="คำสั่งซื้อที่เกี่ยวข้อง (ถ้ามี)",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="ผู้ทำรายการ (ถ้ามี)",
    )
    note = models.TextField(blank=True, verbose_name="หมายเหตุ")

    class Meta:
        verbose_name = "บันทึกการเคลื่อนไหวสต็อก (Stock Movement)"
        verbose_name_plural = "บันทึกการเคลื่อนไหวสต็อกทั้งหมด"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.name} ({self.get_movement_type_display()} {self.quantity})"
