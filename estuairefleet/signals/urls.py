from django.urls import path

from .views.emit import SignalEmitView

app_name = "signals"
urlpatterns = [path("emit/", SignalEmitView.as_view(), name="emit")]
