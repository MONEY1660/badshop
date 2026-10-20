from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from accounts.models import Address
from catalog.models import Category, Brand, Product
from orders.models import StockMovement, StockMovementType

User = get_user_model()


class Command(BaseCommand):
    help = "Seed initial data: Admin, 2 Members with addresses, Brands, Categories, and 24+ Badminton Rackets with stock status"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("--- กำลังเริ่มต้นสร้างข้อมูลจำลอง (Seed Data) ---"))

        # 1. Create Admin
        admin_email = "admin@badshop.com"
        admin_user, created = User.objects.get_or_create(
            email=admin_email,
            defaults={
                "first_name": "ผู้ดูแล",
                "last_name": "ระบบแบดช็อป",
                "phone_number": "0801112233",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )
        if created:
            admin_user.set_password("AdminPassword123!")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f"สร้างแอดมินสำเร็จ: {admin_email} (รหัสผ่าน: AdminPassword123!)"))
        else:
            self.stdout.write(f"พบแอดมินเดิม: {admin_email}")

        # 2. Create Members
        members_data = [
            {
                "email": "somchai@example.com",
                "password": "MemberPassword123!",
                "first_name": "สมชาย",
                "last_name": "รักแบดมินตัน",
                "phone_number": "0812345678",
                "address": {
                    "recipient_name": "สมชาย รักแบดมินตัน",
                    "phone_number": "0812345678",
                    "address_line": "123/45 ซอยสุขุมวิท 55 (ทองหล่อ)",
                    "subdistrict": "คลองตันเหนือ",
                    "district": "วัฒนา",
                    "province": "กรุงเทพมหานคร",
                    "postal_code": "10110",
                    "is_default": True,
                },
            },
            {
                "email": "suda@example.com",
                "password": "MemberPassword123!",
                "first_name": "สุดา",
                "last_name": "สายหยอด",
                "phone_number": "0898765432",
                "address": {
                    "recipient_name": "สุดา สายหยอด",
                    "phone_number": "0898765432",
                    "address_line": "88/19 หมู่บ้านกรีนวัลเลย์ ซอย 4",
                    "subdistrict": "ช้างเผือก",
                    "district": "เมืองเชียงใหม่",
                    "province": "เชียงใหม่",
                    "postal_code": "50300",
                    "is_default": True,
                },
            },
        ]

        for m_info in members_data:
            m_user, m_created = User.objects.get_or_create(
                email=m_info["email"],
                defaults={
                    "first_name": m_info["first_name"],
                    "last_name": m_info["last_name"],
                    "phone_number": m_info["phone_number"],
                    "is_active": True,
                },
            )
            if m_created:
                m_user.set_password(m_info["password"])
                m_user.save()
                self.stdout.write(self.style.SUCCESS(f"สร้างสมาชิกสำเร็จ: {m_user.email} (รหัสผ่าน: {m_info['password']})"))

            # Create default address
            addr_info = m_info["address"]
            addr, addr_created = Address.objects.get_or_create(
                user=m_user,
                address_line=addr_info["address_line"],
                defaults={
                    "recipient_name": addr_info["recipient_name"],
                    "phone_number": addr_info["phone_number"],
                    "subdistrict": addr_info["subdistrict"],
                    "district": addr_info["district"],
                    "province": addr_info["province"],
                    "postal_code": addr_info["postal_code"],
                    "is_default": addr_info["is_default"],
                },
            )

        # 3. Create Brands
        brands_dict = {
            "Yonex": "แบรนด์ไม้แบดมินตันชั้นนำระดับโลกจากประเทศญี่ปุ่น ได้รับความไว้วางใจจากนักกีฬาระดับแชมป์โลก",
            "Victor": "แบรนด์อุปกรณ์แบดมินตันมาตรฐานสากลจากไต้หวัน ผู้สนับสนุนหลักนักกีฬาระดับท็อปของโลก",
            "Li-Ning": "แบรนด์กีฬาและแบดมินตันยักษ์ใหญ่ ผู้นำนวัตกรรมคาร์บอนไฟเบอร์เกรดอากาศยาน",
            "Mizuno": "แบรนด์อุปกรณ์กีฬาพรีเมียมจากญี่ปุ่น โดดเด่นด้านความทนทานและการตอบสนองของก้านไม้",
            "Felet": "แบรนด์ยอดนิยมคุ้มค่าคุ้มราคา ขึ้นเอ็นได้สูง ทนทาน เหมาะกับผู้เล่นทุกระดับ",
        }
        created_brands = {}
        for b_name, b_desc in brands_dict.items():
            brand_obj, _ = Brand.objects.get_or_create(
                name=b_name,
                defaults={"description": b_desc, "is_active": True},
            )
            created_brands[b_name] = brand_obj

        # 4. Create Categories
        categories_dict = {
            "power": {
                "name": "ไม้สายพลังและตบหนัก (Head Heavy)",
                "desc": "ไม้หัวหนัก เหมาะสำหรับผู้เล่นสายบุก ตบหนัก เพิ่มแรงส่งลูกท้ายคอร์ทอย่างทรงพลัง",
            },
            "speed": {
                "name": "ไม้สายสปีดและเกมเร็ว (Head Light)",
                "desc": "ไม้หัวเบา คล่องตัวสูง ตอบสนองลูกดาดหน้าเน็ตและลูกตบสวนกลับได้อย่างรวดเร็ว",
            },
            "all-around": {
                "name": "ไม้สายควบคุมและรอบด้าน (Even Balance)",
                "desc": "ไม้บาลานซ์สมดุล ควบคุมทิศทางลูกได้แม่นยำ เล่นได้ดีทั้งเกมรุกและเกมรับ",
            },
            "beginner": {
                "name": "ไม้สำหรับผู้เล่นเริ่มต้นและฝึกซ้อม",
                "desc": "ไม้แบดมินตันน้ำหนักเบา ก้านสปริงดี ตีง่าย สบายข้อมือ เหมาะสำหรับผู้เริ่มต้น",
            },
        }
        created_categories = {}
        for c_slug, c_info in categories_dict.items():
            cat_obj, _ = Category.objects.get_or_create(
                slug=c_slug,
                defaults={"name": c_info["name"], "description": c_info["desc"], "is_active": True},
            )
            created_categories[c_slug] = cat_obj

        # 5. Create 24 Badminton Racket Products
        products_data = [
            # Yonex
            {
                "name": "Astrox 100 ZZ (Kurenai)",
                "brand": "Yonex",
                "category": "power",
                "price": Decimal("6490.00"),
                "original_price": Decimal("7290.00"),
                "stock": 12,
                "low_stock_threshold": 5,
                "is_new": True,
                "is_bestseller": True,
                "control_rating": 9,
                "power_rating": 10,
                "speed_rating": 7,
                "shaft_flexibility": "แข็งพิเศษ (Extra Stiff)",
                "weight_grip": "4U G5 (ประมาณ 83g)",
                "balance_point": "หัวหนักมาก (Head Heavy 305mm)",
                "description": "ไม้แบดมินตันรุ่นเรือธงยอดนิยม ก้านแข็งพิเศษ Hyper Slim Shaft ถ่ายทอดพลังตบได้อย่างต่อเนื่องและแม่นยำสูงสุด",
            },
            {
                "name": "Astrox 99 Pro (White Tiger)",
                "brand": "Yonex",
                "category": "power",
                "price": Decimal("6190.00"),
                "original_price": Decimal("6990.00"),
                "stock": 4,  # LOW STOCK
                "low_stock_threshold": 5,
                "is_new": False,
                "is_bestseller": True,
                "control_rating": 8,
                "power_rating": 10,
                "speed_rating": 6,
                "shaft_flexibility": "แข็ง (Stiff)",
                "weight_grip": "4U G5 (ประมาณ 83g)",
                "balance_point": "หัวหนัก (Head Heavy 303mm)",
                "description": "พลังทำลายล้างเหนือระดับด้วยเทคโนโลยี Power-Assist Bumper หนักแน่นทุกจังหวะ smash",
            },
            {
                "name": "Nanoflare 1000 Z",
                "brand": "Yonex",
                "category": "speed",
                "price": Decimal("6290.00"),
                "original_price": Decimal("6990.00"),
                "stock": 15,
                "low_stock_threshold": 5,
                "is_new": True,
                "is_bestseller": True,
                "control_rating": 8,
                "power_rating": 8,
                "speed_rating": 10,
                "shaft_flexibility": "แข็งพิเศษ (Extra Stiff)",
                "weight_grip": "4U G5 (ประมาณ 83g)",
                "balance_point": "หัวเบา (Head Light)",
                "description": "ไม้สายสปีดที่ทำสถิติความเร็ว smash โลก ด้วยเฟรม AERO Frame ขั้นสูง เร็วฟ้าผ่า",
            },
            {
                "name": "Nanoflare 800 Pro",
                "brand": "Yonex",
                "category": "speed",
                "price": Decimal("5890.00"),
                "original_price": None,
                "stock": 8,
                "low_stock_threshold": 5,
                "is_new": True,
                "is_bestseller": False,
                "control_rating": 9,
                "power_rating": 7,
                "speed_rating": 10,
                "shaft_flexibility": "แข็ง (Stiff)",
                "weight_grip": "4U G5 (ประมาณ 83g)",
                "balance_point": "หัวเบา (Head Light)",
                "description": "เน้นเกมไดรฟ์และเกมดาดรวดเร็ว ด้ามจับกระชับ เฟรมเพรียวบางลดแรงต้านอากาศ",
            },
            {
                "name": "Arcsaber 11 Pro",
                "brand": "Yonex",
                "category": "all-around",
                "price": Decimal("5990.00"),
                "original_price": Decimal("6700.00"),
                "stock": 10,
                "low_stock_threshold": 5,
                "is_new": False,
                "is_bestseller": True,
                "control_rating": 10,
                "power_rating": 8,
                "speed_rating": 8,
                "shaft_flexibility": "แข็ง (Stiff)",
                "weight_grip": "4U G5 (ประมาณ 83g)",
                "balance_point": "สมดุล (Even Balance 295mm)",
                "description": "ไม้สายคอนโทรลระดับตำนาน กักลูกนานขึ้นเพื่อการวางลูกที่คมกริบและแม่นยำระดับเซนติเมตร",
            },
            {
                "name": "Arcsaber 7 Pro",
                "brand": "Yonex",
                "category": "all-around",
                "price": Decimal("4890.00"),
                "original_price": None,
                "stock": 0,  # OUT OF STOCK (FR-05)
                "low_stock_threshold": 5,
                "is_new": False,
                "is_bestseller": False,
                "control_rating": 9,
                "power_rating": 7,
                "speed_rating": 8,
                "shaft_flexibility": "ปานกลาง (Medium)",
                "weight_grip": "4U G5 (ประมาณ 83g)",
                "balance_point": "สมดุล (Even Balance)",
                "description": "ก้านปานกลาง ตีง่าย คุมเกมง่าย สบายแขน เหมาะกับผู้เล่นที่ต้องการความแม่นยำสูง (สินค้าหมดชั่วคราว)",
            },
            {
                "name": "Astrox 88D Pro (Gen 3)",
                "brand": "Yonex",
                "category": "power",
                "price": Decimal("6390.00"),
                "original_price": None,
                "stock": 14,
                "low_stock_threshold": 5,
                "is_new": True,
                "is_bestseller": False,
                "control_rating": 8,
                "power_rating": 9,
                "speed_rating": 8,
                "shaft_flexibility": "แข็ง (Stiff)",
                "weight_grip": "4U G5 (ประมาณ 83g)",
                "balance_point": "หัวหนัก (Head Heavy)",
                "description": "รุ่นพัฒนาสำหรับผู้เล่นคู่หลัง เน้นเจาะทำแต้มจากแดนหลังด้วยแรงกดสูงสุด",
            },
            {
                "name": "Astrox 88S Pro (Gen 3)",
                "brand": "Yonex",
                "category": "speed",
                "price": Decimal("6390.00"),
                "original_price": None,
                "stock": 11,
                "low_stock_threshold": 5,
                "is_new": True,
                "is_bestseller": False,
                "control_rating": 9,
                "power_rating": 8,
                "speed_rating": 9,
                "shaft_flexibility": "แข็ง (Stiff)",
                "weight_grip": "4U G5 (ประมาณ 83g)",
                "balance_point": "สมดุลค่อนไปทางหัวหนัก",
                "description": "รุ่นพัฒนาสำหรับผู้เล่นคู่หน้า เพิ่มความเร็วการตะปบและการดักตัดลูกหน้าเน็ต",
            },

            # Victor
            {
                "name": "Thruster Ryuga II Pro",
                "brand": "Victor",
                "category": "power",
                "price": Decimal("5690.00"),
                "original_price": Decimal("6400.00"),
                "stock": 7,
                "low_stock_threshold": 5,
                "is_new": True,
                "is_bestseller": True,
                "control_rating": 8,
                "power_rating": 10,
                "speed_rating": 7,
                "shaft_flexibility": "แข็ง (Stiff)",
                "weight_grip": "4U G5",
                "balance_point": "หัวหนักมาก (Head Heavy 305mm)",
                "description": "ไม้ประจำตัว Lee Zii Jia พลังบุกดุดัน ก้านสปริงตัวคืนรูปไวด้วยเทคโนโลยี WES 2.0",
            },
            {
                "name": "Auraspeed 100X",
                "brand": "Victor",
                "category": "speed",
                "price": Decimal("5450.00"),
                "original_price": None,
                "stock": 6,
                "low_stock_threshold": 5,
                "is_new": False,
                "is_bestseller": True,
                "control_rating": 8,
                "power_rating": 8,
                "speed_rating": 10,
                "shaft_flexibility": "แข็ง (Stiff)",
                "weight_grip": "4U G5",
                "balance_point": "สมดุลค่อนหัวเบา",
                "description": "ไม้สายสปีดที่ขึ้นชื่อเรื่องความเสถียร สวิงไม้ต่อเนื่องไม่มีสะดุด",
            },
            {
                "name": "DriveX 10 Metallic",
                "brand": "Victor",
                "category": "all-around",
                "price": Decimal("5200.00"),
                "original_price": None,
                "stock": 9,
                "low_stock_threshold": 5,
                "is_new": True,
                "is_bestseller": False,
                "control_rating": 9,
                "power_rating": 8,
                "speed_rating": 8,
                "shaft_flexibility": "แข็ง (Stiff)",
                "weight_grip": "4U G5",
                "balance_point": "สมดุล (Even Balance)",
                "description": "ผสมผสานเส้นใย Metallic Carbon ช่วยเพิ่มความแน่นและแรงสปริงในทุกจังหวะการตี",
            },
            {
                "name": "Thruster F Enhanced",
                "brand": "Victor",
                "category": "power",
                "price": Decimal("4990.00"),
                "original_price": Decimal("5800.00"),
                "stock": 3,  # LOW STOCK
                "low_stock_threshold": 5,
                "is_new": False,
                "is_bestseller": False,
                "control_rating": 9,
                "power_rating": 9,
                "speed_rating": 7,
                "shaft_flexibility": "แข็งปานกลาง",
                "weight_grip": "4U G5",
                "balance_point": "หัวหนัก",
                "description": "ไม้บุกยอดนิยมของ Tai Tzu Ying คอนโทรลง่าย ตบลูกวิถีปักคม",
            },
            {
                "name": "Brave Sword 12 SE",
                "brand": "Victor",
                "category": "speed",
                "price": Decimal("3990.00"),
                "original_price": Decimal("4500.00"),
                "stock": 0,  # OUT OF STOCK
                "low_stock_threshold": 5,
                "is_new": False,
                "is_bestseller": True,
                "control_rating": 8,
                "power_rating": 7,
                "speed_rating": 9,
                "shaft_flexibility": "ปานกลาง (Medium)",
                "weight_grip": "3U G5 / 4U G5",
                "balance_point": "สมดุล",
                "description": "เฟรมตัดอากาศทรงดาบในตำนาน สวิงไว ตีลูกรับและลูกสวนกลับง่าย (สินค้าหมดชั่วคราว)",
            },

            # Li-Ning
            {
                "name": "Axforce 100 (Kirin)",
                "brand": "Li-Ning",
                "category": "power",
                "price": Decimal("6990.00"),
                "original_price": Decimal("7990.00"),
                "stock": 8,
                "low_stock_threshold": 5,
                "is_new": True,
                "is_bestseller": True,
                "control_rating": 8,
                "power_rating": 10,
                "speed_rating": 7,
                "shaft_flexibility": "แข็ง (Stiff 6.0mm)",
                "weight_grip": "4U G5",
                "balance_point": "หัวหนักมาก (308mm)",
                "description": "ลวดลายกิเลนทอง ก้าน 6.0mm บางพิเศษ ส่งถ่ายแรงตบกระแทกเต็มพิกัด",
            },
            {
                "name": "Halbertec 9000",
                "brand": "Li-Ning",
                "category": "all-around",
                "price": Decimal("6590.00"),
                "original_price": None,
                "stock": 10,
                "low_stock_threshold": 5,
                "is_new": True,
                "is_bestseller": True,
                "control_rating": 10,
                "power_rating": 8,
                "speed_rating": 8,
                "shaft_flexibility": "แข็งปานกลาง",
                "weight_grip": "4U G5",
                "balance_point": "สมดุล (Even Balance)",
                "description": "ไม้ควบคุมระดับไฮเอนด์ของ Yuta Watanabe ออกแบบมาเพื่อการคุมเกมที่แม่นยำอย่างแท้จริง",
            },
            {
                "name": "Tectonic 9",
                "brand": "Li-Ning",
                "category": "power",
                "price": Decimal("5890.00"),
                "original_price": Decimal("6500.00"),
                "stock": 4,  # LOW STOCK
                "low_stock_threshold": 5,
                "is_new": False,
                "is_bestseller": False,
                "control_rating": 8,
                "power_rating": 9,
                "speed_rating": 8,
                "shaft_flexibility": "แข็ง (Stiff)",
                "weight_grip": "4U G5",
                "balance_point": "หัวหนัก",
                "description": "เทคโนโลยี Tectonic กักเก็บพลังงานที่เฟรม 5 และ 7 นาฬิกา สปริงลูกพุ่งแรง",
            },
            {
                "name": "Bladex 900 Moon Max",
                "brand": "Li-Ning",
                "category": "speed",
                "price": Decimal("6290.00"),
                "original_price": None,
                "stock": 7,
                "low_stock_threshold": 5,
                "is_new": True,
                "is_bestseller": False,
                "control_rating": 9,
                "power_rating": 7,
                "speed_rating": 10,
                "shaft_flexibility": "แข็ง (Stiff)",
                "weight_grip": "4U G5",
                "balance_point": "หัวเบา",
                "description": "เฟรมทรง AERO ลดแรงต้าน สำหรับผู้เล่นที่เน้นเกมเร็ว แย่งชิงจังหวะบุก",
            },
            {
                "name": "Windstorm 72",
                "brand": "Li-Ning",
                "category": "beginner",
                "price": Decimal("3290.00"),
                "original_price": Decimal("3990.00"),
                "stock": 18,
                "low_stock_threshold": 5,
                "is_new": False,
                "is_bestseller": True,
                "control_rating": 8,
                "power_rating": 6,
                "speed_rating": 10,
                "shaft_flexibility": "อ่อน (Flexible)",
                "weight_grip": "6U (72 กรัม)",
                "balance_point": "หัวหนักชดเชยน้ำหนักเบา",
                "description": "น้ำหนักเบาเพียง 72 กรัม ตีง่าย สบายแขน ไม่ล้า เหมาะสำหรับผู้หญิงและผู้เริ่มต้น",
            },
            {
                "name": "Aeronaut 9000C",
                "brand": "Li-Ning",
                "category": "power",
                "price": Decimal("5190.00"),
                "original_price": None,
                "stock": 0,  # OUT OF STOCK
                "low_stock_threshold": 5,
                "is_new": False,
                "is_bestseller": False,
                "control_rating": 8,
                "power_rating": 9,
                "speed_rating": 8,
                "shaft_flexibility": "แข็ง (Stiff)",
                "weight_grip": "3U G5",
                "balance_point": "หัวหนัก",
                "description": "ร่องลมคู่บนเฟรมช่วยให้สวิงเร็วขึ้น แม้เป็นไม้หัวหนัก 3U (สินค้าหมดชั่วคราว)",
            },

            # Mizuno
            {
                "name": "Fortius 11 Quick",
                "brand": "Mizuno",
                "category": "speed",
                "price": Decimal("5900.00"),
                "original_price": Decimal("6600.00"),
                "stock": 5,  # LOW STOCK
                "low_stock_threshold": 5,
                "is_new": False,
                "is_bestseller": False,
                "control_rating": 8,
                "power_rating": 8,
                "speed_rating": 10,
                "shaft_flexibility": "แข็ง (Stiff)",
                "weight_grip": "4U G5",
                "balance_point": "หัวเบา",
                "description": "นวัตกรรม Torayca M40X เพิ่มความยืดหยุ่นและตอบสนองจังหวะตีได้รวดเร็วทันใจ",
            },
            {
                "name": "Fortius 11 Power",
                "brand": "Mizuno",
                "category": "power",
                "price": Decimal("5900.00"),
                "original_price": None,
                "stock": 7,
                "low_stock_threshold": 5,
                "is_new": False,
                "is_bestseller": False,
                "control_rating": 8,
                "power_rating": 10,
                "speed_rating": 7,
                "shaft_flexibility": "แข็ง (Stiff)",
                "weight_grip": "4U G5",
                "balance_point": "หัวหนัก",
                "description": "โครงสร้างเฟรมเน้นการส่งกำลังตบลูกท้ายคอร์ทอย่างหนักหน่วง",
            },
            {
                "name": "Altius 01 Feel",
                "brand": "Mizuno",
                "category": "all-around",
                "price": Decimal("5200.00"),
                "original_price": None,
                "stock": 9,
                "low_stock_threshold": 5,
                "is_new": False,
                "is_bestseller": False,
                "control_rating": 10,
                "power_rating": 7,
                "speed_rating": 8,
                "shaft_flexibility": "ปานกลาง (Medium)",
                "weight_grip": "4U G5",
                "balance_point": "สมดุล",
                "description": "สัมผัสลูกนุ่มมือ ควบคุมทิศทางและหยอดได้อย่างละเอียดอ่อน",
            },

            # Felet
            {
                "name": "Woven TJ 1000",
                "brand": "Felet",
                "category": "power",
                "price": Decimal("2890.00"),
                "original_price": Decimal("3590.00"),
                "stock": 20,
                "low_stock_threshold": 5,
                "is_new": False,
                "is_bestseller": True,
                "control_rating": 8,
                "power_rating": 9,
                "speed_rating": 8,
                "shaft_flexibility": "แข็งปานกลาง",
                "weight_grip": "4U G5",
                "balance_point": "หัวหนัก (300mm)",
                "description": "ขึ้นเอ็นได้สูงสุดถึง 35 ปอนด์ โครงสร้าง Woven Carbon ทนทาน คุ้มค่าที่สุดในรุ่น",
            },
            {
                "name": "Aero Carbon 80",
                "brand": "Felet",
                "category": "beginner",
                "price": Decimal("1890.00"),
                "original_price": Decimal("2290.00"),
                "stock": 25,
                "low_stock_threshold": 5,
                "is_new": False,
                "is_bestseller": False,
                "control_rating": 8,
                "power_rating": 7,
                "speed_rating": 8,
                "shaft_flexibility": "ปานกลางค่อนอ่อน (Flexible)",
                "weight_grip": "4U G5",
                "balance_point": "สมดุล",
                "description": "ไม้เริ่มต้นราคาสบายกระเป๋า น้ำหนักกำลังดี ก้านสปริงตัวง่าย ไม่เปลืองแรง",
            },
        ]

        created_count = 0
        for p_info in products_data:
            brand_obj = created_brands[p_info["brand"]]
            cat_obj = created_categories[p_info["category"]]

            product, created = Product.objects.get_or_create(
                name=p_info["name"],
                brand=brand_obj,
                defaults={
                    "category": cat_obj,
                    "price": p_info["price"],
                    "original_price": p_info.get("original_price"),
                    "stock": p_info["stock"],
                    "low_stock_threshold": p_info["low_stock_threshold"],
                    "is_new": p_info["is_new"],
                    "is_bestseller": p_info["is_bestseller"],
                    "is_active": True,
                    "control_rating": p_info["control_rating"],
                    "power_rating": p_info["power_rating"],
                    "speed_rating": p_info["speed_rating"],
                    "shaft_flexibility": p_info["shaft_flexibility"],
                    "weight_grip": p_info["weight_grip"],
                    "balance_point": p_info["balance_point"],
                    "description": p_info["description"],
                },
            )
            if created:
                created_count += 1
                # If stock > 0, log initial stock movement
                if product.stock > 0:
                    StockMovement.objects.create(
                        product=product,
                        movement_type=StockMovementType.MANUAL_IN,
                        quantity=product.stock,
                        remaining_stock=product.stock,
                        created_by=admin_user,
                        note="ยกยอดสต็อกตั้งต้นจาก seed_data",
                    )

        self.stdout.write(self.style.SUCCESS(f"สร้างไม้แบดมินตันทั้งหมดเรียบร้อย: {created_count} รุ่นใหม่ (ทั้งหมด {Product.objects.count()} รุ่น)"))
        self.stdout.write(self.style.SUCCESS("--- สิ้นสุดการ Seed Data สำเร็จสมบูรณ์ 100% ---"))
