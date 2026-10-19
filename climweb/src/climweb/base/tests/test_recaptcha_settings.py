from unittest import mock
from urllib.error import URLError

from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings
from django.urls import reverse
from django_otp.oath import TOTP
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_recaptcha.client import RecaptchaResponse
from django_recaptcha.constants import TEST_PRIVATE_KEY, TEST_PUBLIC_KEY
from wagtail.contrib.forms.models import FormMixin
from wagtail.contrib.settings.views import get_setting_edit_handler
from wagtailcaptcha.forms import WagtailCaptchaFormBuilder

from climweb.base.backups.crypto import decrypt_text, encrypt_text
from climweb.base.forms import CustomWagtailCaptchaFormBuilder
from climweb.base.models.recaptcha_settings import RecaptchaSettings
from climweb.base.recaptcha import SiteCaptchaFormBuilder, SiteReCaptchaField, get_active_keys

ENV_PUBLIC = "6Lenv-public-key-00000000000000000000000"
ENV_PRIVATE = "6Lenv-private-key-0000000000000000000000"
CMS_PUBLIC = "6Lcms-public-key-00000000000000000000000"
CMS_PRIVATE = "6Lcms-private-key-0000000000000000000000"

SERVER_KEYS = dict(RECAPTCHA_PUBLIC_KEY=ENV_PUBLIC, RECAPTCHA_PRIVATE_KEY=ENV_PRIVATE)

GOOGLE_ACCEPTS = RecaptchaResponse(is_valid=True)
GOOGLE_REJECTS_SECRET = RecaptchaResponse(is_valid=False, error_codes=["invalid-input-secret"])
GOOGLE_REJECTS_TOKEN = RecaptchaResponse(is_valid=False, error_codes=["invalid-input-response"])
TEST_TOKEN = "03AFcWeA-token-from-the-test-box"


def _totp_token(device):
    totp = TOTP(device.bin_key, device.step, device.t0, device.digits, device.drift)
    return str(totp.token()).zfill(device.digits)


def _enable_cms_keys(**overrides):
    values = dict(enabled=True, public_key=CMS_PUBLIC, private_key=encrypt_text(CMS_PRIVATE))
    values.update(overrides)
    recaptcha_settings = RecaptchaSettings.load()
    for name, value in values.items():
        setattr(recaptcha_settings, name, value)
    recaptcha_settings.save()
    return recaptcha_settings


def _captcha_field(builder_class=SiteCaptchaFormBuilder):
    form_class = builder_class([]).get_form_class()
    return form_class().fields[WagtailCaptchaFormBuilder.CAPTCHA_FIELD_NAME]


@override_settings(**SERVER_KEYS)
class KeyResolutionTests(TestCase):
    """Keys are looked up each time a form is built, not when Django starts."""

    def test_uses_server_keys_when_cms_settings_are_off(self):
        field = _captcha_field()
        self.assertIsInstance(field, SiteReCaptchaField)
        self.assertEqual((field.public_key, field.private_key), (ENV_PUBLIC, ENV_PRIVATE))
        self.assertEqual(field.widget.attrs["data-sitekey"], ENV_PUBLIC)

    def test_uses_cms_keys_when_switched_on(self):
        _enable_cms_keys()
        field = _captcha_field()
        self.assertEqual((field.public_key, field.private_key), (CMS_PUBLIC, CMS_PRIVATE))
        self.assertEqual(field.widget.attrs["data-sitekey"], CMS_PUBLIC)

    def test_change_applies_to_the_next_form_without_a_restart(self):
        self.assertEqual(_captcha_field().public_key, ENV_PUBLIC)
        _enable_cms_keys()
        self.assertEqual(_captcha_field().public_key, CMS_PUBLIC)
        _enable_cms_keys(enabled=False)
        self.assertEqual(_captcha_field().public_key, ENV_PUBLIC)

    def test_custom_builder_used_by_flexible_and_data_request_forms(self):
        _enable_cms_keys()
        field = _captcha_field(CustomWagtailCaptchaFormBuilder)
        self.assertEqual(field.private_key, CMS_PRIVATE)

    def test_falls_back_to_server_keys_if_secret_cannot_be_decrypted(self):
        """E.g. after SECRET_KEY was changed."""
        _enable_cms_keys(private_key="not-a-fernet-token")
        self.assertEqual(get_active_keys().private_key, ENV_PRIVATE)
        self.assertEqual(_captcha_field().public_key, ENV_PUBLIC)

    def test_falls_back_to_server_keys_if_cms_keys_are_incomplete(self):
        _enable_cms_keys(private_key="")
        self.assertEqual(get_active_keys().public_key, ENV_PUBLIC)

    def test_verification_sends_the_active_secret_to_google(self):
        _enable_cms_keys()
        field = _captcha_field()
        with mock.patch("django_recaptcha.fields.client.submit",
                        return_value=RecaptchaResponse(is_valid=True)) as submit:
            field.validate("token-from-browser")
        self.assertEqual(submit.call_args.kwargs["private_key"], CMS_PRIVATE)

    def test_every_captcha_form_page_uses_the_site_keys(self):
        """Contact, feedback, data request, flexible forms, event registration..."""
        captcha_pages = [
            model for model in apps.get_models()
            if issubclass(model, FormMixin) and issubclass(model.form_builder, WagtailCaptchaFormBuilder)
        ]
        names = {model.__name__ for model in captcha_pages}
        self.assertTrue({"ContactPage", "FeedbackPage", "DataRequestPage", "FlexibleFormPage",
                         "EventRegistrationPage"} <= names, names)
        for model in captcha_pages:
            self.assertTrue(issubclass(model.form_builder, SiteCaptchaFormBuilder), model.__name__)


@override_settings(**SERVER_KEYS)
@mock.patch("climweb.base.recaptcha.client.submit", return_value=GOOGLE_ACCEPTS)
class FormTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="admin", email="admin@met.example", password="s3cret-pass")
        self.totp = TOTPDevice.objects.create(user=self.user, name="Phone", confirmed=True)
        self.form_class = get_setting_edit_handler(RecaptchaSettings).get_form_class()

    def _form(self, user=None, **overrides):
        data = dict(
            public_key=CMS_PUBLIC,
            private_key=CMS_PRIVATE,
            test_token=TEST_TOKEN,
            confirmation_code=_totp_token(self.totp),
        )
        data.update(overrides)
        data = {k: v for k, v in data.items() if v is not None}
        return self.form_class(data, instance=RecaptchaSettings.load(), for_user=user or self.user)

    def test_saving_while_off_does_not_ask_google_and_encrypts_secret(self, submit):
        form = self._form()
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        stored = RecaptchaSettings.load()
        self.assertNotEqual(stored.private_key, CMS_PRIVATE)
        self.assertEqual(decrypt_text(stored.private_key), CMS_PRIVATE)
        self.assertFalse(stored.enabled)
        submit.assert_not_called()

    def test_switching_on_checks_the_test_box_token_with_google(self, submit):
        form = self._form(enabled="on")
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        self.assertEqual(submit.call_args.kwargs["private_key"], CMS_PRIVATE)
        self.assertEqual(submit.call_args.kwargs["recaptcha_response"], TEST_TOKEN)
        self.assertTrue(RecaptchaSettings.load().enabled)
        self.assertEqual(get_active_keys().public_key, CMS_PUBLIC)

    def test_secret_rejected_by_google_blocks_saving(self, submit):
        submit.return_value = GOOGLE_REJECTS_SECRET
        form = self._form(enabled="on")
        self.assertFalse(form.is_valid())
        self.assertIn("did not accept the secret key", str(form.errors["test_token"]))
        self.assertFalse(RecaptchaSettings.load().enabled)

    def test_keys_from_different_sites_block_saving(self, submit):
        submit.return_value = GOOGLE_REJECTS_TOKEN
        form = self._form(enabled="on")
        self.assertFalse(form.is_valid())
        self.assertIn("belong together", form.errors["test_token"][0])

    def test_switching_on_without_ticking_the_test_box_is_refused(self, submit):
        form = self._form(enabled="on", test_token="")
        self.assertFalse(form.is_valid())
        self.assertIn("Tick", str(form.errors["test_token"]))
        submit.assert_not_called()

    def test_google_unreachable_blocks_saving(self, submit):
        submit.side_effect = URLError("timed out")
        form = self._form(enabled="on")
        self.assertFalse(form.is_valid())
        self.assertIn("Could not reach Google", str(form.errors["test_token"]))

    def test_secret_is_never_rendered_and_blank_keeps_it(self, submit):
        _enable_cms_keys(enabled=False)
        form = self._form(private_key="", enabled="on")
        self.assertNotIn(CMS_PRIVATE, str(form["private_key"]))
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertEqual(RecaptchaSettings.load().get_private_key(), CMS_PRIVATE)
        # The stored secret is what gets checked.
        self.assertEqual(submit.call_args.kwargs["private_key"], CMS_PRIVATE)

    def test_switching_on_without_keys_is_refused(self, submit):
        form = self._form(enabled="on", public_key="", private_key="")
        self.assertFalse(form.is_valid())
        self.assertIn("public_key", form.errors)
        self.assertIn("private_key", form.errors)
        submit.assert_not_called()

    def test_malformed_and_test_keys_are_refused(self, submit):
        form = self._form(public_key="not-a-key")
        self.assertFalse(form.is_valid())
        self.assertIn("40 characters", str(form.errors["public_key"]))

        # An authenticator code can only be used once.
        self.totp.delete()
        form = self._form(enabled="on", public_key=TEST_PUBLIC_KEY, private_key=TEST_PRIVATE_KEY,
                          confirmation_code="s3cret-pass")
        self.assertFalse(form.is_valid())
        self.assertIn("test key", str(form.errors["public_key"]))
        self.assertIn("test key", str(form.errors["private_key"]))

    def test_same_key_twice_is_refused(self, submit):
        form = self._form(enabled="on", private_key=CMS_PUBLIC)
        self.assertFalse(form.is_valid())
        self.assertIn("same as the site key", str(form.errors["private_key"]))

    def test_wrong_code_is_rejected(self, submit):
        form = self._form(enabled="on", confirmation_code="000000")
        self.assertFalse(form.is_valid())
        self.assertIn("confirmation_code", form.errors)
        submit.assert_not_called()

    def test_superuser_without_authenticator_confirms_with_password(self, submit):
        self.totp.delete()
        self.assertFalse(self._form(confirmation_code="wrong").is_valid())
        self.assertTrue(self._form(confirmation_code="s3cret-pass").is_valid())

    def test_non_superuser_is_rejected(self, submit):
        editor = get_user_model().objects.create_user(username="ed", password="pw-12345")
        form = self._form(user=editor, confirmation_code="pw-12345")
        self.assertFalse(form.is_valid())
        self.assertIn("Only superusers", str(form.non_field_errors()))


@override_settings(WAGTAIL_2FA_REQUIRED=False, CLIMWEB_2FA_SUPERUSER_REQUIRED=False)
class AccessTests(TestCase):
    url = reverse("wagtailsettings:edit", args=["base", "recaptchasettings"])

    def test_superuser_can_open_the_page(self):
        admin = get_user_model().objects.create_superuser(username="admin", password="pw")
        self.client.force_login(admin)
        response = self.client.get(self.url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "confirmation_code")
        self.assertContains(self.client.get(reverse("wagtailadmin_home")), self.url)

    @override_settings(**SERVER_KEYS)
    def test_page_never_shows_the_secret(self):
        _enable_cms_keys()
        admin = get_user_model().objects.create_superuser(username="admin", password="pw")
        self.client.force_login(admin)
        response = self.client.get(self.url, follow=True)
        self.assertContains(response, CMS_PUBLIC)
        self.assertNotContains(response, CMS_PRIVATE)
        self.assertNotContains(response, ENV_PRIVATE)
        self.assertNotContains(response, RecaptchaSettings.load().private_key)

    def test_editor_with_the_permission_is_still_refused(self):
        """Ticking the permission for a group in Settings -> Groups has no effect."""
        editor = get_user_model().objects.create_user(username="ed", password="pw")
        editor.user_permissions.add(
            Permission.objects.get(codename="access_admin"),
            Permission.objects.get(codename="change_recaptchasettings"),
        )
        self.client.force_login(editor)

        response = self.client.get(self.url, follow=True)
        self.assertNotContains(response, "confirmation_code")
        self.assertNotContains(self.client.get(reverse("wagtailadmin_home")), self.url)
