from django.urls import path

from .views import (
    CancelSignalView,
    CloseSignalView,
    FlagFalseSignalView,
    MineSignalsView,
    RenewSignalView,
    SignalCollectionView,
    VisibleSignalsView,
)

urlpatterns = [
    path("", SignalCollectionView.as_view(), name="collection"),
    path("mine/", MineSignalsView.as_view(), name="mine"),
    path("visible/", VisibleSignalsView.as_view(), name="visible"),
    path("<uuid:pk>/cancel/", CancelSignalView.as_view(), name="cancel"),
    path("<uuid:pk>/renew/", RenewSignalView.as_view(), name="renew"),
    path("<uuid:pk>/close/", CloseSignalView.as_view(), name="close"),
    path("<uuid:pk>/flag-false/", FlagFalseSignalView.as_view(), name="flag_false"),
]
