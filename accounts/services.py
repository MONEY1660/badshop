from django.db import transaction
from django.contrib.auth import authenticate
from .models import User, Address


class AccountService:
    """
    Business logic for user account management and address handling.
    """

    @staticmethod
    def register_user(email, password, first_name, last_name, phone_number=""):
        email = email.strip().lower()
        if User.objects.filter(email=email).exists():
            raise ValueError("อีเมลนี้ถูกใช้งานแล้วในระบบ")
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            phone_number=phone_number.strip(),
        )
        return user

    @staticmethod
    @transaction.atomic
    def save_address(user, recipient_name, phone_number, address_line, subdistrict, district, province, postal_code, is_default=False, address_id=None):
        if is_default:
            Address.objects.filter(user=user, is_default=True).update(is_default=False)

        if address_id:
            address = Address.objects.get(id=address_id, user=user)
            address.recipient_name = recipient_name
            address.phone_number = phone_number
            address.address_line = address_line
            address.subdistrict = subdistrict
            address.district = district
            address.province = province
            address.postal_code = postal_code
            address.is_default = is_default
            address.save()
        else:
            # If it's the first address, make it default automatically
            if not Address.objects.filter(user=user).exists():
                is_default = True
            address = Address.objects.create(
                user=user,
                recipient_name=recipient_name,
                phone_number=phone_number,
                address_line=address_line,
                subdistrict=subdistrict,
                district=district,
                province=province,
                postal_code=postal_code,
                is_default=is_default,
            )
        return address
