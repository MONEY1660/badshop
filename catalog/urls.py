from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.placeholder_view, name="product_list"),
]
