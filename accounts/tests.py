from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import Address

User = get_user_model()


class AccountsAuthAndProfileTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_a = User.objects.create_user(
            email="usera@badshop.com",
            password="Password123!",
            first_name="สมชาย",
            last_name="ใจดี",
            phone_number="0811112222",
        )
        self.address_a = Address.objects.create(
            user=self.user_a,
            recipient_name="สมชาย ใจดี",
            phone_number="0811112222",
            address_line="10/1 ซอยอารีย์",
            subdistrict="พญาไท",
            district="พญาไท",
            province="กรุงเทพมหานคร",
            postal_code="10400",
            is_default=True,
        )

        self.user_b = User.objects.create_user(
            email="userb@badshop.com",
            password="Password123!",
            first_name="สมหญิง",
            last_name="รักเรียน",
            phone_number="0899998888",
        )
        self.address_b = Address.objects.create(
            user=self.user_b,
            recipient_name="สมหญิง รักเรียน",
            phone_number="0899998888",
            address_line="20/2 ถนนนิมมาน",
            subdistrict="สุเทพ",
            district="เมืองเชียงใหม่",
            province="เชียงใหม่",
            postal_code="50200",
            is_default=True,
        )

    def test_fr22_member_registration(self):
        """FR-22: Member can register with personal info and initial shipping address."""
        reg_data = {
            "first_name": "วิชัย",
            "last_name": "มั่นคง",
            "email": "wichai@badshop.com",
            "phone_number": "0855554444",
            "password": "WichaiPassword123!",
            "confirm_password": "WichaiPassword123!",
            "address_line": "999 หมู่บ้านสิริ",
            "subdistrict": "บางเขน",
            "district": "เมืองนนทบุรี",
            "province": "นนทบุรี",
            "postal_code": "11000",
        }
        res = self.client.post(reverse("accounts:register"), reg_data)
        self.assertEqual(res.status_code, 302)  # Redirected on success

        new_user = User.objects.filter(email="wichai@badshop.com").first()
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.first_name, "วิชัย")

        # Verify address was created
        addr = Address.objects.filter(user=new_user).first()
        self.assertIsNotNone(addr)
        self.assertEqual(addr.province, "นนทบุรี")
        self.assertTrue(addr.is_default)

    def test_fr23_duplicate_email_rejected(self):
        """FR-23: Duplicate email registration is strictly rejected."""
        dup_data = {
            "first_name": "สมชาย",
            "last_name": "ซ้ำ",
            "email": "usera@badshop.com",  # Already exists
            "phone_number": "0812345678",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "address_line": "123 ซอยสุขุมวิท",
            "subdistrict": "คลองตัน",
            "district": "คลองเตย",
            "province": "กรุงเทพมหานคร",
            "postal_code": "10110",
        }
        res = self.client.post(reverse("accounts:register"), dup_data)
        self.assertEqual(res.status_code, 200)  # Re-renders form with error
        self.assertContains(res, "อีเมลนี้ถูกใช้งานแล้วในระบบ")

    def test_fr24_profile_and_address_update(self):
        """FR-24: Member can edit their profile and manage multiple shipping addresses."""
        self.client.force_login(self.user_a)

        # 1. Update profile name
        res_prof = self.client.post(reverse("accounts:profile"), {
            "first_name": "สมชาย (แก้ไข)",
            "last_name": "ใจดีมาก",
            "phone_number": "0811119999",
        })
        self.assertEqual(res_prof.status_code, 302)
        self.user_a.refresh_from_db()
        self.assertEqual(self.user_a.first_name, "สมชาย (แก้ไข)")

        # 2. Add second address
        res_addr = self.client.post(reverse("accounts:address_add"), {
            "recipient_name": "สมชาย ใจดี ที่ทำงาน",
            "phone_number": "029998888",
            "address_line": "อาคารทาวเวอร์ 1 ชั้น 20",
            "subdistrict": "สีลม",
            "district": "บางรัก",
            "province": "กรุงเทพมหานคร",
            "postal_code": "10500",
            "is_default": False,
        })
        self.assertEqual(res_addr.status_code, 302)
        self.assertEqual(Address.objects.filter(user=self.user_a).count(), 2)

    def test_fr25_password_change(self):
        """FR-25: Member can change their password securely."""
        self.client.force_login(self.user_a)
        res = self.client.post(reverse("accounts:change_password"), {
            "old_password": "Password123!",
            "new_password": "NewSecurePassword456!",
            "confirm_new_password": "NewSecurePassword456!",
        })
        self.assertEqual(res.status_code, 302)
        self.user_a.refresh_from_db()
        self.assertTrue(self.user_a.check_password("NewSecurePassword456!"))

    def test_fr26_login_required(self):
        """FR-26: Anonymous user is forced to login when accessing member areas."""
        res = self.client.get(reverse("accounts:profile"))
        self.assertEqual(res.status_code, 302)
        self.assertIn("/accounts/login/", res.url)

    def test_fr27_and_nfr05_privacy_isolation(self):
        """FR-27, NFR-05: User A cannot edit or delete User B's address."""
        self.client.force_login(self.user_a)

        # User A tries to edit User B's address
        res_edit = self.client.post(reverse("accounts:address_edit", kwargs={"address_id": self.address_b.id}), {
            "recipient_name": "แอบแก้ไข",
            "phone_number": "0899998888",
            "address_line": "20/2 ถนนนิมมาน",
            "subdistrict": "สุเทพ",
            "district": "เมืองเชียงใหม่",
            "province": "เชียงใหม่",
            "postal_code": "50200",
        })
        # Should be forbidden (403 PermissionDenied)
        self.assertEqual(res_edit.status_code, 403)

        # User A tries to delete User B's address
        res_del = self.client.post(reverse("accounts:address_delete", kwargs={"address_id": self.address_b.id}))
        self.assertEqual(res_del.status_code, 403)

        # Verify User B's address remains intact
        self.assertTrue(Address.objects.filter(id=self.address_b.id).exists())
