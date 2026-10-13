import re

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from estuairefleet.users.models import Chauffeur, Student, User, UserRole


@override_settings(ACCOUNT_ALLOW_REGISTRATION=True)
class StudentSignupTests(TestCase):
    def payload(self):
        return {
            "email": "student@example.test",
            "matricule": "ins-2026-999",
            "first_name": "Amina",
            "last_name": "Ndiaye",
            "password1": "UneBonnePhraseDePasse!2026",
            "password2": "UneBonnePhraseDePasse!2026",
        }

    def test_signup_creates_student_profile_and_logs_user_in(self):
        response = self.client.post(reverse("users:signup"), self.payload())

        self.assertRedirects(response, reverse("users:otp_verify"), fetch_redirect_response=False)
        code = re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)
        response = self.client.post(reverse("users:otp_verify"), {"code": code})
        self.assertRedirects(response, reverse("core:home"), fetch_redirect_response=False)
        user = User.objects.get(email="student@example.test")
        self.assertEqual(user.role, UserRole.STUDENT)
        self.assertFalse(user.must_change_password)
        self.assertEqual(Student.objects.get(user=user).matricule, "INS-2026-999")
        self.assertEqual(str(self.client.session["_auth_user_id"]), str(user.pk))

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(email="student@example.test", password="ExistingPassword!2026")

        response = self.client.post(reverse("users:signup"), self.payload())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cette adresse e-mail est déjà utilisée.")
        self.assertEqual(User.objects.filter(email="student@example.test").count(), 1)

    def test_signup_creates_driver_profile_when_driver_is_selected(self):
        payload = {
            "role": "driver",
            "email": "driver@example.test",
            "licence_number": "LIC-2026-07",
            "first_name": "Paul",
            "last_name": "Talla",
            "password1": "UneBonnePhraseDePasse!2026",
            "password2": "UneBonnePhraseDePasse!2026",
        }
        response = self.client.post(reverse("users:signup"), payload)
        self.assertRedirects(response, reverse("users:otp_verify"), fetch_redirect_response=False)
        code = re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)
        self.client.post(reverse("users:otp_verify"), {"code": code})
        user = User.objects.get(email="driver@example.test")
        self.assertEqual(user.role, UserRole.DRIVER)
        self.assertEqual(Chauffeur.objects.get(user=user).licence_number, "LIC-2026-07")

    def test_login_requires_otp_before_session_is_opened(self):
        user = User.objects.create_user(
            email="login@example.test",
            password="UneBonnePhraseDePasse!2026",
            role=UserRole.STUDENT,
            must_change_password=False,
        )
        response = self.client.post(
            reverse("users:login"), {"username": user.email, "password": "UneBonnePhraseDePasse!2026"}
        )
        self.assertRedirects(response, reverse("users:otp_verify"), fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", self.client.session)
        code = re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)
        response = self.client.post(reverse("users:otp_verify"), {"code": code})
        self.assertRedirects(response, reverse("core:home"), fetch_redirect_response=False)
        self.assertEqual(str(self.client.session["_auth_user_id"]), str(user.pk))
