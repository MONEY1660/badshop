from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "payment_method", "amount", "status", "paid_at", "created_at")
    list_filter = ("status", "payment_method", "created_at")
    search_fields = ("order__order_number", "transaction_ref")
    readonly_fields = ("order", "amount", "created_at", "updated_at")
