from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import Address
from catalog.models import Category, Brand, Product
from cart.models import Cart, CartItem
from orders.models import Order, OrderStatus, PaymentStatus, StockMovement, StockMovementType
from orders.services import OrderService

User = get_user_model()


class Phase1ModelAndServiceTestCase(TestCase):
    def setUp(self):
        # Create User
        self.user = User.objects.create_user(
            email="testuser@badshop.com",
            password="StrongPassword123!",
            first_name="ทดสอบ",
            last_name="ระบบ",
        )
        self.address = Address.objects.create(
            user=self.user,
            recipient_name="คุณทดสอบ ระบบ",
            phone_number="0819998877",
            address_line="99/1 อาคารแบดมินตัน",
            subdistrict="คลองเตย",
            district="คลองเตย",
            province="กรุงเทพมหานคร",
            postal_code="10110",
            is_default=True,
        )

        # Create Category and Brand
        self.brand = Brand.objects.create(name="Yonex")
        self.category = Category.objects.create(name="ไม้สายบุก", slug="power")

        # Create Product with initial stock = 10
        self.product = Product.objects.create(
            name="Astrox Test 99",
            brand=self.brand,
            category=self.category,
            price=Decimal("5000.00"),
            original_price=Decimal("6000.00"),
            stock=10,
            low_stock_threshold=3,
            control_rating=8,
            power_rating=9,
            speed_rating=7,
        )

    def test_custom_user_model(self):
        """Test User uses email as username and Argon2/PBKDF2 hashing."""
        self.assertEqual(self.user.email, "testuser@badshop.com")
        self.assertTrue(self.user.check_password("StrongPassword123!"))
        self.assertTrue(self.user.password.startswith("argon2") or self.user.password.startswith("pbkdf2"))

    def test_product_properties(self):
        """Test product helper properties and Thai formatting."""
        self.assertTrue(self.product.is_in_stock)
        self.assertFalse(self.product.is_low_stock)
        self.assertTrue(self.product.is_sale)
        self.assertEqual(self.product.discount_percent, 17)

    def test_order_creation_stock_deduction_and_idempotency(self):
        """Test atomic order creation from cart, inventory deduction, and idempotency."""
        # Setup cart with 2 items
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)

        idempotency_token = "unique-test-token-123456"
        order = OrderService.create_order_from_cart(
            user=self.user,
            address=self.address,
            idempotency_token=idempotency_token,
        )

        # 1. Check order details
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.subtotal, Decimal("10000.00"))
        # Since subtotal >= 1500, free shipping
        self.assertEqual(order.shipping_fee, Decimal("0.00"))
        self.assertEqual(order.total_amount, Decimal("10000.00"))

        # 2. Check stock was deducted atomically (10 - 2 = 8)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)

        # 3. Check StockMovement log was created
        movement = StockMovement.objects.filter(order=order).first()
        self.assertIsNotNone(movement)
        self.assertEqual(movement.movement_type, StockMovementType.DEDUCT_ORDER)
        self.assertEqual(movement.quantity, -2)
        self.assertEqual(movement.remaining_stock, 8)

        # 4. Check Idempotency: calling again with same token returns same order without double deduction
        duplicate_call_order = OrderService.create_order_from_cart(
            user=self.user,
            address=self.address,
            idempotency_token=idempotency_token,
        )
        self.assertEqual(duplicate_call_order.id, order.id)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)  # Still 8, not deducted twice!

    def test_order_cancellation_restores_stock(self):
        """Test cancelling order restores stock and creates StockMovement log."""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=3)

        order = OrderService.create_order_from_cart(
            user=self.user,
            address=self.address,
            idempotency_token="cancel-test-token-789",
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 7)

        # Cancel order
        OrderService.cancel_order(order, user=self.user, reason="เปลี่ยนใจ")
        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.CANCELLED)

        # Stock should be restored back to 10
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)

        # Check restore stock movement
        restore_movement = StockMovement.objects.filter(
            order=order,
            movement_type=StockMovementType.RESTORE_CANCEL,
        ).first()
        self.assertIsNotNone(restore_movement)
        self.assertEqual(restore_movement.quantity, 3)
        self.assertEqual(restore_movement.remaining_stock, 10)
