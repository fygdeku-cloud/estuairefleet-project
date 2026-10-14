from django.contrib import admin

from .models import Alert, AlertRelayAttempt, AlertResponse, AlertThresholdSchedule

admin.site.register((Alert, AlertResponse, AlertThresholdSchedule, AlertRelayAttempt))
