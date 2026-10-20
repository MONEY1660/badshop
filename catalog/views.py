from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Product, Brand, Category
from .services import CatalogService


def product_list(request):
    """
    Product listing view supporting multi-faceted filtering, searching,
    sorting, and pagination (FR-01 to FR-15).
    """
    # 1. Extract query params
    query = request.GET.get("q", "").strip()
    selected_brands = request.GET.getlist("brand")
    selected_categories = request.GET.getlist("category")
    min_price = request.GET.get("min_price", "")
    max_price = request.GET.get("max_price", "")
    stock_status = request.GET.get("stock", "all")
    min_control = request.GET.get("min_control", "")
    min_power = request.GET.get("min_power", "")
    min_speed = request.GET.get("min_speed", "")
    sort_by = request.GET.get("sort", "default")
    page_number = request.GET.get("page", 1)

    # 2. Query filtered products from CatalogService (NFR-08)
    products_qs = CatalogService.get_filtered_products(
        query=query,
        brand_slugs=selected_brands,
        category_slugs=selected_categories,
        min_price=min_price,
        max_price=max_price,
        stock_status=stock_status,
        min_control=min_control,
        min_power=min_power,
        min_speed=min_speed,
        sort_by=sort_by,
    )

    total_count = products_qs.count()

    # 3. Pagination (12 items per page)
    paginator = Paginator(products_qs, 12)
    try:
        products = paginator.page(page_number)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    # 4. Context data for filter controls
    all_brands = Brand.objects.filter(is_active=True).order_by("name")
    all_categories = Category.objects.filter(is_active=True).order_by("name")

    # Check if any filter is active
    has_active_filters = bool(
        query or selected_brands or selected_categories or min_price or max_price
        or (stock_status and stock_status != "all") or min_control or min_power or min_speed
        or (sort_by and sort_by != "default")
    )

    context = {
        "products": products,
        "total_count": total_count,
        "all_brands": all_brands,
        "all_categories": all_categories,
        "query": query,
        "selected_brands": selected_brands,
        "selected_categories": selected_categories,
        "min_price": min_price,
        "max_price": max_price,
        "stock_status": stock_status,
        "min_control": min_control,
        "min_power": min_power,
        "min_speed": min_speed,
        "sort_by": sort_by,
        "has_active_filters": has_active_filters,
    }

    # If request is HTMX, return just the product grid partial
    if request.headers.get("HX-Request") == "true" and not request.GET.get("full_page"):
        return render(request, "catalog/partials/product_grid.html", context)

    return render(request, "catalog/product_list.html", context)


def product_detail(request, slug):
    """
    Detailed product showcase view (FR-16 to FR-21).
    Displays specs, stock status, ratings, and related products.
    """
    product = get_object_or_404(
        Product.objects.select_related("brand", "category"),
        slug=slug,
        is_active=True,
    )

    related_products = CatalogService.get_related_products(product, limit=4)

    context = {
        "product": product,
        "related_products": related_products,
    }
    return render(request, "catalog/product_detail.html", context)
