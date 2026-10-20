from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Address


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "first_name", "last_name", "phone_number", "is_staff", "is_active", "date_joined")
    list_filter = ("is_staff", "is_active", "date_joined")
    search_fields = ("email", "first_name", "last_name", "phone_number")
    ordering = ("-date_joined",)
    
    fieldsets = (
        ("ข้อมูลเข้าสู่ระบบ", {"fields": ("email", "password")}),
        ("ข้อมูลส่วนตัว", {"fields": ("first_name", "last_name", "phone_number")}),
        ("สิทธิ์การใช้งาน", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("ข้อมูลระบบ", {"fields": ("date_joined", "last_login")}),
    )
    readonly_fields = ("date_joined", "last_login")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("recipient_name", "user", "phone_number", "province", "postal_code", "is_default")
    list_filter = ("province", "is_default")
    search_fields = ("recipient_name", "phone_number", "user__email", "address_line")
