from django.urls import path

from .views.main import FleetOverviewView, MyBusView, NetworkView

app_name = "fleet"
urlpatterns = [
    path("overview/", FleetOverviewView.as_view(), name="overview"),
    path("my-bus/", MyBusView.as_view(), name="my_bus"),
    path("network/", NetworkView.as_view(), name="network"),
]
