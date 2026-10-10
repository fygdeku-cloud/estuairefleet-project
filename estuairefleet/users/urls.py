from django.urls import path

from .views import login_view, logout_view, user_detail_view, user_redirect_view, user_update_view

app_name = "users"
urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("~redirect/", user_redirect_view, name="redirect"),
    path("~update/", user_update_view, name="update"),
    path("<uuid:pk>/", user_detail_view, name="detail"),
]
