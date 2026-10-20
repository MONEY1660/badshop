from django.contrib import admin
from .models import Order, OrderItem, OrderStatusLog, StockMovement


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_name", "product_brand", "unit_price", "quantity", "subtotal")


class OrderStatusLogInLine(admin.TabularInline):
    model = OrderStatusLog
    extra = 0
    readonly_fields = ("from_status", "to_status", "changed_by", "note", "created_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "user",
        "recipient_name",
        "status",
        "payment_status",
        "total_amount",
        "tracking_number",
        "created_at",
    )
    list_filter = ("status", "payment_status", "created_at")
    search_fields = ("order_number", "user__email", "recipient_name", "phone_number", "tracking_number")
    readonly_fields = ("order_number", "idempotency_token", "created_at", "updated_at", "subtotal", "total_amount")
    inlines = [OrderItemInline, OrderStatusLogInLine]


@admin.register(OrderStatusLog)
class OrderStatusLogAdmin(admin.ModelAdmin):
    list_display = ("order", "from_status", "to_status", "changed_by", "created_at")
    search_fields = ("order__order_number", "note")
    readonly_fields = ("order", "from_status", "to_status", "changed_by", "note", "created_at")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("product", "movement_type", "quantity", "remaining_stock", "order", "created_by", "created_at")
    list_filter = ("movement_type", "created_at")
    search_fields = ("product__name", "order__order_number", "note")
    readonly_fields = ("product", "movement_type", "quantity", "remaining_stock", "order", "created_by", "note", "created_at")
