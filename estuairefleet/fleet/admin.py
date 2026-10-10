from django.contrib import admin

from .models import Bus, Campus, Trajet

admin.site.register((Campus, Trajet, Bus))
