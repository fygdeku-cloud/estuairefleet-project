import re
from datetime import timedelta

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from estuairefleet.users.models import OTPChallenge, OTPPurpose, User, UserRole
from estuairefleet.users.services import verify_otp


@override_settings(
    ESTUAIREFLEET_OTP_RESEND_COOLDOWN_SECONDS=0,
    ESTUAIREFLEET_OTP_MAX_SENDS_PER_WINDOW=10,
)
class PasswordResetFlowTests(TestCase):
    def setUp(self):
        self.old_password = "AncienMotDePasse!2026"
        self.new_password = "NouveauMotDePasse!2026"
        self.user = User.objects.create_user(
            email="reset@example.test",
            matricule="INS-2026-777",
            password=self.old_password,
            role=UserRole.STUDENT,
            must_change_password=False,
        )

    def _request_reset(self, identifier="INS-2026-777"):
        response = self.client.post(reverse("users:password_reset"), {"identifier": identifier})
        self.assertRedirects(response, reverse("users:password_reset_done"), fetch_redirect_response=False)
        challenge = OTPChallenge.objects.get(purpose=OTPPurpose.PASSWORD_RESET)
        code = re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)
        return challenge, code

    def test_request_accepts_matricule_without_exposing_unknown_accounts(self):
        self._request_reset()
        self.assertEqual(mail.outbox[-1].to, [self.user.email])

        mail.outbox.clear()
        response = self.client.post(reverse("users:password_reset"), {"identifier": "unknown@example.test"})

        self.assertRedirects(response, reverse("users:password_reset_done"), fetch_redirect_response=False)
        self.assertEqual(mail.outbox, [])

    def test_full_reset_flow_changes_password_and_allows_relogin(self):
        challenge, code = self._request_reset()

        response = self.client.post(reverse("users:password_reset_otp"), {"code": code})
        self.assertRedirects(response, reverse("users:password_reset_confirm"), fetch_redirect_response=False)
        challenge.refresh_from_db()
        self.assertIsNotNone(challenge.consumed_at)

        response = self.client.post(
            reverse("users:password_reset_confirm"),
            {"new_password1": self.new_password, "new_password2": self.new_password},
        )
        self.assertRedirects(response, reverse("users:password_reset_complete"), fetch_redirect_response=False)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.new_password))
        self.assertFalse(self.user.check_password(self.old_password))
        self.assertFalse(self.user.must_change_password)

        response = self.client.post(
            reverse("users:login"),
            {"username": self.user.email, "password": self.new_password},
        )
        self.assertRedirects(response, reverse("users:otp_verify"), fetch_redirect_response=False)
        login_code = re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)
        response = self.client.post(reverse("users:otp_verify"), {"code": login_code})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(str(self.client.session["_auth_user_id"]), str(self.user.pk))

    def test_expired_otp_is_rejected(self):
        challenge, code = self._request_reset()
        OTPChallenge.objects.filter(pk=challenge.pk).update(expires_at=timezone.now() - timedelta(minutes=1))

        response = self.client.post(reverse("users:password_reset_otp"), {"code": code})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Code invalide, expiré ou trop de tentatives.")
        challenge.refresh_from_db()
        self.assertIsNone(challenge.consumed_at)

    def test_otp_is_single_use(self):
        challenge, code = self._request_reset()

        self.assertIsNotNone(verify_otp(challenge_id=challenge.pk, code=code))
        self.assertIsNone(verify_otp(challenge_id=challenge.pk, code=code))

    def test_otp_usage_is_bound_to_the_requested_flow(self):
        challenge, code = self._request_reset()

        self.assertIsNone(verify_otp(challenge_id=challenge.pk, code=code, purpose=OTPPurpose.LOGIN))
        challenge.refresh_from_db()
        self.assertIsNone(challenge.consumed_at)

    def test_invalid_otp_purpose_is_rejected_without_consuming_code(self):
        challenge, code = self._request_reset()

        self.assertIsNone(verify_otp(challenge_id=challenge.pk, code=code, purpose="unknown"))
        challenge.refresh_from_db()
        self.assertIsNone(challenge.consumed_at)

    @override_settings(ESTUAIREFLEET_OTP_RESEND_COOLDOWN_SECONDS=60)
    def test_resend_is_rate_limited_during_cooldown(self):
        self._request_reset()
        mail.outbox.clear()

        response = self.client.post(reverse("users:password_reset_otp"), {"resend": "1"}, follow=True)

        self.assertContains(response, "Veuillez patienter encore")
        self.assertEqual(mail.outbox, [])

    @override_settings(ESTUAIREFLEET_OTP_MAX_SENDS_PER_WINDOW=2)
    def test_resend_succeeds_then_stops_at_window_limit(self):
        self._request_reset()
        response = self.client.post(reverse("users:password_reset_otp"), {"resend": "1"})
        self.assertRedirects(response, reverse("users:password_reset_otp"), fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), 2)

        response = self.client.post(reverse("users:password_reset_otp"), {"resend": "1"}, follow=True)

        self.assertContains(response, "Trop de demandes")
        self.assertEqual(len(mail.outbox), 2)
