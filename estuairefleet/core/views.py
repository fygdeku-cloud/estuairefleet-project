from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView

from estuairefleet.users.permissions import AdminRequiredMixin


class HomeRedirectView(TemplateView):
    template_name = "pages/home.html"

    def get_redirect_url(self):
        destinations = {
            "student": "signals:home",
            "driver": "signals:driver_map",
            "admin": "core:dashboard",
            "administrator": "core:dashboard",
            "staff": "signals:monitor",
        }
        if self.request.user.is_superuser:
            return reverse("core:dashboard")
        return reverse(destinations.get(self.request.user.role, "signals:home"))

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.get_redirect_url())
        return super().dispatch(request, *args, **kwargs)


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = "core/dashboard.html"
