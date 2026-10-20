from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/change-password/", views.change_password_view, name="change_password"),
    path("address/add/", views.address_add_view, name="address_add"),
    path("address/<int:address_id>/edit/", views.address_edit_view, name="address_edit"),
    path("address/<int:address_id>/delete/", views.address_delete_view, name="address_delete"),
    # Default index redirects to login or profile
    path("", views.login_view, name="index"),
]
