from django.urls import path

from .views import AdminDashboardView, HomeRedirectView

app_name = "core"
urlpatterns = [
    path("", HomeRedirectView.as_view(), name="home"),
    path("dashboard/", AdminDashboardView.as_view(), name="dashboard"),
]
