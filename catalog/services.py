from decimal import Decimal
from django.db.models import Q
from .models import Product, Brand, Category


class CatalogService:
    """
    Business logic for product browsing, filtering, searching, and sorting.
    """

    @staticmethod
    def get_filtered_products(
        query=None,
        brand_slugs=None,
        category_slugs=None,
        min_price=None,
        max_price=None,
        stock_status=None,  # 'in_stock', 'out_of_stock', or 'all'
        min_control=None,
        min_power=None,
        min_speed=None,
        sort_by=None,       # 'price_asc', 'price_desc', 'newest', 'popular'
        include_inactive=False,
    ):
        qs = Product.objects.select_related("brand", "category")
        if not include_inactive:
            qs = qs.filter(is_active=True)

        # 1. Search Query (Name or Brand name - FR-07)
        if query:
            q_clean = query.strip()
            qs = qs.filter(
                Q(name__icontains=q_clean) |
                Q(brand__name__icontains=q_clean) |
                Q(description__icontains=q_clean)
            )

        # 2. Brand Filter (FR-09)
        if brand_slugs:
            if isinstance(brand_slugs, str):
                brand_slugs = [brand_slugs]
            qs = qs.filter(brand__slug__in=brand_slugs)

        # 3. Category Filter (FR-04)
        if category_slugs:
            if isinstance(category_slugs, str):
                category_slugs = [category_slugs]
            qs = qs.filter(category__slug__in=category_slugs)

        # 4. Price Range Filter (FR-08)
        if min_price:
            try:
                qs = qs.filter(price__gte=Decimal(str(min_price)))
            except Exception:
                pass
        if max_price:
            try:
                qs = qs.filter(price__lte=Decimal(str(max_price)))
            except Exception:
                pass

        # 5. Stock Status Filter (FR-10)
        if stock_status == "in_stock":
            qs = qs.filter(stock__gt=0)
        elif stock_status == "out_of_stock":
            qs = qs.filter(stock__lte=0)

        # 6. Badminton Specs Filter (FR-11)
        if min_control:
            try:
                qs = qs.filter(control_rating__gte=int(min_control))
            except Exception:
                pass
        if min_power:
            try:
                qs = qs.filter(power_rating__gte=int(min_power))
            except Exception:
                pass
        if min_speed:
            try:
                qs = qs.filter(speed_rating__gte=int(min_speed))
            except Exception:
                pass

        # 7. Sorting (FR-12)
        if sort_by == "price_asc":
            qs = qs.order_by("price", "-created_at")
        elif sort_by == "price_desc":
            qs = qs.order_by("-price", "-created_at")
        elif sort_by == "popular":
            qs = qs.order_by("-is_bestseller", "-stock", "-created_at")
        elif sort_by == "newest":
            qs = qs.order_by("-is_new", "-created_at")
        else:
            # Default sorting: Newest and bestsellers first
            qs = qs.order_by("-is_new", "-is_bestseller", "-created_at")

        return qs

    @staticmethod
    def get_related_products(product, limit=4):
        """
        Get related products by brand or category, excluding current product (FR-21).
        """
        return (
            Product.objects.filter(is_active=True)
            .filter(Q(brand=product.brand) | Q(category=product.category))
            .exclude(id=product.id)
            .select_related("brand", "category")[:limit]
        )
