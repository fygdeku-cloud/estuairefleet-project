from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import RedirectView, TemplateView


class HomeRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        destinations = {
            "student": "signals:home",
            "driver": "signals:driver_map",
            "admin": "core:dashboard",
            "administrator": "core:dashboard",
            "staff": "signals:monitor",
        }
        return reverse(destinations.get(self.request.user.role, "signals:home"))


class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "core/dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in {"admin", "administrator"} and not request.user.is_superuser:
            from django.core.exceptions import PermissionDenied

            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
