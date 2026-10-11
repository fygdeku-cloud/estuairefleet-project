from django.conf import settings
from django.urls import include, path
from rest_framework.routers import DefaultRouter, SimpleRouter

from estuairefleet.fleet.api.views import BusViewSet, CampusViewSet, TrajetViewSet
from estuairefleet.users.api.views import UserViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()
router.register("users", UserViewSet)
router.register("campuses", CampusViewSet)
router.register("trajets", TrajetViewSet)
router.register("buses", BusViewSet)
urlpatterns = [*router.urls, path("signals/", include("estuairefleet.signals.api.urls"))]
