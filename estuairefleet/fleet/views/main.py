from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from estuairefleet.users.permissions import AdminRequiredMixin, DriverRequiredMixin

from ..selectors import get_bus_for_chauffeur, get_buses_for_map, get_fleet_overview_counts, get_trajets_in_service


class FleetOverviewView(AdminRequiredMixin, TemplateView):
    template_name = "fleet/overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"buses": get_buses_for_map(self.request.user), "counts": get_fleet_overview_counts()})
        return context


class MyBusView(DriverRequiredMixin, TemplateView):
    template_name = "fleet/my_bus_live.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["bus"] = get_bus_for_chauffeur(self.request.user)
        return context


class NetworkView(LoginRequiredMixin, TemplateView):
    template_name = "fleet/network_live.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["trajets"] = get_trajets_in_service()
        return context
