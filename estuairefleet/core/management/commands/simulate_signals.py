from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from estuairefleet.fleet.models import Trajet
from estuairefleet.signals.services import emit_signal
from estuairefleet.users.models import Student


class Command(BaseCommand):
    help = "Crée des signaux plausibles pour une démonstration."

    def add_arguments(self, parser):
        parser.add_argument("--trajet", required=True)
        parser.add_argument("--count", type=int, default=5)

    def handle(self, *args, **options):
        trajet = Trajet.objects.filter(code=options["trajet"]).first()
        if not trajet:
            raise CommandError("Trajet introuvable.")
        created = 0
        for student in Student.objects.filter(user__is_active=True)[: options["count"]]:
            if not student.has_location_consent:
                student.location_consent_at = timezone.now()
                student.consent_location = True
                student.save(update_fields=["location_consent_at", "consent_location", "updated_at"])
            try:
                emit_signal(
                    student=student,
                    lat=float(trajet.itinerary[0][0]),
                    lng=float(trajet.itinerary[0][1]),
                    trajet=trajet,
                )
                created += 1
            except Exception as exc:
                self.stderr.write(str(exc))
        self.stdout.write(self.style.SUCCESS(f"{created} signal(aux) créé(s)."))
