from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Brand, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "brand",
        "category",
        "price",
        "original_price",
        "stock_status_display",
        "is_active",
        "is_new",
        "is_bestseller",
        "is_sale",
    )
    list_filter = (
        "brand",
        "category",
        "is_active",
        "is_new",
        "is_bestseller",
        "is_sale",
    )
    search_fields = ("name", "brand__name", "category__name", "description")
    list_editable = ("is_active", "price")
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        ("ข้อมูลพื้นฐาน", {
            "fields": ("name", "slug", "brand", "category", "image", "description", "is_active")
        }),
        ("ราคาและสต็อก", {
            "fields": ("price", "original_price", "stock", "low_stock_threshold")
        }),
        ("ป้ายกำกับการตลาด", {
            "fields": ("is_new", "is_bestseller", "is_sale")
        }),
        ("คุณสมบัติไม้แบดมินตัน", {
            "fields": (
                "control_rating",
                "power_rating",
                "speed_rating",
                "shaft_flexibility",
                "weight_grip",
                "balance_point",
            )
        }),
    )

    def stock_status_display(self, obj):
        if obj.stock == 0:
            return format_html('<span style="color:red; font-weight:bold;">สินค้าหมด (0)</span>')
        elif obj.stock <= obj.low_stock_threshold:
            return format_html('<span style="color:orange; font-weight:bold;">ใกล้หมด ({})</span>', obj.stock)
        return format_html('<span style="color:green;">มีจำหน่าย ({})</span>', obj.stock)

    stock_status_display.short_description = "สถานะสต็อก"
