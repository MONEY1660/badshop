from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from core.models import TimeStampedModel
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model using email as the unique username.
    """
    email = models.EmailField(
        unique=True,
        max_length=255,
        verbose_name="อีเมล",
        db_index=True,
        error_messages={"unique": "อีเมลนี้มีผู้ใช้งานในระบบแล้ว"},
    )
    first_name = models.CharField(max_length=150, verbose_name="ชื่อจริง")
    last_name = models.CharField(max_length=150, verbose_name="นามสกุล")
    phone_number = models.CharField(max_length=20, blank=True, verbose_name="เบอร์โทรศัพท์")
    
    is_active = models.BooleanField(default=True, verbose_name="เปิดใช้งาน")
    is_staff = models.BooleanField(default=False, verbose_name="สถานะผู้ดูแลระบบ/ทีมงาน")
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="วันที่สมัครสมาชิก")

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = "ผู้ใช้งาน"
        verbose_name_plural = "ผู้ใช้งานทั้งหมด"
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.email} ({self.get_full_name()})"

    def get_full_name(self):
        full = f"{self.first_name} {self.last_name}".strip()
        return full if full else self.email

    def get_short_name(self):
        return self.first_name or self.email


class Address(TimeStampedModel):
    """
    Shipping address model for members.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="addresses",
        verbose_name="สมาชิกเจ้าของที่อยู่",
    )
    recipient_name = models.CharField(max_length=150, verbose_name="ชื่อผู้รับสินค้า")
    phone_number = models.CharField(max_length=20, verbose_name="เบอร์โทรศัพท์ผู้รับ")
    address_line = models.CharField(max_length=255, verbose_name="ที่อยู่ (บ้านเลขที่ / ซอย / ถนน / อาคาร)")
    subdistrict = models.CharField(max_length=100, verbose_name="แขวง / ตำบล")
    district = models.CharField(max_length=100, verbose_name="เขต / อำเภอ")
    province = models.CharField(max_length=100, verbose_name="จังหวัด")
    postal_code = models.CharField(max_length=10, verbose_name="รหัสไปรษณีย์")
    is_default = models.BooleanField(default=False, verbose_name="ตั้งเป็นที่อยู่จัดส่งเริ่มต้น")

    class Meta:
        verbose_name = "ที่อยู่จัดส่ง"
        verbose_name_plural = "ที่อยู่จัดส่งทั้งหมด"
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.recipient_name} - {self.address_line}, {self.subdistrict}, {self.district}, {self.province} {self.postal_code}"

    def full_address(self):
        return f"{self.address_line} ต./แขวง {self.subdistrict} อ./เขต {self.district} จ.{self.province} {self.postal_code}"
