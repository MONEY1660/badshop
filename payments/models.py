from django.db import models
from core.models import TimeStampedModel
from orders.models import Order, PaymentStatus


class Payment(TimeStampedModel):
    """
    Payment record holding payment method, status, amount, and optional proof of payment.
    Designed so real payment gateways (PromptPay, Stripe, Omise) can plug in later.
    """
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="payment",
        verbose_name="คำสั่งซื้อ",
    )
    payment_method = models.CharField(
        max_length=50,
        default="MANUAL_TRANSFER",
        verbose_name="ช่องทางชำระเงิน",
        help_text="เช่น โอนผ่านธนาคาร, PromptPay, บัตรเครดิต",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="ยอดเงิน (บาท)",
    )
    status = models.CharField(
        max_length=30,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name="สถานะการชำระเงิน",
    )
    proof_of_payment = models.ImageField(
        upload_to="payment_slips/%Y/%m/",
        null=True,
        blank=True,
        verbose_name="หลักฐานการโอนเงิน (สลิป)",
        help_text="เตรียมไว้สำหรับระบบอัปโหลดสลิปในอนาคต",
    )
    transaction_ref = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="รหัสอ้างอิงธุรกรรม / Slip Reference",
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="เวลาที่ชำระเงิน",
    )

    class Meta:
        verbose_name = "ข้อมูลการชำระเงิน"
        verbose_name_plural = "ข้อมูลการชำระเงินทั้งหมด"

    def __str__(self):
        return f"Payment for {self.order.order_number}: {self.amount} ฿ ({self.get_status_display()})"
