from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, ListView

from estuairefleet.users.permissions import OTPRequiredMixin, StaffOrAdminRequiredMixin

from ..forms import CoursInterCampusForm
from ..models import CoursInterCampus
from ..selectors import get_manageable_courses, get_upcoming_courses
from ..services import create_course, transition_course


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


class CourseTransitionView(StaffOrAdminRequiredMixin, ListView):
    def post(self, request, *args, **kwargs):
        course = get_object_or_404(CoursInterCampus, pk=kwargs["pk"])
        transition_course(course=course, target=kwargs["target"])
        messages.success(request, "Le statut du cours a été mis à jour.")
        return redirect("intercampus:manage")
