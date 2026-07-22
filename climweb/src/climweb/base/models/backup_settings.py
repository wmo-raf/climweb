"""
Cloud backup configuration, managed entirely from the CMS admin.

This replaces the per-server, command-line setup previously handled by the
separate ``climweb-backup-sync`` repo. Each site configures its own Google
Drive destination from Settings -> Backup and connects an account in one of two
ways — both handled in the browser, no server access required:

  * **Connect button** — one-click OAuth consent flow (needs the site's Google
    OAuth Client ID / Secret, entered once on this page).
  * **Paste a token** — paste a refresh token generated elsewhere (e.g. Google
    OAuth Playground or ``rclone authorize``).

The OAuth Client ID/Secret live in the database (secret encrypted at rest), so
no docker-compose / environment changes are needed. Django settings are used
only as an optional fallback if the fields are left blank.
"""
import json

from django import forms
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.admin.panels import (
    FieldPanel,
    MultiFieldPanel,
    ObjectList,
    TabbedInterface,
)
from wagtail.contrib.settings.models import BaseSiteSetting
from wagtail.contrib.settings.registry import register_setting

from climweb.base.backups.crypto import decrypt_text, encrypt_text
from climweb.base.backups.panels import BackupConnectionPanel


class BackupStatus(models.TextChoices):
    NEVER = "never", _("Never run")
    SUCCESS = "success", _("Success")
    FAILED = "failed", _("Failed")


WEEKDAY_CHOICES = (
    (0, _("Monday")),
    (1, _("Tuesday")),
    (2, _("Wednesday")),
    (3, _("Thursday")),
    (4, _("Friday")),
    (5, _("Saturday")),
    (6, _("Sunday")),
)


def extract_refresh_token(pasted: str):
    """Accept either a raw refresh-token string or a token JSON blob (rclone /
    OAuth Playground style) and return the refresh token."""
    pasted = (pasted or "").strip()
    if not pasted:
        return None
    if pasted.startswith("{"):
        try:
            data = json.loads(pasted)
            return data.get("refresh_token") or None
        except (ValueError, TypeError):
            return None
    return pasted


class BackupSettingsForm(WagtailAdminModelForm):
    """Makes the client secret and pasted token write-only: they are never
    rendered back into the form, and are encrypted / consumed on save."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Snapshot the stored (encrypted) secret before the ModelForm can
        # overwrite it with the blank input value on save.
        self._stored_client_secret = getattr(self.instance, "oauth_client_secret", "")

        if "oauth_client_secret" in self.fields:
            f = self.fields["oauth_client_secret"]
            f.required = False
            f.initial = ""
            f.widget = forms.PasswordInput(render_value=False)
            f.help_text = _("Paste to set or change. Leave blank to keep the current secret.")

        if "paste_refresh_token" in self.fields:
            f = self.fields["paste_refresh_token"]
            f.required = False
            f.initial = ""
            f.widget = forms.Textarea(attrs={"rows": 3})
            f.help_text = _(
                "Optional: paste a refresh token (or token JSON) generated elsewhere "
                "to connect without the button. Cleared after saving."
            )

        # SFTP secrets — same write-only treatment.
        self._stored_sftp_password = getattr(self.instance, "sftp_password", "")
        if "sftp_password" in self.fields:
            f = self.fields["sftp_password"]
            f.required = False
            f.initial = ""
            f.widget = forms.PasswordInput(render_value=False)
            f.help_text = _("Paste to set or change. Leave blank to keep the current password.")

        if "paste_private_key" in self.fields:
            f = self.fields["paste_private_key"]
            f.required = False
            f.initial = ""
            f.widget = forms.Textarea(attrs={"rows": 4})
            f.help_text = _(
                "Optional: paste an existing OpenSSH private key instead of generating "
                "one. Cleared after saving."
            )

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Client secret: encrypt a newly entered value, otherwise keep the stored one.
        submitted_secret = self.cleaned_data.get("oauth_client_secret", "")
        if submitted_secret:
            instance.oauth_client_secret = encrypt_text(submitted_secret)
        else:
            instance.oauth_client_secret = self._stored_client_secret

        # Pasted token: consume it into the encrypted refresh-token store, never persist.
        pasted = self.cleaned_data.get("paste_refresh_token", "")
        token = extract_refresh_token(pasted)
        if token:
            instance.set_refresh_token(token, email=instance.google_account_email or "")
        instance.paste_refresh_token = ""

        # SFTP password: encrypt new value, otherwise keep the stored one.
        submitted_pw = self.cleaned_data.get("sftp_password", "")
        if submitted_pw:
            instance.sftp_password = encrypt_text(submitted_pw)
        else:
            instance.sftp_password = self._stored_sftp_password

        # Pasted SSH private key: store encrypted + derive the public line, never persist raw.
        pasted_key = (self.cleaned_data.get("paste_private_key") or "").strip()
        if pasted_key:
            from climweb.base.backups.sftp import public_line_from_private
            instance.set_sftp_private_key(pasted_key, public_line_from_private(pasted_key))
        instance.paste_private_key = ""

        if commit:
            instance.save()
        return instance


@register_setting(icon="download")
class BackupSettings(BaseSiteSetting):
    base_form_class = BackupSettingsForm

    PROVIDER_CHOICES = (
        ("gdrive", _("Google Drive")),
        ("sftp", _("Remote server (SFTP)")),
    )

    SFTP_AUTH_CHOICES = (
        ("key", _("SSH key (recommended)")),
        ("password", _("Password")),
    )

    enabled = models.BooleanField(
        default=False,
        verbose_name=_("Enable cloud backups"),
        help_text=_(
            "When enabled, the daily backup will be uploaded to the connected "
            "cloud account. You must connect an account below first."
        ),
    )

    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        default="gdrive",
        verbose_name=_("Provider"),
    )

    remote_folder = models.CharField(
        max_length=255,
        default="ClimWeb Backups",
        verbose_name=_("Remote folder"),
        help_text=_("Top-level folder created in the drive to hold backups."),
    )

    db_retention_days = models.PositiveIntegerField(
        default=10,
        verbose_name=_("Database copies to keep"),
        help_text=_("Number of daily database snapshots to retain on the remote."),
    )

    media_retention_days = models.PositiveIntegerField(
        default=3,
        verbose_name=_("Media copies to keep"),
        help_text=_("Number of weekly media snapshots to retain on the remote."),
    )

    media_upload_weekday = models.PositiveIntegerField(
        default=0,
        choices=WEEKDAY_CHOICES,
        verbose_name=_("Media upload day"),
        help_text=_("Day of the week the (larger) media archive is uploaded."),
    )

    notify_email = models.EmailField(
        blank=True,
        verbose_name=_("Failure notification email"),
        help_text=_("Where to email if a backup fails. Leave blank to use the "
                    "server's admin addresses."),
    )

    # --- OAuth application credentials (entered here, not in env) ---
    oauth_client_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("OAuth Client ID"),
        help_text=_(
            "From your Google Cloud OAuth 'Web application' client. This value is "
            "public. Required for the Connect button."
        ),
    )
    # Stored ENCRYPTED at rest; edited via the write-only form field above.
    oauth_client_secret = models.CharField(
        max_length=512,
        blank=True,
        verbose_name=_("OAuth Client Secret"),
    )
    # Transient input only — never persisted with a value (see the form's save()).
    paste_refresh_token = models.CharField(
        max_length=4096,
        blank=True,
        verbose_name=_("Paste a token (fallback)"),
    )

    # --- Remote server (SFTP) settings ---
    sftp_host = models.CharField(
        max_length=255, blank=True, verbose_name=_("Host"),
        help_text=_("Destination server hostname or IP."))
    sftp_port = models.PositiveIntegerField(default=22, verbose_name=_("Port"))
    sftp_username = models.CharField(max_length=255, blank=True, verbose_name=_("Username"))
    sftp_remote_path = models.CharField(
        max_length=512, default="climweb-backups", verbose_name=_("Remote directory"),
        help_text=_("Directory on the destination server (relative to the login "
                    "home, or an absolute path). Created if missing."))
    sftp_auth_method = models.CharField(
        max_length=10, choices=SFTP_AUTH_CHOICES, default="key",
        verbose_name=_("Authentication"))
    # Stored ENCRYPTED at rest; edited via write-only form fields.
    sftp_password = models.CharField(max_length=512, blank=True, verbose_name=_("Password"))
    sftp_private_key = models.TextField(blank=True, editable=False)
    # Transient input only — never persisted with a value (see the form's save()).
    paste_private_key = models.TextField(blank=True, verbose_name=_("Paste an SSH private key (fallback)"))
    # Public key to add to the destination's authorized_keys (display only).
    sftp_public_key = models.TextField(blank=True, editable=False)
    # Pinned server host key (trust-on-first-use), display/verify only.
    sftp_host_key = models.TextField(blank=True, editable=False)

    # --- connection state (managed by the OAuth flow / paste, not edited directly) ---
    google_account_email = models.CharField(
        max_length=254,
        blank=True,
        editable=False,
        verbose_name=_("Connected account"),
    )
    encrypted_token = models.TextField(
        blank=True,
        editable=False,
        help_text=_("Encrypted OAuth refresh token. Never edit by hand."),
    )

    # --- last-run status, surfaced in the admin ---
    last_backup_at = models.DateTimeField(null=True, blank=True, editable=False)
    last_backup_status = models.CharField(
        max_length=20,
        choices=BackupStatus.choices,
        default=BackupStatus.NEVER,
        editable=False,
    )
    last_backup_message = models.TextField(blank=True, editable=False)

    class Meta:
        verbose_name = _("Backup Settings")

    # ------------------------------------------------------------------ #
    # Credential helpers.
    # ------------------------------------------------------------------ #
    def get_oauth_client_secret(self):
        if not self.oauth_client_secret:
            return ""
        try:
            return decrypt_text(self.oauth_client_secret)
        except Exception:
            return ""

    def resolved_client_credentials(self):
        """(client_id, client_secret) from this page, falling back to settings."""
        cid = self.oauth_client_id or getattr(settings, "GOOGLE_DRIVE_OAUTH_CLIENT_ID", "")
        secret = self.get_oauth_client_secret() or getattr(
            settings, "GOOGLE_DRIVE_OAUTH_CLIENT_SECRET", "")
        return cid, secret

    def is_oauth_app_configured(self):
        cid, secret = self.resolved_client_credentials()
        return bool(cid and secret)

    # ------------------------------------------------------------------ #
    # Refresh-token helpers — encrypted at rest.
    # ------------------------------------------------------------------ #
    @property
    def is_connected(self):
        return bool(self.encrypted_token)

    def get_refresh_token(self):
        if not self.encrypted_token:
            return None
        return decrypt_text(self.encrypted_token)

    def set_refresh_token(self, refresh_token, email=""):
        self.encrypted_token = encrypt_text(refresh_token) if refresh_token else ""
        self.google_account_email = email or self.google_account_email

    def clear_connection(self):
        self.encrypted_token = ""
        self.google_account_email = ""

    # ------------------------------------------------------------------ #
    # SFTP helpers.
    # ------------------------------------------------------------------ #
    def get_sftp_password(self):
        if not self.sftp_password:
            return ""
        try:
            return decrypt_text(self.sftp_password)
        except Exception:
            return ""

    def get_sftp_private_key(self):
        if not self.sftp_private_key:
            return ""
        try:
            return decrypt_text(self.sftp_private_key)
        except Exception:
            return ""

    def set_sftp_private_key(self, pem, public_line=""):
        self.sftp_private_key = encrypt_text(pem) if pem else ""
        self.sftp_public_key = public_line or self.sftp_public_key
        # A new key invalidates any pinned host key context only if host changes;
        # leave host key pinning as-is.

    def clear_sftp_key(self):
        self.sftp_private_key = ""
        self.sftp_public_key = ""

    def is_sftp_configured(self):
        if not (self.sftp_host and self.sftp_username and self.sftp_remote_path):
            return False
        if self.sftp_auth_method == "password":
            return bool(self.sftp_password)
        return bool(self.sftp_private_key)

    # ------------------------------------------------------------------ #
    # Provider-agnostic readiness (used by the task and the admin panel).
    # ------------------------------------------------------------------ #
    def provider_ready(self):
        if self.provider == "sftp":
            return self.is_sftp_configured()
        return self.is_connected  # gdrive

    edit_handler = TabbedInterface([
        ObjectList([
            BackupConnectionPanel(),
            FieldPanel("provider"),
            # These two groups are shown/hidden by JS based on the provider
            # dropdown (see backup_connection_panel.html). The classname is the
            # JS hook.
            MultiFieldPanel([
                FieldPanel("oauth_client_id"),
                FieldPanel("oauth_client_secret"),
                FieldPanel("paste_refresh_token"),
            ], heading=_("Google Drive credentials"), classname="backup-provider-gdrive"),
            MultiFieldPanel([
                FieldPanel("sftp_host"),
                FieldPanel("sftp_port"),
                FieldPanel("sftp_username"),
                FieldPanel("sftp_remote_path"),
                FieldPanel("sftp_auth_method"),
                FieldPanel("sftp_password"),
                FieldPanel("paste_private_key"),
            ], heading=_("Remote server (SFTP)"), classname="backup-provider-sftp"),
            FieldPanel("enabled"),
        ], heading=_("Connection")),
        ObjectList([
            FieldPanel("remote_folder"),
            FieldPanel("db_retention_days"),
            FieldPanel("media_retention_days"),
            FieldPanel("media_upload_weekday"),
            FieldPanel("notify_email"),
        ], heading=_("Options")),
    ])
