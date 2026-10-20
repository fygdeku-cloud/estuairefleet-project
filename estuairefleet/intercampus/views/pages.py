from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from estuairefleet.fleet.models import Bus
from estuairefleet.users.permissions import OTPRequiredMixin, StaffOrAdminRequiredMixin

from ..forms import CoursInterCampusForm
from ..models import CoursInterCampus, IntercampusCourseStatus
from ..selectors import get_manageable_courses, get_upcoming_courses
from ..services import (
    assign_bus,
    auto_assign_bus,
    create_course,
    mark_driver_notified,
    transition_course,
    update_course,
)


class CourseListView(OTPRequiredMixin, ListView):
    template_name = "intercampus/list.html"
    context_object_name = "courses"

    def get_queryset(self):
        return get_upcoming_courses()


class CourseManageListView(StaffOrAdminRequiredMixin, ListView):
    template_name = "intercampus/manage.html"
    context_object_name = "courses"

    def get_queryset(self):
        return get_manageable_courses()


class CourseCreateView(StaffOrAdminRequiredMixin, CreateView):
    template_name = "intercampus/form.html"
    form_class = CoursInterCampusForm

    def form_valid(self, form):
        self.object = create_course(**form.cleaned_data)
        messages.success(self.request, "Le cours inter-campus a été planifié.")
        return redirect("intercampus:manage")


class CourseUpdateView(StaffOrAdminRequiredMixin, UpdateView):
    template_name = "intercampus/form.html"
    form_class = CoursInterCampusForm
    model = CoursInterCampus

    def form_valid(self, form):
        self.object = update_course(course=self.get_object(), **form.cleaned_data)
        messages.success(self.request, "Le cours inter-campus a été mis à jour.")
        return redirect("intercampus:manage")


class CourseTransitionView(StaffOrAdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        course = get_object_or_404(CoursInterCampus, pk=kwargs["pk"])
        transition_course(course=course, target=kwargs["target"])
        messages.success(request, "Le statut du cours a été mis à jour.")
        return redirect("intercampus:manage")


class CourseAssignBusView(StaffOrAdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        course = get_object_or_404(CoursInterCampus, pk=kwargs["pk"])
        if request.POST.get("bus_id") == "auto":
            auto_assign_bus(course=course)
            messages.success(request, "Le bus compatible le plus disponible a été affecté.")
        else:
            bus = get_object_or_404(Bus, pk=request.POST.get("bus_id"))
            assign_bus(course=course, bus=bus)
            messages.success(request, "Le bus a été affecté au cours inter-campus.")
        return redirect("intercampus:manage")


class CourseNotifyDriverView(StaffOrAdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        course = get_object_or_404(CoursInterCampus, pk=kwargs["pk"])
        mark_driver_notified(course=course)
        messages.success(request, "Le chauffeur a été prévenu du cours inter-campus.")
        return redirect("intercampus:manage")


class CourseCancelView(StaffOrAdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        course = get_object_or_404(CoursInterCampus, pk=kwargs["pk"])
        transition_course(course=course, target=IntercampusCourseStatus.CANCELLED)
        messages.success(request, "Le cours inter-campus a été annulé.")
        return redirect("intercampus:manage")
