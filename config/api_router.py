from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from estuairefleet.fleet.api.views import BusViewSet, CampusViewSet, TrajetViewSet
from estuairefleet.signals.api.views import SignalViewSet
from estuairefleet.users.api.views import UserViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()
router.register("users", UserViewSet)
router.register("campuses", CampusViewSet)
router.register("routes", TrajetViewSet)
router.register("buses", BusViewSet)
router.register("signals", SignalViewSet)
app_name = "api"
urlpatterns = router.urls
