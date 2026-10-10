from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.views.generic import DetailView, RedirectView, UpdateView

from estuairefleet.users.models import User


class IdentifierLoginView(LoginView):
    template_name = "account/login.html"


class UserDetailView(DetailView):
    model = User
    template_name = "users/user_detail.html"


class UserUpdateView(SuccessMessageMixin, UpdateView):
    model = User
    fields = ("first_name", "last_name", "phone")
    template_name = "users/user_form.html"
    success_message = "Votre profil a été mis à jour."

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return self.request.user.get_absolute_url()


class UserRedirectView(RedirectView):
    permanent = False

    def get_redirect_url(self):
        return reverse("users:detail", kwargs={"pk": self.request.user.pk})


login_view = IdentifierLoginView.as_view()
logout_view = LogoutView.as_view()
user_detail_view = UserDetailView.as_view()
user_update_view = UserUpdateView.as_view()
user_redirect_view = UserRedirectView.as_view()
