from django.core.management.base import BaseCommand, CommandError

from estuairefleet.fleet.models import Bus
from estuairefleet.fleet.services import update_bus_position
from estuairefleet.users.models import User


class Command(BaseCommand):
    help = "Déplace un bus au premier point de son itinéraire."

    def add_arguments(self, parser):
        parser.add_argument("--bus", required=True)

    def handle(self, *args, **options):
        bus = Bus.objects.select_related("trajet").filter(plate_number=options["bus"]).first()
        admin = User.objects.filter(role="admin", is_superuser=True).first()
        if not bus or not bus.trajet or not bus.trajet.itinerary or not admin:
            raise CommandError("Bus, trajet ou administrateur de démonstration introuvable.")
        point = bus.trajet.itinerary[0]
        update_bus_position(bus=bus, lat=point[0], lng=point[1], by=admin)
        self.stdout.write(self.style.SUCCESS("Position du bus mise à jour."))
