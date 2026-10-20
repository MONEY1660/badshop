from abc import ABC, abstractmethod
from decimal import Decimal
from django.utils import timezone
from .models import Payment
from orders.models import Order, PaymentStatus, OrderStatus
from orders.services import OrderService


class PaymentServiceInterface(ABC):
    """
    Standard interface for all payment providers (Manual Transfer, PromptPay QR, Stripe, Omise, etc.)
    Allows plugging in real payment gateways later without altering Order or Checkout logic.
    """

    @abstractmethod
    def initiate_payment(self, order: Order) -> Payment:
        """Create or initialize a pending payment record for an order."""
        pass

    @abstractmethod
    def verify_payment(self, payment_id: int, **kwargs) -> bool:
        """Verify the payment with external provider or slip check."""
        pass

    @abstractmethod
    def handle_webhook(self, payload: dict) -> bool:
        """Handle incoming webhook notification from gateway."""
        pass


class ManualBankTransferPaymentService(PaymentServiceInterface):
    """
    Default implementation for current phase:
    Creates a pending payment record with placeholder message:
    'ร้านค้าจะติดต่อแจ้งช่องทางชำระเงิน'
    """

    def initiate_payment(self, order: Order) -> Payment:
        payment, created = Payment.objects.get_or_create(
            order=order,
            defaults={
                "payment_method": "MANUAL_TRANSFER",
                "amount": order.total_amount,
                "status": PaymentStatus.PENDING,
            },
        )
        return payment

    def verify_payment(self, payment_id: int, verified_by=None, note: str = "") -> bool:
        try:
            payment = Payment.objects.get(id=payment_id)
            payment.status = PaymentStatus.PAID
            payment.paid_at = timezone.now()
            payment.save(update_fields=["status", "paid_at", "updated_at"])

            # Synchronize with Order and audit log
            OrderService.update_payment_status(
                order=payment.order,
                new_payment_status=PaymentStatus.PAID,
                changed_by=verified_by,
                note=note or "ยืนยันการชำระเงินผ่านระบบจัดการหลังบ้าน",
            )
            return True
        except Payment.DoesNotExist:
            return False

    def handle_webhook(self, payload: dict) -> bool:
        # Not applicable for manual bank transfer
        return True


# Default instance to be used across the application
payment_service = ManualBankTransferPaymentService()
