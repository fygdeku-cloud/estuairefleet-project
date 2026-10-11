from django.urls import path

from .views.emit import SignalEmitView
from .views.pages import (
    AbuseView,
    DriverSignalMapView,
    SignalMonitorView,
    StudentSignalHistoryView,
    StudentSignalHomeView,
)

app_name = "signals"
urlpatterns = [
    path("", StudentSignalHomeView.as_view(), name="home"),
    path("emit/", SignalEmitView.as_view(), name="emit"),
    path("history/", StudentSignalHistoryView.as_view(), name="history"),
    path("driver/", DriverSignalMapView.as_view(), name="driver_map"),
    path("monitor/", SignalMonitorView.as_view(), name="monitor"),
    path("abuse/", AbuseView.as_view(), name="abuse"),
]
