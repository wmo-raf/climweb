"""
Outgoing email settings, edited from Settings -> Email in the CMS.

How the settings are used is described in ``climweb.base.smtp``. Because
whoever controls these settings can read every email the site sends — password
reset links and 2FA codes included — the page is guarded more tightly than
other settings:

  * superusers only (``SuperuserOnlyPermissionPolicy``),
  * every save asks for a fresh authenticator code (or the account password
    for a superuser without an authenticator),
  * switching it on sends a test email first, and nothing is saved unless it
    is delivered,
  * the password is write-only and encrypted at rest.

Changes appear in the CMS history log like any other settings edit.
"""
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django.conf import settings

from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel, Panel
from wagtail.contrib.settings.models import BaseGenericSetting
from wagtail.contrib.settings.registry import register_setting
from wagtail.permission_policies.base import BasePermissionPolicy

from climweb.base.backups.crypto import decrypt_text, encrypt_text
from climweb.base.smtp import PROVIDER_PRESETS, Security, SMTPConfig, friendly_error

__all__ = ["EmailSettings", "EmailSettingsForm"]


class EmailSettingsHelpPanel(Panel):
    """Read-only status and per-provider setup tips at the top of the page."""

    class BoundPanel(Panel.BoundPanel):
        template_name = "admin/panels/email_settings_help_panel.html"

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)
            context.update({
                "enabled": self.instance.enabled,
                "server_host": getattr(settings, "EMAIL_HOST", ""),
                "server_backend": getattr(settings, "EMAIL_BACKEND", ""),
            })
            return context


class SuperuserOnlyPermissionPolicy(BasePermissionPolicy):
    def user_has_permission(self, user, action):
        return user.is_active and user.is_superuser

    def user_has_any_permission(self, user, actions):
        return user.is_active and user.is_superuser

    def users_with_any_permission(self, actions):
        return get_user_model().objects.filter(is_active=True, is_superuser=True)

    def users_with_permission(self, action):
        return self.users_with_any_permission([action])


def user_has_authenticator(user):
    from django_otp.plugins.otp_totp.models import TOTPDevice

    return TOTPDevice.objects.devices_for_user(user, confirmed=True).exists()


def verify_user_code(user, code):
    """True if ``code`` is a current authenticator code for ``user`` or, for a
    user with no authenticator, their account password."""
    from django_otp.plugins.otp_totp.models import TOTPDevice

    code = (code or "").strip()
    if not code:
        return False
    devices = list(TOTPDevice.objects.devices_for_user(user, confirmed=True))
    if devices:
        token = code.replace(" ", "")
        # verify_token() applies django-otp's throttling after failed attempts.
        return any(device.verify_token(token) for device in devices)
    return user.check_password(code)


class EmailSettingsForm(WagtailAdminModelForm):
    confirmation_code = forms.CharField(
        required=True,
        label=_("Confirm it's you"),
        widget=forms.PasswordInput(render_value=False, attrs={"autocomplete": "one-time-code"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Snapshot the stored (encrypted) password before the ModelForm can
        # overwrite it with the blank input value on save.
        self._stored_password = getattr(self.instance, "password", "")

        if "password" in self.fields:
            f = self.fields["password"]
            f.required = False
            f.initial = ""
            f.widget = forms.PasswordInput(render_value=False, attrs={"autocomplete": "new-password"})
            f.help_text = _(
                "Paste to set or change. Leave blank to keep the current password. "
                "Gmail and Microsoft 365 need an app password here."
            )

        for name in ("host", "port"):
            if name in self.fields:
                self.fields[name].required = False

        user = getattr(self, "for_user", None)
        if user is not None and not user_has_authenticator(user):
            self.fields["confirmation_code"].help_text = _(
                "Enter your account password to confirm this change."
            )
        else:
            self.fields["confirmation_code"].help_text = _(
                "Enter the current 6-digit code from your authenticator app to "
                "confirm this change."
            )

    def clean(self):
        cleaned_data = super().clean()
        user = getattr(self, "for_user", None)

        if user is None or not user.is_superuser:
            raise ValidationError(_("Only superusers can change the email settings."))

        if not verify_user_code(user, cleaned_data.get("confirmation_code")):
            self.add_error(
                "confirmation_code",
                _("That code (or password) is not correct. Please try again."),
            )
            return cleaned_data

        provider = cleaned_data.get("provider")
        if provider in PROVIDER_PRESETS:
            host, port, security = PROVIDER_PRESETS[provider]
            cleaned_data.update(host=host, port=port, security=security)

        if not cleaned_data.get("enabled"):
            return cleaned_data

        # Everything below only matters when the settings will be used.
        if not cleaned_data.get("host"):
            self.add_error("host", _("Enter the mail server's host name."))
        if not cleaned_data.get("port"):
            self.add_error("port", _("Enter the mail server's port."))
        if not cleaned_data.get("from_email"):
            username = cleaned_data.get("username") or ""
            if "@" in username:
                cleaned_data["from_email"] = username
            else:
                self.add_error("from_email", _("Enter the address emails are sent from."))
        if not user.email:
            raise ValidationError(_(
                "Your account has no email address, so a test email can't be sent. "
                "Add one under Account settings, then try again."
            ))
        if self.errors:
            return cleaned_data

        config = SMTPConfig(
            host=cleaned_data["host"],
            port=cleaned_data["port"],
            security=cleaned_data.get("security") or Security.STARTTLS,
            username=cleaned_data.get("username") or "",
            password=cleaned_data.get("password") or self._stored_plain_password(),
            from_email=cleaned_data["from_email"],
            from_name=cleaned_data.get("from_name") or "",
        )
        try:
            self.send_test_email(config, user)
        except Exception as e:
            raise ValidationError(friendly_error(e))

        return cleaned_data

    def _stored_plain_password(self):
        try:
            return decrypt_text(self._stored_password) if self._stored_password else ""
        except Exception:
            # Undecryptable (SECRET_KEY changed): the admin must re-enter it.
            return ""

    def send_test_email(self, config, user):
        site_name = getattr(settings, "WAGTAIL_SITE_NAME", "ClimWeb")
        body = _(
            "This is a test email from %(site)s.\n\n"
            "It was sent while %(user)s saved the email settings at %(time)s. "
            "Because you received it, the settings work and have been saved."
        ) % {
            "site": site_name,
            "user": user.get_username(),
            "time": timezone.localtime().strftime("%Y-%m-%d %H:%M %Z"),
        }
        EmailMessage(
            subject=_("%(site)s: email settings test") % {"site": site_name},
            body=body,
            from_email=config.sender,
            to=[user.email],
            connection=config.connection(),
        ).send()

    def save(self, commit=True):
        instance = super().save(commit=False)

        submitted_password = self.cleaned_data.get("password", "")
        if submitted_password:
            instance.password = encrypt_text(submitted_password)
        else:
            instance.password = self._stored_password

        if commit:
            instance.save()
        return instance


@register_setting(icon="mail")
class EmailSettings(BaseGenericSetting):
    base_form_class = EmailSettingsForm

    PROVIDER_CHOICES = (
        ("gmail", _("Gmail / Google Workspace")),
        ("microsoft", _("Microsoft 365 / Outlook")),
        ("custom", _("Other (enter server details)")),
    )

    SECURITY_CHOICES = (
        (Security.STARTTLS, _("STARTTLS (usually port 587)")),
        (Security.SSL, _("SSL/TLS (usually port 465)")),
        (Security.NONE, _("None (not recommended)")),
    )

    enabled = models.BooleanField(
        default=False,
        verbose_name=_("Use these settings to send email"),
        help_text=_(
            "When off, the site uses the email settings from the server "
            "configuration, as before. Turning this on sends you a test email "
            "first; nothing is saved unless it arrives."
        ),
    )
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        default="custom",
        verbose_name=_("Email provider"),
    )
    host = models.CharField(max_length=255, blank=True, verbose_name=_("SMTP server"),
                            help_text=_("For example mail.example.org"))
    port = models.PositiveIntegerField(default=587, null=True, blank=True, verbose_name=_("Port"))
    security = models.CharField(max_length=10, choices=SECURITY_CHOICES,
                                default=Security.STARTTLS, verbose_name=_("Security"))
    username = models.CharField(max_length=255, blank=True, verbose_name=_("Username"),
                                help_text=_("Usually the full email address of the account."))
    # Stored ENCRYPTED at rest; edited via the write-only form field above.
    password = models.CharField(max_length=512, blank=True, verbose_name=_("Password"))
    from_email = models.EmailField(
        blank=True,
        verbose_name=_("Send emails from"),
        help_text=_(
            "Every email the site sends comes from this address. Leave blank to "
            "use the username. Gmail and Microsoft 365 only allow the account's "
            "own address or an alias it is allowed to send as."
        ),
    )
    from_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Sender name"),
        help_text=_("Optional. Shown to recipients, e.g. 'National Meteorological Service'."),
    )

    class Meta:
        verbose_name = _("Email Settings")

    @classmethod
    def get_permission_policy(cls):
        # Hides the menu item and refuses the page to everyone else, even if
        # the permission is ticked for a group in Settings -> Groups.
        return SuperuserOnlyPermissionPolicy(cls)

    def get_password(self):
        return decrypt_text(self.password) if self.password else ""

    def get_config(self):
        """The SMTPConfig for these settings. Raises if the stored password
        can't be decrypted (e.g. SECRET_KEY was changed)."""
        host, port, security = PROVIDER_PRESETS.get(
            self.provider, (self.host, self.port, self.security))
        if not host or not port:
            raise ValueError("no SMTP server configured")
        return SMTPConfig(
            host=host,
            port=port,
            security=security,
            username=self.username,
            password=self.get_password(),
            from_email=self.from_email or (self.username if "@" in self.username else ""),
            from_name=self.from_name,
        )

    panels = [
        EmailSettingsHelpPanel(),
        FieldPanel("provider"),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel("host", classname="col8"),
                FieldPanel("port", classname="col4"),
            ]),
            FieldPanel("security"),
        ], heading=_("Server"), classname="email-custom-server"),
        MultiFieldPanel([
            FieldPanel("username"),
            FieldPanel("password"),
        ], heading=_("Account")),
        MultiFieldPanel([
            FieldPanel("from_email"),
            FieldPanel("from_name"),
        ], heading=_("Sender")),
        FieldPanel("enabled"),
        FieldPanel("confirmation_code"),
    ]
