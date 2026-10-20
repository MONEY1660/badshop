from django.urls import path
from . import views

app_name = "cart"

urlpatterns = [
    path("", views.placeholder_view, name="cart_detail"),
]
