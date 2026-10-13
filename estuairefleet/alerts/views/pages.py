from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, FormView, ListView

from estuairefleet.users.permissions import AdminRequiredMixin, DriverRequiredMixin, NonStudentRequiredMixin

from ..forms import AlertResponseForm
from ..models import Alert
from ..selectors import get_alerts_for_driver, get_open_alerts
from ..services import resolve_alert, respond_to_alert


class AlertListView(NonStudentRequiredMixin, ListView):
    template_name = "alerts/list.html"
    context_object_name = "alerts"

    def get_queryset(self):
        if self.request.user.role == "driver":
            return get_alerts_for_driver(self.request.user)
        return get_open_alerts()


class DriverAlertListView(DriverRequiredMixin, ListView):
    template_name = "alerts/list.html"
    context_object_name = "alerts"

    def get_queryset(self):
        return get_alerts_for_driver(self.request.user)


class AlertDetailView(NonStudentRequiredMixin, DetailView):
    template_name = "alerts/detail.html"
    context_object_name = "alert"
    model = Alert

    def get_object(self, queryset=None):
        if self.request.user.role == "driver":
            return get_object_or_404(get_alerts_for_driver(self.request.user), pk=self.kwargs["pk"])
        return get_object_or_404(get_open_alerts(), pk=self.kwargs["pk"])


class AlertResponseView(DriverRequiredMixin, FormView):
    template_name = "alerts/respond.html"
    form_class = AlertResponseForm

    def dispatch(self, request, *args, **kwargs):
        self.alert = get_object_or_404(get_alerts_for_driver(request.user), pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["alert"] = self.alert
        return context

    def form_valid(self, form):
        try:
            respond_to_alert(alert=self.alert, driver=self.request.user, **form.cleaned_data)
        except PermissionDenied as exc:
            form.add_error(None, str(exc))
            return self.form_invalid(form)
        messages.success(self.request, "Votre réponse a été enregistrée.")
        return redirect("alerts:detail", pk=self.alert.pk)


class AlertResolveView(AdminRequiredMixin, FormView):
    def post(self, request, *args, **kwargs):
        alert = get_object_or_404(get_open_alerts(), pk=kwargs["pk"])
        resolve_alert(alert=alert, by=request.user)
        messages.success(request, "L'alerte a été clôturée.")
        return redirect("alerts:list")
