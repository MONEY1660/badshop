from decimal import Decimal
from datetime import timedelta
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from core.models import TimeStampedModel
from catalog.models import Product


def default_cart_expiry():
    days = getattr(settings, "CART_EXPIRY_DAYS", 7)
    return timezone.now() + timedelta(days=days)


class Cart(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
        verbose_name="ผู้ใช้เจ้าของตะกร้า",
    )
    expires_at = models.DateTimeField(
        default=default_cart_expiry,
        verbose_name="หมดอายุเมื่อ",
    )

    class Meta:
        verbose_name = "ตะกร้าสินค้า"
        verbose_name_plural = "ตะกร้าสินค้าทั้งหมด"

    def __str__(self):
        return f"ตะกร้าของ {self.user.email}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.subtotal for item in self.items.all()) or Decimal("0.00")


class CartItem(TimeStampedModel):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="ตะกร้า",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="cart_items",
        verbose_name="สินค้า",
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="จำนวน",
    )

    class Meta:
        verbose_name = "รายการสินค้าในตะกร้า"
        verbose_name_plural = "รายการสินค้าในตะกร้าทั้งหมด"
        unique_together = ("cart", "product")
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="cart_item_quantity_gt_0",
            )
        ]

    def __str__(self):
        return f"{self.product.name} ({self.quantity} ชิ้น)"

    @property
    def subtotal(self):
        return self.product.price * self.quantity

    @property
    def has_sufficient_stock(self):
        return self.product.stock >= self.quantity
