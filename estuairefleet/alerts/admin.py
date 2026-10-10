from django.contrib import admin

from .models import Alert, AlertResponse

admin.site.register((Alert, AlertResponse))
