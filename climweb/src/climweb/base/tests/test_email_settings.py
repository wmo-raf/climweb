import smtplib
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core import mail
from django.core.mail import EmailMessage
from django.core.mail.backends import locmem
from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django_otp.oath import TOTP
from django_otp.plugins.otp_totp.models import TOTPDevice
from wagtail.contrib.settings.views import get_setting_edit_handler

from climweb.base.backups.crypto import decrypt_text, encrypt_text
from climweb.base.mail import get_default_from_email
from climweb.base.models.email_settings import EmailSettings
from climweb.base.smtp import SiteSMTPBackend, SMTPConfig, friendly_error, get_active_config
from climweb.pages.flexible_forms.models import FlexibleFormPage

SERVER_EMAIL_SETTINGS = dict(
    EMAIL_HOST="env-mail.example.org",
    EMAIL_PORT=25,
    EMAIL_HOST_USER="env-user",
    EMAIL_HOST_PASSWORD="env-pass",
    EMAIL_USE_TLS=False,
    DEFAULT_FROM_EMAIL="env@example.org",
)


def _totp_token(device):
    totp = TOTP(device.bin_key, device.step, device.t0, device.digits, device.drift)
    return str(totp.token()).zfill(device.digits)


def _enable_cms_settings(**overrides):
    values = dict(
        enabled=True,
        provider="custom",
        host="smtp.cms.example.org",
        port=465,
        security="ssl",
        username="weather@cms.example.org",
        password=encrypt_text("cms-pass"),
        from_email="",
        from_name="Met Service",
    )
    values.update(overrides)
    email_settings = EmailSettings.load()
    for name, value in values.items():
        setattr(email_settings, name, value)
    email_settings.save()
    return email_settings


@override_settings(**SERVER_EMAIL_SETTINGS)
class BackendTests(TestCase):
    """Every email goes through SiteSMTPBackend, so it decides where mail goes."""

    def test_uses_server_settings_when_cms_settings_are_off(self):
        backend = SiteSMTPBackend()
        self.assertEqual((backend.host, backend.port), ("env-mail.example.org", 25))
        self.assertEqual((backend.username, backend.password), ("env-user", "env-pass"))
        self.assertIsNone(get_active_config())

    def test_uses_cms_settings_when_switched_on(self):
        _enable_cms_settings()
        backend = SiteSMTPBackend()
        self.assertEqual((backend.host, backend.port), ("smtp.cms.example.org", 465))
        self.assertEqual((backend.username, backend.password), ("weather@cms.example.org", "cms-pass"))
        self.assertTrue(backend.use_ssl)
        self.assertFalse(backend.use_tls)
        self.assertEqual(backend.timeout, 20)

    def test_provider_preset_overrides_stored_server_details(self):
        _enable_cms_settings(provider="microsoft", host="ignored", port=1, security="none")
        backend = SiteSMTPBackend()
        self.assertEqual((backend.host, backend.port), ("smtp.office365.com", 587))
        self.assertTrue(backend.use_tls)

    def test_sends_everything_from_the_configured_sender(self):
        """Providers reject other senders, so 2FA codes, resets, forms all use it."""
        _enable_cms_settings()
        message = EmailMessage("Hi", "Body", "someone-else@example.com", ["to@example.com"])
        with mock.patch.object(SMTPEmailBackend, "send_messages", return_value=1) as send:
            SiteSMTPBackend().send_messages([message])
        send.assert_called_once()
        self.assertEqual(message.from_email, "Met Service <weather@cms.example.org>")

    def test_leaves_sender_alone_with_server_settings(self):
        message = EmailMessage("Hi", "Body", "someone-else@example.com", ["to@example.com"])
        with mock.patch.object(SMTPEmailBackend, "send_messages", return_value=1):
            SiteSMTPBackend().send_messages([message])
        self.assertEqual(message.from_email, "someone-else@example.com")

    def test_falls_back_to_server_settings_if_password_cannot_be_decrypted(self):
        """E.g. after SECRET_KEY was changed."""
        _enable_cms_settings(password="not-a-fernet-token")
        backend = SiteSMTPBackend()
        self.assertEqual(backend.host, "env-mail.example.org")

    def test_default_sender_follows_cms_settings(self):
        self.assertEqual(get_default_from_email(), "env@example.org")
        _enable_cms_settings(from_email="noreply@cms.example.org", from_name="")
        self.assertEqual(get_default_from_email(), "noreply@cms.example.org")

    def test_disable_command_switches_back_to_server_settings(self):
        _enable_cms_settings()
        call_command("disable_cms_email", stdout=mock.Mock())
        self.assertFalse(EmailSettings.load().enabled)
        self.assertEqual(SiteSMTPBackend().host, "env-mail.example.org")


class FriendlyErrorTests(TestCase):
    def test_microsoft_smtp_auth_disabled(self):
        exc = smtplib.SMTPAuthenticationError(
            535, b"5.7.139 Authentication unsuccessful, SmtpClientAuthentication is disabled for the Tenant.")
        self.assertIn("SMTP AUTH is turned off", friendly_error(exc))
        self.assertIn("5.7.139", friendly_error(exc))

    def test_gmail_needs_app_password(self):
        exc = smtplib.SMTPAuthenticationError(534, b"5.7.9 Application-specific password required.")
        self.assertIn("App Password", friendly_error(exc))

    def test_sender_not_allowed(self):
        exc = smtplib.SMTPDataError(554, b"5.2.252 SendAsDenied; user not allowed to send as x")
        self.assertIn("will not send from this sender address", friendly_error(exc))

    def test_unreachable_server(self):
        self.assertIn("Could not reach", friendly_error(TimeoutError("timed out")))


def _locmem_connection(self, fail_silently=False):
    return locmem.EmailBackend()


@override_settings(**SERVER_EMAIL_SETTINGS)
class FormTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="admin", email="admin@met.example", password="s3cret-pass")
        self.totp = TOTPDevice.objects.create(user=self.user, name="Phone", confirmed=True)
        self.form_class = get_setting_edit_handler(EmailSettings).get_form_class()

    def _data(self, **overrides):
        data = dict(
            provider="custom",
            host="smtp.cms.example.org",
            port="587",
            security="starttls",
            username="weather@cms.example.org",
            password="new-pass",
            from_email="",
            from_name="",
            confirmation_code=_totp_token(self.totp),
        )
        data.update(overrides)
        return {k: v for k, v in data.items() if v is not None}

    def _form(self, user=None, **overrides):
        return self.form_class(self._data(**overrides), instance=EmailSettings.load(),
                               for_user=user or self.user)

    def test_saving_while_off_needs_no_test_email_and_encrypts_password(self):
        form = self._form()
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        stored = EmailSettings.load()
        self.assertNotEqual(stored.password, "new-pass")
        self.assertEqual(decrypt_text(stored.password), "new-pass")
        self.assertEqual(len(mail.outbox), 0)

    def test_password_is_never_rendered_and_blank_keeps_it(self):
        _enable_cms_settings(enabled=False)
        form = self._form(password="")
        self.assertNotIn("cms-pass", str(form["password"]))
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertEqual(EmailSettings.load().get_password(), "cms-pass")

    def test_wrong_code_is_rejected(self):
        form = self._form(confirmation_code="000000")
        self.assertFalse(form.is_valid())
        self.assertIn("confirmation_code", form.errors)

    def test_superuser_without_authenticator_confirms_with_password(self):
        self.totp.delete()
        self.assertFalse(self._form(confirmation_code="wrong").is_valid())
        self.assertTrue(self._form(confirmation_code="s3cret-pass").is_valid())

    def test_non_superuser_is_rejected(self):
        editor = get_user_model().objects.create_user(username="ed", password="pw-12345")
        form = self._form(user=editor, confirmation_code="pw-12345")
        self.assertFalse(form.is_valid())
        self.assertIn("Only superusers", str(form.non_field_errors()))

    @mock.patch.object(SMTPConfig, "connection", _locmem_connection)
    def test_switching_on_sends_a_test_email_first(self):
        form = self._form(enabled="on", from_name="Met Service")
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["admin@met.example"])
        self.assertEqual(mail.outbox[0].from_email, "Met Service <weather@cms.example.org>")
        stored = EmailSettings.load()
        self.assertTrue(stored.enabled)
        # Blank sender defaults to the username.
        self.assertEqual(stored.from_email, "weather@cms.example.org")

    def test_failed_test_email_blocks_saving(self):
        failing = mock.Mock()
        failing.send_messages.side_effect = smtplib.SMTPAuthenticationError(
            535, b"5.7.139 Authentication unsuccessful, SmtpClientAuthentication is disabled")
        with mock.patch.object(SMTPConfig, "connection", return_value=failing):
            form = self._form(enabled="on", provider="microsoft")
            self.assertFalse(form.is_valid())
        self.assertIn("SMTP AUTH is turned off", str(form.non_field_errors()))
        self.assertFalse(EmailSettings.load().enabled)

    @mock.patch.object(SMTPConfig, "connection", _locmem_connection)
    def test_provider_preset_fills_in_server(self):
        form = self._form(enabled="on", provider="gmail", host="", port="")
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        stored = EmailSettings.load()
        self.assertEqual((stored.host, stored.port), ("smtp.gmail.com", 587))


@override_settings(WAGTAIL_2FA_REQUIRED=False, CLIMWEB_2FA_SUPERUSER_REQUIRED=False)
class AccessTests(TestCase):
    url = reverse("wagtailsettings:edit", args=["base", "emailsettings"])

    def test_superuser_can_open_the_page(self):
        admin = get_user_model().objects.create_superuser(username="admin", password="pw")
        self.client.force_login(admin)
        response = self.client.get(self.url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "confirmation_code")
        self.assertContains(self.client.get(reverse("wagtailadmin_home")), self.url)

    def test_editor_with_the_permission_is_still_refused(self):
        """Ticking the permission for a group in Settings -> Groups has no effect."""
        editor = get_user_model().objects.create_user(username="ed", password="pw")
        editor.user_permissions.add(
            Permission.objects.get(codename="access_admin"),
            Permission.objects.get(codename="change_emailsettings"),
        )
        self.client.force_login(editor)

        response = self.client.get(self.url, follow=True)
        self.assertNotContains(response, "confirmation_code")
        self.assertNotContains(self.client.get(reverse("wagtailadmin_home")), self.url)


@override_settings(**SERVER_EMAIL_SETTINGS, EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class FormPageEmailTests(TestCase):
    def test_form_pages_have_no_from_field(self):
        from climweb.pages.contact.models import ContactPage
        from climweb.pages.data_request.models import DataRequestPage
        from climweb.pages.feedback.models import FeedbackPage

        for model in (ContactPage, DataRequestPage, FeedbackPage, FlexibleFormPage):
            field_names = {f.name for f in model._meta.get_fields()}
            self.assertNotIn("from_address", field_names, model.__name__)

    def test_submission_is_sent_from_the_site_sender_with_reply_to(self):
        _enable_cms_settings(from_email="noreply@cms.example.org", from_name="")
        page = FlexibleFormPage(title="Ask us", subject="New question", to_address="staff@met.example")
        form = mock.Mock(cleaned_data={"email": "visitor@example.com"})
        with mock.patch.object(FlexibleFormPage, "render_email", return_value="body"):
            page.send_mail(form)

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.from_email, "noreply@cms.example.org")
        self.assertEqual(message.reply_to, ["visitor@example.com"])
        self.assertEqual(message.to, ["staff@met.example"])
