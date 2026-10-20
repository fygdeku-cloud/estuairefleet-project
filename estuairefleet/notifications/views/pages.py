from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView

from estuairefleet.users.permissions import OTPRequiredMixin

from ..selectors import get_notifications_for_user, get_unread_notification_count
from ..services import mark_notification_read


class NotificationListView(OTPRequiredMixin, ListView):
    template_name = "notifications/list.html"
    context_object_name = "notifications"

    def get_queryset(self):
        return get_notifications_for_user(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["unread_count"] = get_unread_notification_count(self.request.user)
        return context


class NotificationReadView(OTPRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        notification = get_object_or_404(get_notifications_for_user(request.user), pk=kwargs["pk"])
        mark_notification_read(notification=notification, user=request.user)
        return redirect("notifications:list")
