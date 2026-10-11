from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import FormView

from estuairefleet.signals.forms import SignalForm
from estuairefleet.signals.services import emit_signal
from estuairefleet.users.permissions import StudentRequiredMixin


class SignalEmitView(StudentRequiredMixin, FormView):
    form_class = SignalForm
    template_name = "signals/emit.html"

    def form_valid(self, form):
        emit_signal(
            student=self.request.user,
            trajet=form.cleaned_data["trajet"],
            lat=form.cleaned_data["position_lat"],
            lng=form.cleaned_data["position_lng"],
        )
        messages.success(self.request, "Votre signal a été envoyé au trajet sélectionné.")
        return redirect("signals:emit")
