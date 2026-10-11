from django.views.generic import TemplateView

from estuairefleet.users.permissions import (
    AdminRequiredMixin,
    DriverRequiredMixin,
    StaffOrAdminRequiredMixin,
    StudentRequiredMixin,
)

from ..selectors import get_student_signal_history, get_visible_signals_for


class StudentSignalHomeView(StudentRequiredMixin, TemplateView):
    template_name = "signals/home.html"


class StudentSignalHistoryView(StudentRequiredMixin, TemplateView):
    template_name = "signals/history.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["signals"] = get_student_signal_history(self.request.user)
        return context


class DriverSignalMapView(DriverRequiredMixin, TemplateView):
    template_name = "signals/driver_map.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["signals"] = get_visible_signals_for(self.request.user)
        return context


class SignalMonitorView(StaffOrAdminRequiredMixin, TemplateView):
    template_name = "signals/monitor.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["signals"] = get_visible_signals_for(self.request.user)
        return context


class AbuseView(AdminRequiredMixin, TemplateView):
    template_name = "signals/abuse.html"
