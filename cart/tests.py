from decimal import Decimal
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from catalog.models import Category, Brand, Product
from cart.models import Cart, CartItem
from cart.services import CartService

User = get_user_model()


class CartSystemTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="cartuser@badshop.com",
            password="Password123!",
            first_name="ผู้ใช้",
            last_name="ตะกร้า",
        )
        self.client.force_login(self.user)

        self.brand = Brand.objects.create(name="Yonex")
        self.category = Category.objects.create(name="ไม้สายบุก", slug="power")

        self.product1 = Product.objects.create(
            name="Astrox 100 ZZ",
            brand=self.brand,
            category=self.category,
            price=Decimal("6000.00"),
            original_price=Decimal("7000.00"),
            stock=10,
        )

        self.product2 = Product.objects.create(
            name="Arcsaber 11 Pro",
            brand=self.brand,
            category=self.category,
            price=Decimal("5000.00"),
            stock=2,  # Low stock
        )

    def test_fr28_and_fr31_add_to_cart_and_display(self):
        """FR-28, FR-31: Add product to cart, display title, price, quantity, and subtotal."""
        res_add = self.client.post(reverse("cart:cart_add"), {
            "product_id": self.product1.id,
            "quantity": 2,
        })
        self.assertEqual(res_add.status_code, 302)

        # Inspect cart page
        res_cart = self.client.get(reverse("cart:cart_detail"))
        self.assertEqual(res_cart.status_code, 200)
        self.assertContains(res_cart, "Astrox 100 ZZ")
        self.assertContains(res_cart, "6,000")
        self.assertContains(res_cart, "12,000")  # 6000 * 2

    def test_fr29_update_quantity_and_remove(self):
        """FR-29: Change quantity (+/-) and remove item from cart."""
        # 1. Add item
        CartService.add_to_cart(self.user, self.product1.id, quantity=1)
        cart = CartService.get_or_create_cart(self.user)
        item = cart.items.first()
        self.assertEqual(item.quantity, 1)

        # 2. Increase quantity via post
        self.client.post(reverse("cart:cart_update", kwargs={"item_id": item.id}), {"action": "increase"})
        item.refresh_from_db()
        self.assertEqual(item.quantity, 2)

        # 3. Decrease quantity via post
        self.client.post(reverse("cart:cart_update", kwargs={"item_id": item.id}), {"action": "decrease"})
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)

        # 4. Remove completely
        res_remove = self.client.post(reverse("cart:cart_remove", kwargs={"item_id": item.id}))
        self.assertEqual(res_remove.status_code, 302)
        self.assertEqual(cart.items.count(), 0)

    def test_fr30_and_nfr06_strict_decimal_calculation(self):
        """FR-30, NFR-06: Accurate server-side subtotal calculation using Decimal."""
        CartService.add_to_cart(self.user, self.product1.id, quantity=2)  # 6000 * 2 = 12000
        CartService.add_to_cart(self.user, self.product2.id, quantity=1)  # 5000 * 1 = 5000
        cart = CartService.get_or_create_cart(self.user)

        self.assertIsInstance(cart.subtotal, Decimal)
        self.assertEqual(cart.subtotal, Decimal("17000.00"))
        self.assertEqual(cart.total_items, 3)

    def test_fr32_cart_stock_validation(self):
        """FR-32: System checks stock before checkout; blocks checkout if stock insufficient."""
        # Product 2 has stock = 2. Try to add 3 or update to 3
        cart = CartService.get_or_create_cart(self.user)
        # Directly simulate cart item having quantity > product.stock (e.g. stock was bought by someone else)
        item = CartItem.objects.create(cart=cart, product=self.product2, quantity=5)

        is_valid, errors = CartService.validate_cart_stock(cart)
        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 1)

        # Attempt to proceed to checkout
        res_checkout = self.client.get(reverse("cart:validate_checkout"))
        self.assertEqual(res_checkout.status_code, 302)

        # Inspect cart page renders warning
        res_cart = self.client.get(reverse("cart:cart_detail"))
        self.assertContains(res_cart, "สต็อกไม่เพียงพอ")

    def test_fr33_cart_retention_expiry(self):
        """FR-33: Cart retains items up to configured expiry time (7 days)."""
        cart = CartService.get_or_create_cart(self.user)
        self.assertFalse(cart.is_expired)
        self.assertGreater(cart.expires_at, timezone.now())

        # If cart is expired in the past, get_or_create_cart renews it
        cart.expires_at = timezone.now() - timedelta(days=1)
        cart.save()
        self.assertTrue(cart.is_expired)

        renewed_cart = CartService.get_or_create_cart(self.user)
        self.assertFalse(renewed_cart.is_expired)
