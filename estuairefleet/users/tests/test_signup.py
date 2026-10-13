import re
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from estuairefleet.users.models import Chauffeur, Student, User, UserRole
from estuairefleet.users.services import issue_otp


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

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
        EMAIL_HOST="mailpit",
        EMAIL_PORT=1025,
        EMAIL_USE_TLS=False,
        EMAIL_USE_SSL=False,
    )
    @patch("django.core.mail.backends.smtp.EmailBackend.send_messages", autospec=True, return_value=1)
    def test_otp_is_sent_through_the_configured_mailpit_smtp_backend(self, send_messages):
        issue_otp(email="mailpit@example.test", purpose="signup")

        send_messages.assert_called_once()
        email_messages = send_messages.call_args.args[-1]
        self.assertEqual(len(email_messages), 1)
        self.assertEqual(email_messages[0].to, ["mailpit@example.test"])
        self.assertRegex(email_messages[0].body, r"\b\d{6}\b")
