from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView

from estuairefleet.users.permissions import AdminRequiredMixin

from .selectors import get_operational_statistics
from .services import export_csv, export_pdf, export_xlsx


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statistics"] = get_operational_statistics()
        return context


class OperationalExportView(AdminRequiredMixin, TemplateView):
    export_type = "csv"

    def get(self, request, *args, **kwargs):
        statistics = get_operational_statistics()
        exporters = {
            "csv": (export_csv, "text/csv", "statistiques.csv"),
            "xlsx": (
                export_xlsx,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "statistiques.xlsx",
            ),
            "pdf": (export_pdf, "application/pdf", "statistiques.pdf"),
        }
        try:
            exporter, content_type, filename = exporters[kwargs["export_type"]]
        except KeyError as exc:
            raise Http404 from exc
        response = HttpResponse(exporter(statistics), content_type=content_type)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
