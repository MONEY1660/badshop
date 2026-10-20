from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.placeholder_view, name="index"),
]
