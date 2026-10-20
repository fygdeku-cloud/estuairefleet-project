from django.urls import path

from .views import AdminDashboardView, DashboardLiveView, HomeRedirectView, OperationalExportView

app_name = "core"
urlpatterns = [
    path("", HomeRedirectView.as_view(), name="home"),
    path("dashboard/", AdminDashboardView.as_view(), name="dashboard"),
    path("dashboard/live/", DashboardLiveView.as_view(), name="dashboard_live"),
    path("dashboard/export/<str:export_type>/", OperationalExportView.as_view(), name="dashboard_export"),
]
