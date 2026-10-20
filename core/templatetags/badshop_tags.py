from decimal import Decimal
from django import template

register = template.Library()


@register.filter(name="th_currency")
def th_currency(value):
    """
    Format numeric value as Thai Baht currency (e.g., ฿2,590.00 or ฿2,590)
    """
    if value is None or value == "":
        return "฿0"
    try:
        val = Decimal(str(value))
        if val % 1 == 0:
            return f"฿{int(val):,}"
        return f"฿{val:,.2f}"
    except Exception:
        return f"฿{value}"


@register.filter(name="order_status_badge")
def order_status_badge(status):
    """
    Return Tailwind CSS color classes for order status badges.
    """
    badge_map = {
        "PENDING_PAYMENT": "bg-amber-100 text-amber-800 border-amber-300",
        "AWAITING_VERIFICATION": "bg-blue-100 text-blue-800 border-blue-300",
        "PREPARING": "bg-indigo-100 text-indigo-800 border-indigo-300",
        "SHIPPED": "bg-emerald-100 text-emerald-800 border-emerald-300",
        "CANCELLED": "bg-rose-100 text-rose-800 border-rose-300",
    }
    return badge_map.get(status, "bg-slate-100 text-slate-800 border-slate-300")
