from django.urls import path

from .views import (
    login_view,
    logout_view,
    password_change_view,
    password_reset_complete_view,
    password_reset_confirm_view,
    password_reset_done_view,
    password_reset_view,
    signup_view,
    otp_verify_view,
    user_detail_view,
    user_redirect_view,
    user_update_view,
)

app_name = "users"
urlpatterns = [
    path("login/", login_view, name="login"),
    path("signup/", signup_view, name="signup"),
    path("otp/", otp_verify_view, name="otp_verify"),
    path("logout/", logout_view, name="logout"),
    path("~redirect/", user_redirect_view, name="redirect"),
    path("~update/", user_update_view, name="update"),
    path("password/change/", password_change_view, name="password_change"),
    path("password/reset/", password_reset_view, name="password_reset"),
    path("password/reset/done/", password_reset_done_view, name="password_reset_done"),
    path("password/reset/<uidb64>/<token>/", password_reset_confirm_view, name="password_reset_confirm"),
    path("password/reset/complete/", password_reset_complete_view, name="password_reset_complete"),
    path("<uuid:pk>/", user_detail_view, name="detail"),
]
