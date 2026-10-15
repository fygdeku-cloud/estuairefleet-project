from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from estuairefleet.fleet.models import Bus, BusStatus, Campus, Direction, Stop, Trajet
from estuairefleet.signals.models import SignalStatus
from estuairefleet.signals.services import emit_signal
from estuairefleet.users.models import Administrateur, Chauffeur, Personnel, Student, User, UserRole

DEMO_PASSWORD = "EstuaireDemo2026!"


class Command(BaseCommand):
    help = "Crée un jeu de données de démonstration idempotent."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Le jeu de démonstration est réservé au mode DEBUG.")
        campuses = [
            self.campus("INSAM-CENTRE", "INSAM Centre", 3.8667, 11.5167),
            self.campus("INSAM-ODZA", "INSAM Odza", 3.8170, 11.5480),
        ]
        routes = []
        for index, campus in enumerate(campuses, start=1):
            for direction in (Direction.ALLER, Direction.RETOUR):
                code = f"R{index}-{direction[:2].upper()}"
                route, _ = Trajet.objects.update_or_create(
                    code=code,
                    defaults={
                        "name": f"{campus.name} · {direction.label}",
                        "direction": direction,
                        "itinerary": [[float(campus.latitude), float(campus.longitude)], [3.8800, 11.5200]],
                        "horaires": ["06:00", "07:00", "17:00", "18:00"],
                        "days_of_week": [0, 1, 2, 3, 4, 5, 6],
                        "service_start": "00:00",
                        "service_end": "23:59",
                        "is_active": True,
                    },
                )
                route.campuses.set([campus])
                Stop.objects.update_or_create(
                    trajet=route,
                    order=1,
                    defaults={"name": campus.name, "latitude": campus.latitude, "longitude": campus.longitude},
                )
                routes.append(route)
        admin = self.user("admin@insam.local", "ADMIN-001", UserRole.ADMIN, "Administrateur", "INSAM")
        Administrateur.objects.get_or_create(user=admin, defaults={"job_title": "Responsable transport"})
        staff = self.user("scolarite@insam.local", "STAFF-001", UserRole.STAFF, "Personnel", "Scolarité")
        Personnel.objects.get_or_create(user=staff, defaults={"service": "Scolarité", "campus": campuses[0]})
        drivers = []
        for index in range(3):
            driver = self.user(
                f"chauffeur{index + 1}@insam.local",
                f"DRV-{index + 1:03d}",
                UserRole.DRIVER,
                "Chauffeur",
                str(index + 1),
            )
            profile, _ = Chauffeur.objects.get_or_create(
                user=driver, defaults={"licence_number": f"LIC-{index + 1:03d}"}
            )
            drivers.append(profile)
        for index in range(25):
            student = self.user(
                f"etudiant{index + 1}@insam.local",
                f"INS-2026-{index + 1:03d}",
                UserRole.STUDENT,
                "Étudiant",
                str(index + 1),
            )
            profile, _ = Student.objects.get_or_create(
                user=student, defaults={"matricule": student.matricule, "campus": campuses[index % 2]}
            )
            profile.trajets_habituels.add(routes[index % len(routes)])
            if index < 5:
                profile.consent_location = True
                profile.location_consent_at = timezone.now()
                profile.save(update_fields=["consent_location", "location_consent_at", "updated_at"])
                if not profile.signals.filter(status=SignalStatus.ACTIF).exists():
                    point = routes[index % len(routes)].itinerary[0]
                    emit_signal(student=profile, trajet=routes[index % len(routes)], lat=point[0], lng=point[1])
        statuses = [BusStatus.EN_ROUTE, BusStatus.DISPONIBLE, BusStatus.INDISPONIBLE]
        for index, driver in enumerate(drivers):
            Bus.objects.update_or_create(
                plate_number=f"CE-{2026 + index}-EF",
                defaults={
                    "label": f"Bus {index + 1}",
                    "capacity": 30,
                    "status": statuses[index],
                    "chauffeur": driver,
                    "trajet": routes[index],
                },
            )
        self.stdout.write(self.style.SUCCESS(f"Jeu de démonstration créé. Mot de passe : {DEMO_PASSWORD}"))

    @staticmethod
    def campus(code, name, latitude, longitude):
        campus, _ = Campus.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "latitude": latitude,
                "longitude": longitude,
                "address": "Yaoundé · coordonnées de démonstration",
            },
        )
        return campus

    @staticmethod
    def user(email, matricule, role, first_name, last_name):
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "matricule": matricule,
                "role": role,
                "first_name": first_name,
                "last_name": last_name,
                "is_active": True,
                "must_change_password": False,
            },
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save(update_fields=["password", "updated_at"])
        return user
