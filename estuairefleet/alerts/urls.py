from django.urls import path

from .views import AlertDetailView, AlertListView, AlertResolveView, AlertResponseView, DriverAlertListView

app_name = "alerts"
urlpatterns = [
    path("", AlertListView.as_view(), name="list"),
    path("driver/", DriverAlertListView.as_view(), name="driver_list"),
    path("<uuid:pk>/", AlertDetailView.as_view(), name="detail"),
    path("<uuid:pk>/respond/", AlertResponseView.as_view(), name="respond"),
    path("<uuid:pk>/resolve/", AlertResolveView.as_view(), name="resolve"),
]
