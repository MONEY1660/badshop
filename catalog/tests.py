from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from catalog.models import Category, Brand, Product
from catalog.services import CatalogService


class CatalogStorefrontTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Create Categories
        self.cat_power = Category.objects.create(name="ไม้สายบุก", slug="power")
        self.cat_speed = Category.objects.create(name="ไม้สายสปีด", slug="speed")

        # Create Brands
        self.brand_yonex = Brand.objects.create(name="Yonex", slug="yonex")
        self.brand_victor = Brand.objects.create(name="Victor", slug="victor")

        # Create Products
        self.p1 = Product.objects.create(
            name="Astrox 100 ZZ",
            brand=self.brand_yonex,
            category=self.cat_power,
            price=Decimal("6490.00"),
            original_price=Decimal("7290.00"),
            stock=12,
            is_new=True,
            is_bestseller=True,
            control_rating=9,
            power_rating=10,
            speed_rating=7,
            shaft_flexibility="แข็งพิเศษ",
            weight_grip="4U G5",
            balance_point="หัวหนักมาก",
        )

        self.p2 = Product.objects.create(
            name="Nanoflare 1000 Z",
            brand=self.brand_yonex,
            category=self.cat_speed,
            price=Decimal("6290.00"),
            original_price=Decimal("6990.00"),
            stock=5,
            is_new=True,
            is_bestseller=False,
            control_rating=8,
            power_rating=8,
            speed_rating=10,
            shaft_flexibility="แข็งพิเศษ",
            weight_grip="4U G5",
            balance_point="หัวเบา",
        )

        self.p3 = Product.objects.create(
            name="Thruster Ryuga II",
            brand=self.brand_victor,
            category=self.cat_power,
            price=Decimal("5690.00"),
            original_price=None,
            stock=0,  # Out of stock
            is_new=False,
            is_bestseller=True,
            control_rating=8,
            power_rating=10,
            speed_rating=7,
            shaft_flexibility="แข็ง",
            weight_grip="4U G5",
            balance_point="หัวหนัก",
        )

    def test_fr01_product_listing_page(self):
        """FR-01: Product list page loads and renders product cards."""
        response = self.client.get(reverse("catalog:product_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Astrox 100 ZZ")
        self.assertContains(response, "Nanoflare 1000 Z")
        self.assertContains(response, "Thruster Ryuga II")

    def test_fr02_and_fr03_badges_and_prices(self):
        """FR-02, FR-03: Displays price, original price, discount %, and badges."""
        response = self.client.get(reverse("catalog:product_list"))
        self.assertContains(response, "6,490")
        self.assertContains(response, "7,290")
        self.assertContains(response, "สินค้าใหม่")
        self.assertContains(response, "ขายดี")
        self.assertContains(response, "-11%")  # 7290 -> 6490 discount is 11%

    def test_fr05_stock_status_display(self):
        """FR-05: Displays in-stock vs out-of-stock badges."""
        response = self.client.get(reverse("catalog:product_list"))
        self.assertContains(response, "พร้อมส่ง")
        self.assertContains(response, "สินค้าหมด")

    def test_fr07_search_by_name_and_brand(self):
        """FR-07: Search by model name or brand name."""
        # Search by model name
        res_name = self.client.get(reverse("catalog:product_list") + "?q=Nanoflare")
        self.assertContains(res_name, "Nanoflare 1000 Z")
        self.assertNotContains(res_name, "Thruster Ryuga II")

        # Search by brand
        res_brand = self.client.get(reverse("catalog:product_list") + "?q=Victor")
        self.assertContains(res_brand, "Thruster Ryuga II")
        self.assertNotContains(res_brand, "Astrox 100 ZZ")

    def test_fr08_price_filter(self):
        """FR-08: Filter by min and max price."""
        # Range 5,000 to 6,000 -> only p3 (5,690)
        res = self.client.get(reverse("catalog:product_list") + "?min_price=5000&max_price=6000")
        self.assertContains(res, "Thruster Ryuga II")
        self.assertNotContains(res, "Astrox 100 ZZ")
        self.assertNotContains(res, "Nanoflare 1000 Z")

    def test_fr09_brand_filter(self):
        """FR-09: Filter by brand."""
        res = self.client.get(reverse("catalog:product_list") + "?brand=victor")
        self.assertContains(res, "Thruster Ryuga II")
        self.assertNotContains(res, "Astrox 100 ZZ")

    def test_fr10_stock_filter(self):
        """FR-10: Filter by in_stock and out_of_stock."""
        # In stock only
        res_in = self.client.get(reverse("catalog:product_list") + "?stock=in_stock")
        self.assertContains(res_in, "Astrox 100 ZZ")
        self.assertNotContains(res_in, "Thruster Ryuga II")

        # Out of stock only
        res_out = self.client.get(reverse("catalog:product_list") + "?stock=out_of_stock")
        self.assertContains(res_out, "Thruster Ryuga II")
        self.assertNotContains(res_out, "Astrox 100 ZZ")

    def test_fr11_ratings_filter(self):
        """FR-11: Filter by badminton attributes (Control, Power, Speed)."""
        # Speed >= 10 -> only p2 (Nanoflare 1000 Z)
        res_speed = self.client.get(reverse("catalog:product_list") + "?min_speed=10")
        self.assertContains(res_speed, "Nanoflare 1000 Z")
        self.assertNotContains(res_speed, "Astrox 100 ZZ")

    def test_fr12_sorting(self):
        """FR-12: Sort by price ascending and descending."""
        # Price ascending (5690, 6290, 6490)
        res_asc = self.client.get(reverse("catalog:product_list") + "?sort=price_asc")
        products = list(res_asc.context["products"])
        self.assertEqual(products[0], self.p3)
        self.assertEqual(products[-1], self.p1)

        # Price descending (6490, 6290, 5690)
        res_desc = self.client.get(reverse("catalog:product_list") + "?sort=price_desc")
        products_desc = list(res_desc.context["products"])
        self.assertEqual(products_desc[0], self.p1)
        self.assertEqual(products_desc[-1], self.p3)

    def test_fr13_results_counter_and_fr15_empty_state(self):
        """FR-13: Count of results, FR-15: Empty state message."""
        # Results count
        res = self.client.get(reverse("catalog:product_list"))
        self.assertEqual(res.context["total_count"], 3)

        # No match query -> FR-15 message
        res_none = self.client.get(reverse("catalog:product_list") + "?q=NonExistentModelXYZ")
        self.assertEqual(res_none.context["total_count"], 0)
        self.assertContains(res_none, "ไม่พบไม้แบดมินตันที่ตรงกับเงื่อนไข")

    def test_fr16_to_fr21_product_detail_page(self):
        """FR-16 to FR-21: Product detail, specs, stock status, and related products."""
        res_detail = self.client.get(reverse("catalog:product_detail", kwargs={"slug": self.p1.slug}))
        self.assertEqual(res_detail.status_code, 200)

        # FR-16: Model name, brand, price, specs
        self.assertContains(res_detail, "Astrox 100 ZZ")
        self.assertContains(res_detail, "Yonex")
        self.assertContains(res_detail, "6,490")
        self.assertContains(res_detail, "แข็งพิเศษ")
        self.assertContains(res_detail, "4U G5")

        # FR-18: Stock count
        self.assertContains(res_detail, "คงเหลือในสต็อก 12 ชิ้น")

        # FR-19: Quantity input
        self.assertContains(res_detail, 'name="quantity"')

        # FR-21: Related products (p2 Nanoflare is from Yonex)
        self.assertContains(res_detail, "ไม้แบดมินตันที่คุณอาจสนใจ")
        self.assertContains(res_detail, "Nanoflare 1000 Z")

    def test_fr20_out_of_stock_warning_on_detail(self):
        """FR-20: Out of stock warning banner on product detail for out of stock items."""
        res_out = self.client.get(reverse("catalog:product_detail", kwargs={"slug": self.p3.slug}))
        self.assertEqual(res_out.status_code, 200)
        self.assertContains(res_out, "สินค้าหมดชั่วคราว")
        self.assertContains(res_out, "disabled")
