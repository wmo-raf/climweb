from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.http import urlencode
from django_otp.oath import TOTP
from django_otp.plugins.otp_email.models import EmailDevice
from django_otp.plugins.otp_totp.models import TOTPDevice

from climweb.base.two_factor import mask_email


def _totp_token(device):
    totp = TOTP(device.bin_key, device.step, device.t0, device.digits, device.drift)
    return str(totp.token()).zfill(device.digits)


@override_settings(
    WAGTAIL_2FA_REQUIRED=True,
    CLIMWEB_2FA_SUPERUSER_REQUIRED=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="climweb@example.com",
)
class EmailFallbackTests(TestCase):
    """A user who has lost their phone gets back in with an emailed code."""

    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="editor", email="jane.doe@met.example", password="s3cret-pass"
        )
        self.totp = TOTPDevice.objects.create(user=self.user, name="Phone", confirmed=True)
        self.client.force_login(self.user)
        self.email_code_url = reverse("climweb_2fa_email_code")
        self.auth_url = reverse("wagtail_2fa_auth")

    def _emailed_token(self):
        return EmailDevice.objects.get(user=self.user).token

    def _devices_url(self):
        return reverse("wagtail_2fa_device_list", kwargs={"user_id": self.user.pk})

    def test_email_code_page_is_reachable_before_verification(self):
        """Otherwise the middleware would bounce the button back to the code prompt."""
        response = self.client.post(self.email_code_url)
        self.assertTrue(response.url.startswith(self.auth_url))
        self.assertEqual(len(mail.outbox), 1)

    def test_code_is_emailed_to_the_account_address(self):
        self.client.post(self.email_code_url)

        message = mail.outbox[0]
        self.assertEqual(message.to, ["jane.doe@met.example"])
        self.assertIn(self._emailed_token(), message.body)
        self.assertIn("someone else knows your password", message.body)

    def test_emailed_code_signs_in_and_lands_on_the_devices_page(self):
        """Someone recovering has lost their phone; take them where they add one."""
        home = reverse("wagtailadmin_home")
        response = self.client.post(self.email_code_url, {"next": home})
        self.assertEqual(
            response.url, f"{self.auth_url}?{urlencode({'next': self._devices_url()})}"
        )

        # The verification page carries `next` through in a hidden field.
        page = self.client.get(response.url)
        self.assertContains(page, f'name="next" value="{self._devices_url()}"')

        response = self.client.post(
            self.auth_url, {"otp_token": self._emailed_token(), "next": self._devices_url()}
        )
        self.assertRedirects(response, self._devices_url(), fetch_redirect_response=False)
        self.assertEqual(self.client.get(self._devices_url()).status_code, 200)
        self.assertEqual(self.client.get(reverse("wagtail_2fa_device_new")).status_code, 200)

    def test_emailed_code_is_single_use(self):
        self.client.post(self.email_code_url)
        token = self._emailed_token()
        device = EmailDevice.objects.get(user=self.user)

        self.assertTrue(device.verify_token(token))
        device.refresh_from_db()
        self.assertFalse(device.verify_token(token))

    def test_authenticator_code_still_works(self):
        self.client.post(self.email_code_url)
        home = reverse("wagtailadmin_home")
        response = self.client.post(
            self.auth_url, {"otp_token": _totp_token(self.totp), "next": home}
        )
        self.assertRedirects(response, home, fetch_redirect_response=False)

    def test_next_is_kept_when_no_code_is_sent(self):
        self.client.post(self.email_code_url)
        response = self.client.post(self.email_code_url, {"next": "/cms-admin/pages/"})
        self.assertEqual(response.url, f"{self.auth_url}?next=%2Fcms-admin%2Fpages%2F")

    def test_repeat_requests_within_the_cooldown_send_one_email(self):
        self.client.post(self.email_code_url)
        response = self.client.post(self.email_code_url, follow=True)

        self.assertEqual(len(mail.outbox), 1)
        self.assertContains(response, "less than a minute ago")

    def test_get_is_not_allowed(self):
        """Sending an email is a side effect; keep it behind POST and CSRF."""
        self.assertEqual(self.client.get(self.email_code_url).status_code, 405)

    def test_user_without_an_email_address_is_told_to_ask_an_admin(self):
        self.user.email = ""
        self.user.save()

        response = self.client.post(self.email_code_url, follow=True)

        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(EmailDevice.objects.filter(user=self.user).exists())
        self.assertContains(response, "no email address on your account")

    def test_mail_failure_is_reported_not_raised(self):
        with mock.patch.object(EmailDevice, "send_mail", side_effect=OSError("smtp down")):
            with self.assertLogs("climweb.base.two_factor", level="ERROR"):
                response = self.client.post(self.email_code_url, follow=True)

        self.assertContains(response, "couldn&#x27;t send the email")

    def test_user_without_an_authenticator_is_sent_to_enrolment(self):
        """They aren't recovering anything, and an EmailDevice would wrongly
        mark them as enrolled."""
        self.totp.delete()

        response = self.client.post(self.email_code_url)

        self.assertRedirects(
            response, reverse("wagtail_2fa_device_new"), fetch_redirect_response=False
        )
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(EmailDevice.objects.filter(user=self.user).exists())

    def test_verification_page_offers_the_email_button(self):
        response = self.client.get(self.auth_url)
        self.assertContains(response, self.email_code_url)
        self.assertContains(response, "Email me a code instead")


@override_settings(
    WAGTAIL_2FA_REQUIRED=True,
    CLIMWEB_2FA_SUPERUSER_REQUIRED=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="climweb@example.com",
)
class NonSuperuserEmailFallbackTests(TestCase):
    """Editors go through upstream wagtail-2fa's middleware logic, not ours."""

    def test_enrolled_editor_can_request_a_code(self):
        user = get_user_model().objects.create_user(
            username="editor", email="ed@met.example", password="s3cret-pass"
        )
        user.user_permissions.add(
            Permission.objects.get(content_type__app_label="wagtailadmin", codename="access_admin")
        )
        TOTPDevice.objects.create(user=user, name="Phone", confirmed=True)
        self.client.force_login(user)

        response = self.client.post(reverse("climweb_2fa_email_code"))

        self.assertTrue(response.url.startswith(reverse("wagtail_2fa_auth")))
        self.assertEqual(len(mail.outbox), 1)


@override_settings(WAGTAIL_2FA_REQUIRED=True, CLIMWEB_2FA_SUPERUSER_REQUIRED=True)
class AdminResetTests(TestCase):
    """Removing someone's authenticator must still let them re-enrol with a password."""

    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="editor", email="jane@met.example", password="s3cret-pass"
        )
        self.totp = TOTPDevice.objects.create(user=self.user, name="Phone", confirmed=True)
        EmailDevice.objects.create(user=self.user, name="Email", confirmed=True)

    def test_removing_the_last_authenticator_removes_the_email_fallback(self):
        self.totp.delete()
        self.assertFalse(EmailDevice.objects.filter(user=self.user).exists())

        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("wagtail_2fa_device_new")).status_code, 200)

    def test_removing_one_of_several_authenticators_keeps_it(self):
        TOTPDevice.objects.create(user=self.user, name="Tablet", confirmed=True)
        self.totp.delete()
        self.assertTrue(EmailDevice.objects.filter(user=self.user).exists())

    def test_discarding_an_unconfirmed_enrolment_keeps_it(self):
        """wagtail-2fa deletes half-finished enrolments whenever the page loads."""
        TOTPDevice.objects.create(user=self.user, name="Pending", confirmed=False).delete()
        self.assertTrue(EmailDevice.objects.filter(user=self.user).exists())


# 2FA enforcement is off so the test can reach the Account page without first
# enrolling and verifying a device; the panel itself doesn't depend on it.
@override_settings(WAGTAIL_2FA_REQUIRED=False, CLIMWEB_2FA_SUPERUSER_REQUIRED=False)
class AccountPagePanelTests(TestCase):
    """wagtail-2fa hides its link under Account -> "More actions"."""

    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="editor", email="jane@met.example", password="s3cret-pass"
        )
        self.client.force_login(self.user)
        self.devices_url = reverse("wagtail_2fa_device_list", kwargs={"user_id": self.user.pk})

    def test_account_page_links_to_the_devices_page(self):
        response = self.client.get(reverse("wagtailadmin_account"))
        self.assertContains(response, "Two-factor authentication")
        self.assertContains(response, f'href="{self.devices_url}" class="button')

    def test_saving_other_account_settings_still_works(self):
        """The Account view validates every panel's form on POST."""
        url = reverse("wagtailadmin_account")
        data = {}
        for panels in self.client.get(url).context["panels_by_tab"].values():
            for panel in panels:
                form = panel.get_form()
                for name, field in form.fields.items():
                    value = form.get_initial_for_field(field, name)
                    if value and not hasattr(value, "file"):  # skip the empty avatar
                        data[form.add_prefix(name)] = value
        data.update({"name_email-first_name": "Jane", "name_email-last_name": "Doe"})

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Jane")


class MaskEmailTests(TestCase):
    def test_masks_the_local_part(self):
        self.assertEqual(mask_email("jane.doe@met.go.ke"), "j*******@met.go.ke")

    def test_single_character_local_part_is_still_masked(self):
        self.assertEqual(mask_email("j@met.go.ke"), "j*@met.go.ke")
