"""
Models backing the automated product sync.

A national met service runs `climweb-sync` on the server that generates its
bulletins. Rather than asking them to transcribe settings out of this admin by
hand — which is how a variable_name ends up misspelled and a product silently
stops publishing — an editor generates a short setup code here, and their
server exchanges it for a scoped API token plus the correct settings.

Two objects support that:

* ProductSyncSetupCode — short-lived, single-use, human-readable. Safe to read
  aloud over the phone or paste into an email, because on its own it grants
  nothing beyond the settings for one product, and only once.
* ProductSyncCredential — the long-lived token the source server then uses to
  upload. Stored hashed, scoped to a single product, revocable from the admin.
"""

import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Deliberately excludes characters people confuse when reading a code off a
# screen and typing it on another machine: O/0, I/1/l, S/5, B/8.
_CODE_ALPHABET = "ACDEFGHJKMNPQRTUVWXYZ2346789"
_CODE_GROUPS = 3
_CODE_GROUP_LEN = 4

SETUP_CODE_TTL = timedelta(hours=48)


def generate_setup_code():
    """Return a code like 'K7FA-2C91-DTX4'."""
    groups = [
        "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_GROUP_LEN))
        for _ in range(_CODE_GROUPS)
    ]
    return "-".join(groups)


def normalise_setup_code(raw):
    """
    Accept what a person actually types: lowercase, missing dashes, stray
    spaces. Rejecting those would generate support tickets, not security.
    """
    if not raw:
        return ""
    cleaned = "".join(ch for ch in str(raw).upper() if ch in _CODE_ALPHABET)
    if len(cleaned) != _CODE_GROUPS * _CODE_GROUP_LEN:
        return ""
    return "-".join(
        cleaned[i:i + _CODE_GROUP_LEN]
        for i in range(0, len(cleaned), _CODE_GROUP_LEN)
    )


def hash_token(token):
    """Tokens are high-entropy, so a plain SHA-256 is appropriate here."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class ProductSyncSetupCode(models.Model):
    """A one-time code that a source server exchanges for a sync credential."""

    product = models.ForeignKey(
        "base.Product",
        on_delete=models.CASCADE,
        related_name="sync_setup_codes",
        verbose_name=_("Product"),
    )
    code = models.CharField(max_length=20, unique=True, verbose_name=_("Setup Code"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("Created By"),
    )
    expires_at = models.DateTimeField(verbose_name=_("Expires At"))
    used_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Used At"))
    used_by_host = models.CharField(
        max_length=255, blank=True, verbose_name=_("Used By Host")
    )

    class Meta:
        verbose_name = _("Product Sync Setup Code")
        verbose_name_plural = _("Product Sync Setup Codes")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} ({self.product})"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_setup_code()
        if not self.expires_at:
            self.expires_at = timezone.now() + SETUP_CODE_TTL
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def is_used(self):
        return self.used_at is not None

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired

    @property
    def status(self):
        if self.is_used:
            return _("Used")
        if self.is_expired:
            return _("Expired")
        return _("Waiting")

    @classmethod
    def issue(cls, product, user=None):
        """
        Create a fresh code, retiring any outstanding ones for this product.

        Only one code should be live at a time: if an editor clicks the button
        twice, the instructions they already sent should stop working, so there
        is never ambiguity about which code is the real one.
        """
        cls.objects.filter(product=product, used_at__isnull=True).update(
            expires_at=timezone.now()
        )
        return cls.objects.create(
            product=product,
            created_by=user if (user and user.is_authenticated) else None,
        )

    @classmethod
    def claim(cls, raw_code):
        """
        Look up a valid, unused code. Returns None rather than raising, so the
        API can answer every failure identically and not leak which codes exist.
        """
        code = normalise_setup_code(raw_code)
        if not code:
            return None
        obj = cls.objects.filter(code=code).select_related("product").first()
        if obj is None or not obj.is_valid:
            return None
        return obj


class ProductSyncCredential(models.Model):
    """A revocable, product-scoped token used by one source server."""

    product = models.ForeignKey(
        "base.Product",
        on_delete=models.CASCADE,
        related_name="sync_credentials",
        verbose_name=_("Product"),
    )
    label = models.CharField(
        max_length=255,
        verbose_name=_("Server"),
        help_text=_("Hostname reported by the server that set this up."),
    )
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    token_prefix = models.CharField(
        max_length=12,
        verbose_name=_("Token"),
        help_text=_("First characters of the token, to tell credentials apart."),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    last_used_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Last Used")
    )
    last_used_ip = models.GenericIPAddressField(
        null=True, blank=True, verbose_name=_("Last Used From")
    )
    upload_count = models.PositiveIntegerField(
        default=0, verbose_name=_("Files Received")
    )
    revoked_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Revoked At")
    )

    # Traffic only ever flows from the source server to here, so an editor
    # cannot make that server send on demand. Instead the request is left as a
    # flag: the client already contacts the API on every run, and picks it up
    # then. The delay is one of the source server's cron intervals.
    full_sync_requested_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Full Sync Requested At")
    )
    full_sync_completed_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Full Sync Completed At")
    )

    class Meta:
        verbose_name = _("Product Sync Credential")
        verbose_name_plural = _("Product Sync Credentials")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.label} -> {self.product}"

    @property
    def is_active(self):
        return self.revoked_at is None

    @classmethod
    def issue(cls, product, label):
        """
        Create a credential and return (instance, plaintext_token).

        The plaintext is returned exactly once and never stored; if it is lost,
        the operator generates a new setup code rather than recovering the old
        token.
        """
        token = secrets.token_urlsafe(32)
        credential = cls.objects.create(
            product=product,
            label=(label or "unknown")[:255],
            token_hash=hash_token(token),
            token_prefix=token[:8],
        )
        return credential, token

    @classmethod
    def authenticate(cls, token):
        """Return the active credential for this token, or None."""
        if not token:
            return None
        return (
            cls.objects.filter(token_hash=hash_token(token), revoked_at__isnull=True)
            .select_related("product")
            .first()
        )

    def touch(self, ip=None, uploaded=False):
        fields = ["last_used_at"]
        self.last_used_at = timezone.now()
        if ip:
            self.last_used_ip = ip
            fields.append("last_used_ip")
        if uploaded:
            self.upload_count = models.F("upload_count") + 1
            fields.append("upload_count")
        self.save(update_fields=fields)

    def revoke(self):
        if self.is_active:
            self.revoked_at = timezone.now()
            self.save(update_fields=["revoked_at"])

    # -- full sync request -----------------------------------------------------
    @property
    def full_sync_pending(self):
        return self.full_sync_requested_at is not None

    def request_full_sync(self):
        """Ask the source server to re-offer every file on its next run."""
        self.full_sync_requested_at = timezone.now()
        self.save(update_fields=["full_sync_requested_at"])

    def complete_full_sync(self):
        """
        Called by the client once it has finished a requested full sync.

        The flag is cleared here rather than when the client first reads it, so
        a run that dies halfway leaves the request outstanding and the next run
        picks it up again.
        """
        self.full_sync_completed_at = timezone.now()
        self.full_sync_requested_at = None
        self.save(
            update_fields=["full_sync_completed_at", "full_sync_requested_at"]
        )

    def cancel_full_sync(self):
        if self.full_sync_pending:
            self.full_sync_requested_at = None
            self.save(update_fields=["full_sync_requested_at"])
