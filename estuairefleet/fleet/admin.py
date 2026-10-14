from django.contrib import admin

from .models import Bus, Campus, Incident, Trajet

admin.site.register((Campus, Trajet, Bus, Incident))
