import re

import pytest
from django.core import mail
from django.core.exceptions import PermissionDenied
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIRequestFactory

from estuairefleet.users.backends import IdentifierBackend
from estuairefleet.users.models import Chauffeur, Student, UserRole
from estuairefleet.users.permissions import IsDriver, IsStudent, IsTransportAdmin
from estuairefleet.users.services import create_user_with_profile, update_student_profile, update_user_and_profile


def test_identifier_backend_authenticates_by_email_and_matricule(student):
    backend = IdentifierBackend()
    password = "UneBonnePhraseDePasse!2026"
    student.user.set_password(password)
    student.user.save(update_fields=["password", "updated_at"])

    assert backend.authenticate(None, username=student.user.email, password=password) == student.user
    assert backend.authenticate(None, username=student.user.matricule, password=password) == student.user
    assert backend.authenticate(None, username=student.user.matricule, password="incorrect") is None


@override_settings(ACCOUNT_ALLOW_REGISTRATION=True)
@pytest.mark.django_db
def test_login_by_matricule_requires_and_accepts_otp(client, student):
    response = client.post(
        reverse("users:login"),
        {"username": student.user.matricule, "password": "UneBonnePhraseDePasse!2026"},
    )

    assert response.status_code == 302
    assert response.url == reverse("users:otp_verify")
    assert "_auth_user_id" not in client.session
    code = re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)

    response = client.post(reverse("users:otp_verify"), {"code": code})

    assert response.status_code == 302
    assert str(client.session["_auth_user_id"]) == str(student.user.pk)
    assert client.session.get("otp_verified_at")


@pytest.mark.django_db
def test_role_helpers_and_profiles_are_consistent(student, driver, admin_user, staff_user):
    assert student.user.role == UserRole.STUDENT
    assert driver.user.role == UserRole.DRIVER
    assert Chauffeur.objects.get(pk=driver.pk) == driver
    assert admin_user.role == UserRole.ADMIN
    assert staff_user.role == UserRole.STAFF
    assert not student.user.is_transport_staff
    assert driver.user.is_transport_staff
    assert admin_user.is_transport_staff
    assert staff_user.is_transport_staff


@pytest.mark.django_db
def test_role_permissions_allow_only_expected_roles(student, driver, admin_user, staff_user):
    factory = APIRequestFactory()

    def allowed(permission, user):
        request = factory.get("/permissions")
        request.user = user
        return permission().has_permission(request, None)

    assert allowed(IsStudent, student.user)
    assert not allowed(IsStudent, driver.user)
    assert allowed(IsDriver, driver.user)
    assert not allowed(IsDriver, student.user)
    assert allowed(IsTransportAdmin, admin_user)
    assert allowed(IsTransportAdmin, staff_user) is False


@pytest.mark.django_db
def test_create_user_with_profile_creates_the_requested_role_profile(campus):
    user, temporary_password = create_user_with_profile(
        role=UserRole.STUDENT,
        email="new-student@example.test",
        matricule="INS-2026-100",
        first_name="Nouveau",
        last_name="Étudiant",
        campus=campus,
    )

    assert temporary_password
    assert user.role == UserRole.STUDENT
    assert Student.objects.get(user=user).matricule == "INS-2026-100"


@pytest.mark.django_db
def test_profile_update_requires_admin_and_updates_user_and_student(student, admin_user, second_campus, trajet):
    with pytest.raises(PermissionDenied):
        update_user_and_profile(user=student.user, by=student.user, first_name="Refusé")

    updated = update_user_and_profile(
        user=student.user,
        by=admin_user,
        first_name="Amina",
        last_name="Modifiée",
        profile={"campus": second_campus},
    )
    refreshed_student = update_student_profile(
        student=student,
        campus=second_campus,
        trajets_habituels=[trajet],
        consent_location=False,
    )

    updated.refresh_from_db()
    assert updated.get_full_name() == "Amina Modifiée"
    assert refreshed_student.campus == second_campus
    assert not refreshed_student.consent_location
    assert list(refreshed_student.trajets_habituels.all()) == [trajet]
