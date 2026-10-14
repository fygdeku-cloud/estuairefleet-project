import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


class MessageProvider:
    def send(self, *, recipient, title, message):
        raise NotImplementedError


class EmailProvider(MessageProvider):
    def send(self, *, recipient, title, message):
        send_mail(title, message, settings.DEFAULT_FROM_EMAIL, [recipient.email], fail_silently=False)
        return "email"


class ConsoleSmsProvider(MessageProvider):
    def send(self, *, recipient, title, message):
        logger.info("Notification SMS pour %s: %s — %s", recipient.phone_number, title, message)
        return "console"


def provider_for(channel):
    return {"email": EmailProvider(), "sms": ConsoleSmsProvider()}.get(channel)
