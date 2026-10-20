from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from .forms import RegisterForm, LoginForm, ProfileUpdateForm, AddressForm, ChangePasswordForm
from .models import Address
from .services import AccountService


def register_view(request):
    """
    Member registration view (FR-22, FR-23).
    """
    if request.user.is_authenticated:
        return redirect("catalog:product_list")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                # 1. Register User via AccountService (NFR-08)
                user = AccountService.register_user(
                    email=form.cleaned_data["email"],
                    password=form.cleaned_data["password"],
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    phone_number=form.cleaned_data["phone_number"],
                )

                # 2. Save initial shipping address
                AccountService.save_address(
                    user=user,
                    recipient_name=f"{user.first_name} {user.last_name}",
                    phone_number=user.phone_number,
                    address_line=form.cleaned_data["address_line"],
                    subdistrict=form.cleaned_data["subdistrict"],
                    district=form.cleaned_data["district"],
                    province=form.cleaned_data["province"],
                    postal_code=form.cleaned_data["postal_code"],
                    is_default=True,
                )

                # 3. Log in automatically and redirect
                login(request, user)
                messages.success(request, f"ยินดีต้อนรับคุณ {user.first_name}! สมัครสมาชิกเรียบร้อยแล้ว")
                return redirect("catalog:product_list")
            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "กรุณาตรวจสอบข้อมูลในแบบฟอร์มให้ถูกต้อง")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    """
    Member login view with redirect to requested page (FR-26).
    """
    if request.user.is_authenticated:
        return redirect("catalog:product_list")

    next_url = request.GET.get("next") or request.POST.get("next") or "catalog:product_list"

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.user
            login(request, user)
            messages.success(request, f"เข้าสู่ระบบสำเร็จ ยินดีต้อนรับคุณ {user.first_name or user.email}")
            return redirect(next_url)
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form, "next": next_url})


def logout_view(request):
    """
    Member logout view.
    """
    logout(request)
    messages.info(request, "คุณได้ออกจากระบบเรียบร้อยแล้ว")
    return redirect("catalog:product_list")


@login_required
def profile_view(request):
    """
    Member profile and address management view (FR-24, FR-27, NFR-05).
    Strictly displays data belonging only to current authenticated user.
    """
    user = request.user
    addresses = Address.objects.filter(user=user)

    if request.method == "POST":
        profile_form = ProfileUpdateForm(request.POST, instance=user)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "อัปเดตข้อมูลส่วนตัวเรียบร้อยแล้ว")
            return redirect("accounts:profile")
    else:
        profile_form = ProfileUpdateForm(instance=user)

    context = {
        "user": user,
        "profile_form": profile_form,
        "addresses": addresses,
    }
    return render(request, "accounts/profile.html", context)


@login_required
def address_add_view(request):
    """
    Add a new shipping address for the logged-in member (FR-24).
    """
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            if address.is_default:
                Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
            # If it's the first address, make it default automatically
            elif not Address.objects.filter(user=request.user).exists():
                address.is_default = True
            address.save()
            messages.success(request, "เพิ่มที่อยู่จัดส่งใหม่สำเร็จ")
            return redirect("accounts:profile")
    else:
        # Pre-fill recipient name and phone from profile
        form = AddressForm(initial={
            "recipient_name": f"{request.user.first_name} {request.user.last_name}".strip(),
            "phone_number": request.user.phone_number,
        })

    return render(request, "accounts/address_form.html", {
        "form": form,
        "title": "เพิ่มที่อยู่จัดส่งใหม่",
        "action": "add",
    })


@login_required
def address_edit_view(request, address_id):
    """
    Edit an existing address. Strictly restricted to owner (FR-24, FR-27, NFR-05).
    """
    address = get_object_or_404(Address, id=address_id)
    if address.user != request.user:
        raise PermissionDenied("คุณไม่มีสิทธิ์แก้ไขที่อยู่นี้")

    if request.method == "POST":
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            addr = form.save(commit=False)
            if addr.is_default:
                Address.objects.filter(user=request.user, is_default=True).exclude(id=addr.id).update(is_default=False)
            addr.save()
            messages.success(request, "บันทึกการแก้ไขที่อยู่จัดส่งเรียบร้อยแล้ว")
            return redirect("accounts:profile")
    else:
        form = AddressForm(instance=address)

    return render(request, "accounts/address_form.html", {
        "form": form,
        "title": "แก้ไขที่อยู่จัดส่ง",
        "action": "edit",
        "address": address,
    })


@login_required
def address_delete_view(request, address_id):
    """
    Delete an address. Strictly restricted to owner (FR-27, NFR-05).
    """
    address = get_object_or_404(Address, id=address_id)
    if address.user != request.user:
        raise PermissionDenied("คุณไม่มีสิทธิ์ลบที่อยู่นี้")

    if request.method == "POST":
        was_default = address.is_default
        address.delete()
        # If deleted address was default, set another remaining address as default
        if was_default:
            next_addr = Address.objects.filter(user=request.user).first()
            if next_addr:
                next_addr.is_default = True
                next_addr.save()

        messages.success(request, "ลบที่อยู่จัดส่งเรียบร้อยแล้ว")
    return redirect("accounts:profile")


@login_required
def change_password_view(request):
    """
    Secure password changing view (FR-25).
    """
    if request.method == "POST":
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            new_password = form.cleaned_data["new_password"]
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "เปลี่ยนรหัสผ่านสำเร็จเรียบร้อยแล้ว")
            return redirect("accounts:profile")
    else:
        form = ChangePasswordForm(request.user)

    return render(request, "accounts/change_password.html", {"form": form})
