from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from estuairefleet.intercampus.models import CoursInterCampus
from estuairefleet.intercampus.selectors import get_upcoming_courses
from estuairefleet.intercampus.services import create_course, delete_course, update_course
from estuairefleet.users.permissions import IsStaffOrAdmin

from .serializers import CoursInterCampusSerializer


class CoursInterCampusViewSet(viewsets.ModelViewSet):
    queryset = CoursInterCampus.objects.all()
    serializer_class = CoursInterCampusSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        if self.request.user.role in {"admin", "administrator", "staff"} or self.request.user.is_superuser:
            return CoursInterCampus.objects.all().select_related("campus_depart", "campus_arrivee", "bus_affecte")
        return get_upcoming_courses()

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsStaffOrAdmin()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.instance = create_course(**serializer.validated_data)

    def perform_update(self, serializer):
        serializer.instance = update_course(course=self.get_object(), **serializer.validated_data)

    def perform_destroy(self, instance):
        delete_course(course=instance)
