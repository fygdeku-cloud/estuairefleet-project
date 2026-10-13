from rest_framework.routers import DefaultRouter

from .views import CoursInterCampusViewSet

router = DefaultRouter()
router.register("", CoursInterCampusViewSet, basename="intercampus-course")
urlpatterns = router.urls
