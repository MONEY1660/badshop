from decimal import Decimal
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.text import slugify
from core.models import TimeStampedModel


class Category(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True, verbose_name="ชื่อหมวดหมู่")
    slug = models.SlugField(max_length=120, unique=True, verbose_name="Slug สำหรับ URL")
    description = models.TextField(blank=True, verbose_name="รายละเอียดหมวดหมู่")
    is_active = models.BooleanField(default=True, verbose_name="เปิดใช้งาน")

    class Meta:
        verbose_name = "หมวดหมู่สินค้า"
        verbose_name_plural = "หมวดหมู่สินค้าทั้งหมด"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class Brand(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True, verbose_name="ชื่อยี่ห้อ/แบรนด์")
    slug = models.SlugField(max_length=120, unique=True, verbose_name="Slug สำหรับ URL")
    description = models.TextField(blank=True, verbose_name="รายละเอียดแบรนด์")
    logo = models.ImageField(upload_to="brands/", blank=True, null=True, verbose_name="โลโก้แบรนด์")
    is_active = models.BooleanField(default=True, verbose_name="เปิดใช้งาน")

    class Meta:
        verbose_name = "ยี่ห้อ/แบรนด์"
        verbose_name_plural = "ยี่ห้อ/แบรนด์ทั้งหมด"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class Product(TimeStampedModel):
    name = models.CharField(max_length=200, db_index=True, verbose_name="ชื่อรุ่นไม้แบดมินตัน")
    slug = models.SlugField(max_length=230, unique=True, verbose_name="Slug สำหรับ URL")
    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="ยี่ห้อ/แบรนด์",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="หมวดหมู่",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="ราคาปัจจุบัน (บาท)",
        help_text="ราคาขายจริงที่ใช้คิดเงิน",
    )
    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="ราคาก่อนลด (บาท)",
        help_text="ราคาเต็มก่อนได้รับส่วนลด สำหรับแสดงขีดฆ่า",
    )
    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True,
        verbose_name="รูปภาพสินค้า",
    )
    description = models.TextField(blank=True, verbose_name="รายละเอียดสินค้า")
    stock = models.IntegerField(
        default=0,
        verbose_name="จำนวนสต็อกคงเหลือ",
        help_text="สต็อกต้องไม่ติดลบ",
    )
    low_stock_threshold = models.PositiveIntegerField(
        default=5,
        verbose_name="เกณฑ์เตือนสต็อกต่ำ",
    )
    
    # Marketing badges
    is_new = models.BooleanField(default=False, verbose_name="ป้ายสินค้าใหม่ (New)")
    is_bestseller = models.BooleanField(default=False, verbose_name="ป้ายสินค้าขายดี (Bestseller)")
    is_sale = models.BooleanField(default=False, verbose_name="ป้ายลดราคา (Sale)")
    is_active = models.BooleanField(default=True, db_index=True, verbose_name="เปิดจำหน่าย")

    # Badminton-specific specs (Ratings 1-10)
    control_rating = models.PositiveSmallIntegerField(
        default=5,
        verbose_name="ค่าการควบคุม (Control: 1-10)",
        help_text="ระดับ 1 ถึง 10",
    )
    power_rating = models.PositiveSmallIntegerField(
        default=5,
        verbose_name="ค่าพลังตบ/ความแรง (Power: 1-10)",
        help_text="ระดับ 1 ถึง 10",
    )
    speed_rating = models.PositiveSmallIntegerField(
        default=5,
        verbose_name="ค่าความเร็วหน้าไม้ (Speed: 1-10)",
        help_text="ระดับ 1 ถึง 10",
    )

    # Technical Specs
    shaft_flexibility = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="ความยืดหยุ่นก้าน",
        help_text="เช่น แข็งพิเศษ (Extra Stiff), แข็ง (Stiff), ปานกลาง (Medium), อ่อน (Flexible)",
    )
    weight_grip = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="น้ำหนักและขนาดด้ามจับ",
        help_text="เช่น 4U G5, 3U G5",
    )
    balance_point = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="จุดสมดุล",
        help_text="เช่น หัวหนัก (Head Heavy), สมดุล (Even Balance), หัวเบา (Head Light)",
    )

    class Meta:
        verbose_name = "ไม้แบดมินตัน"
        verbose_name_plural = "ไม้แบดมินตันทั้งหมด"
        ordering = ["-is_new", "-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(stock__gte=0),
                name="catalog_product_stock_gte_0",
            ),
            models.CheckConstraint(
                condition=Q(price__gt=0),
                name="catalog_product_price_gt_0",
            ),
        ]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["brand", "is_active"]),
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["price"]),
            models.Index(fields=["stock"]),
            models.Index(fields=["control_rating"]),
            models.Index(fields=["power_rating"]),
            models.Index(fields=["speed_rating"]),
        ]

    def __str__(self):
        return f"{self.brand.name} {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.brand.name}-{self.name}", allow_unicode=True)
        # Automatically set is_sale if original_price is greater than price
        if self.original_price and self.original_price > self.price:
            self.is_sale = True
        super().save(*args, **kwargs)

    @property
    def is_in_stock(self):
        return self.stock > 0

    @property
    def is_low_stock(self):
        return 0 < self.stock <= self.low_stock_threshold

    @property
    def discount_percent(self):
        if self.original_price and self.original_price > self.price:
            diff = self.original_price - self.price
            pct = (diff / self.original_price) * Decimal(100)
            return round(pct)
        return 0
