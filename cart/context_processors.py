def cart_summary(request):
    """
    Context processor to make cart total item count available globally to navbar.
    """
    if request.user.is_authenticated:
        try:
            cart = getattr(request.user, "cart", None)
            if cart and not cart.is_expired:
                return {
                    "cart_total_items": cart.total_items,
                    "cart_subtotal": cart.subtotal,
                }
        except Exception:
            pass
    return {
        "cart_total_items": 0,
        "cart_subtotal": 0,
    }
