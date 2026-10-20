from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Address

User = get_user_model()


class RegisterForm(forms.Form):
    """
    Form for registering a new user including basic personal info,
    credentials, and shipping address (FR-22, FR-23).
    """
    first_name = forms.CharField(
        max_length=150,
        label="ชื่อจริง",
        widget=forms.TextInput(attrs={
            "class": "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 focus:bg-white",
            "placeholder": "เช่น สมชาย",
        }),
    )
    last_name = forms.CharField(
        max_length=150,
        label="นามสกุล",
        widget=forms.TextInput(attrs={
            "class": "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 focus:bg-white",
            "placeholder": "เช่น รักดี",
        }),
    )
    email = forms.EmailField(
        label="อีเมล (ใช้เป็นบัญชีเข้าสู่ระบบ)",
        widget=forms.EmailInput(attrs={
            "class": "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 focus:bg-white",
            "placeholder": "name@example.com",
        }),
    )
    phone_number = forms.CharField(
        max_length=20,
        label="เบอร์โทรศัพท์",
        widget=forms.TextInput(attrs={
            "class": "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 focus:bg-white",
            "placeholder": "0812345678",
        }),
    )
    password = forms.CharField(
        label="รหัสผ่าน (อย่างน้อย 8 ตัวอักษร)",
        widget=forms.PasswordInput(attrs={
            "class": "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 focus:bg-white",
            "placeholder": "••••••••",
        }),
    )
    confirm_password = forms.CharField(
        label="ยืนยันรหัสผ่าน",
        widget=forms.PasswordInput(attrs={
            "class": "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 focus:bg-white",
            "placeholder": "••••••••",
        }),
    )

    # Initial shipping address fields (FR-22)
    address_line = forms.CharField(
        max_length=255,
        label="ที่อยู่ (บ้านเลขที่ / ถนน / ซอย / อาคาร)",
        widget=forms.TextInput(attrs={
            "class": "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 focus:bg-white",
            "placeholder": "เช่น 123/45 ถนนสุขุมวิท ซอย 55",
        }),
    )
    subdistrict = forms.CharField(
        max_length=100,
        label="แขวง / ตำบล",
        widget=forms.TextInput(attrs={
            "class": "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 focus:bg-white",
            "placeholder": "คลองตันเหนือ",
        }),
    )
    district = forms.CharField(
        max_length=100,
        label="เขต / อำเภอ",
        widget=forms.TextInput(attrs={
            "class": "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 focus:bg-white",
            "placeholder": "วัฒนา",
        }),
    )
    province = forms.CharField(
        max_length=100,
        label="จังหวัด",
        widget=forms.TextInput(attrs={
            "class": "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 focus:bg-white",
            "placeholder": "กรุงเทพมหานคร",
        }),
    )
    postal_code = forms.CharField(
        max_length=10,
        label="รหัสไปรษณีย์",
        widget=forms.TextInput(attrs={
            "class": "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 focus:bg-white",
            "placeholder": "10110",
        }),
    )

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("อีเมลนี้ถูกใช้งานแล้วในระบบ กรุณาใช้อีเมลอื่นหรือเข้าสู่ระบบ")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password:
            if password != confirm_password:
                self.add_error("confirm_password", "รหัสผ่านทั้งสองช่องไม่ตรงกัน")
            else:
                validate_password(password)
        return cleaned_data


class LoginForm(forms.Form):
    """
    Form for member authentication (FR-26).
    """
    email = forms.EmailField(
        label="อีเมล",
        widget=forms.EmailInput(attrs={
            "class": "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 focus:bg-white",
            "placeholder": "name@example.com",
            "autofocus": True,
        }),
    )
    password = forms.CharField(
        label="รหัสผ่าน",
        widget=forms.PasswordInput(attrs={
            "class": "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 focus:bg-white",
            "placeholder": "••••••••",
        }),
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email", "").strip().lower()
        password = cleaned_data.get("password")

        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise ValidationError("อีเมลหรือรหัสผ่านไม่ถูกต้อง กรุณาตรวจสอบใหม่อีกครั้ง")
            if not user.is_active:
                raise ValidationError("บัญชีผู้ใช้นี้ถูกปิดใช้งาน กรุณาติดต่อผู้ดูแลระบบ")
            self.user = user
        return cleaned_data


class ProfileUpdateForm(forms.ModelForm):
    """
    Form for updating basic profile info (FR-24).
    """
    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone_number"]
        widgets = {
            "first_name": forms.TextInput(attrs={
                "class": "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 focus:bg-white",
            }),
            "last_name": forms.TextInput(attrs={
                "class": "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 focus:bg-white",
            }),
            "phone_number": forms.TextInput(attrs={
                "class": "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 focus:bg-white",
            }),
        }
        labels = {
            "first_name": "ชื่อจริง",
            "last_name": "นามสกุล",
            "phone_number": "เบอร์โทรศัพท์",
        }


class AddressForm(forms.ModelForm):
    """
    Form for adding and editing shipping addresses (FR-24).
    """
    class Meta:
        model = Address
        fields = [
            "recipient_name",
            "phone_number",
            "address_line",
            "subdistrict",
            "district",
            "province",
            "postal_code",
            "is_default",
        ]
        widgets = {
            "recipient_name": forms.TextInput(attrs={
                "class": "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 focus:bg-white",
                "placeholder": "ชื่อ-นามสกุลผู้รับสินค้า",
            }),
            "phone_number": forms.TextInput(attrs={
                "class": "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 focus:bg-white",
                "placeholder": "0812345678",
            }),
            "address_line": forms.TextInput(attrs={
                "class": "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 focus:bg-white",
                "placeholder": "บ้านเลขที่ / ซอย / ถนน / อาคาร",
            }),
            "subdistrict": forms.TextInput(attrs={
                "class": "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 focus:bg-white",
                "placeholder": "แขวง / ตำบล",
            }),
            "district": forms.TextInput(attrs={
                "class": "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 focus:bg-white",
                "placeholder": "เขต / อำเภอ",
            }),
            "province": forms.TextInput(attrs={
                "class": "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 focus:bg-white",
                "placeholder": "จังหวัด",
            }),
            "postal_code": forms.TextInput(attrs={
                "class": "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 focus:bg-white",
                "placeholder": "รหัสไปรษณีย์ 5 หลัก",
            }),
            "is_default": forms.CheckboxInput(attrs={
                "class": "rounded border-slate-300 text-emerald-600 focus:ring-emerald-500",
            }),
        }
        labels = {
            "recipient_name": "ชื่อผู้รับสินค้า",
            "phone_number": "เบอร์โทรศัพท์ผู้รับ",
            "address_line": "ที่อยู่",
            "subdistrict": "แขวง / ตำบล",
            "district": "เขต / อำเภอ",
            "province": "จังหวัด",
            "postal_code": "รหัสไปรษณีย์",
            "is_default": "ตั้งเป็นที่อยู่จัดส่งเริ่มต้น",
        }


class ChangePasswordForm(forms.Form):
    """
    Form for secure password change (FR-25).
    """
    old_password = forms.CharField(
        label="รหัสผ่านปัจจุบัน",
        widget=forms.PasswordInput(attrs={
            "class": "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 focus:bg-white",
            "placeholder": "••••••••",
        }),
    )
    new_password = forms.CharField(
        label="รหัสผ่านใหม่",
        widget=forms.PasswordInput(attrs={
            "class": "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 focus:bg-white",
            "placeholder": "••••••••",
        }),
    )
    confirm_new_password = forms.CharField(
        label="ยืนยันรหัสผ่านใหม่",
        widget=forms.PasswordInput(attrs={
            "class": "w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 focus:bg-white",
            "placeholder": "••••••••",
        }),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get("old_password")
        if not self.user.check_password(old_password):
            raise ValidationError("รหัสผ่านปัจจุบันไม่ถูกต้อง")
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_new_password = cleaned_data.get("confirm_new_password")

        if new_password and confirm_new_password:
            if new_password != confirm_new_password:
                self.add_error("confirm_new_password", "รหัสผ่านใหม่ทั้งสองช่องไม่ตรงกัน")
            else:
                validate_password(new_password, self.user)
        return cleaned_data
