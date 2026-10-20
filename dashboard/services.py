from decimal import Decimal
from django.db.models import Sum, Count, Q, F
from orders.models import Order, OrderStatus, PaymentStatus
from catalog.models import Product


class DashboardReportService:
    """
    Business logic for administrative dashboard metrics, sales reports,
    and inventory stock alerts (FR-51, FR-54).
    """

    @staticmethod
    def get_summary_metrics():
        # Total Sales (Completed or Preparing orders with paid status)
        sales_data = (
            Order.objects.filter(payment_status=PaymentStatus.PAID)
            .exclude(status=OrderStatus.CANCELLED)
            .aggregate(
                total_revenue=Sum("total_amount"),
                paid_order_count=Count("id"),
            )
        )
        total_revenue = sales_data.get("total_revenue") or Decimal("0.00")
        paid_orders = sales_data.get("paid_order_count") or 0

        # Orders breakdown
        total_orders = Order.objects.count()
        pending_payment = Order.objects.filter(status=OrderStatus.PENDING_PAYMENT).count()
        awaiting_verification = Order.objects.filter(status=OrderStatus.AWAITING_VERIFICATION).count()
        preparing = Order.objects.filter(status=OrderStatus.PREPARING).count()
        shipped = Order.objects.filter(status=OrderStatus.SHIPPED).count()
        cancelled = Order.objects.filter(status=OrderStatus.CANCELLED).count()

        # Inventory Alerts (FR-51)
        out_of_stock_count = Product.objects.filter(is_active=True, stock__lte=0).count()
        low_stock_count = (
            Product.objects.filter(is_active=True, stock__gt=0, stock__lte=F("low_stock_threshold"))
            .count()
        )
        total_active_products = Product.objects.filter(is_active=True).count()

        return {
            "total_revenue": total_revenue,
            "paid_orders": paid_orders,
            "total_orders": total_orders,
            "pending_payment": pending_payment,
            "awaiting_verification": awaiting_verification,
            "preparing": preparing,
            "shipped": shipped,
            "cancelled": cancelled,
            "out_of_stock_count": out_of_stock_count,
            "low_stock_count": low_stock_count,
            "total_active_products": total_active_products,
        }

    @staticmethod
    def get_low_stock_products():
        """
        Get products that are out of stock or below threshold for staff alert (FR-51).
        """
        return (
            Product.objects.filter(is_active=True)
            .filter(Q(stock__lte=0) | Q(stock__lte=F("low_stock_threshold")))
            .select_related("brand", "category")
            .order_by("stock", "name")
        )
