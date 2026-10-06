"""Email every superuser when a new user account is created.

An account nobody expected is one of the first signs that a site has been
compromised, so this listens on the model rather than on a particular admin
form: accounts made in the Wagtail admin, the Django admin, `createsuperuser`,
a sign-up flow or a shell all trigger it.

Best-effort, like the backup notifications: a missing or broken mail setup is
logged and never stops the account from being created.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from loguru import logger

from climweb.base.mail import send_mail


def _recipients(new_user):
    return list(
        get_user_model()
        .objects.filter(is_superuser=True, is_active=True)
        .exclude(pk=new_user.pk)
        .exclude(email="")
        .values_list("email", flat=True)
    )


def _account_type(user):
    if user.is_superuser:
        return "Superuser (full access to everything)"
    if user.is_staff:
        return "Staff"
    return "Standard user"


def _edit_url(user):
    path = reverse("wagtailusers_users:edit", args=[user.pk])
    base_url = (getattr(settings, "WAGTAILADMIN_BASE_URL", "") or "").rstrip("/")
    return f"{base_url}{path}" if base_url else path


def notify_superusers(user_pk):
    """Send the notification. Never raises."""
    try:
        user = get_user_model().objects.get(pk=user_pk)
    except get_user_model().DoesNotExist:
        return

    recipients = _recipients(user)
    if not recipients:
        logger.warning(
            f"[USERS] New user '{user.get_username()}' created but no other active "
            f"superuser has an email address to notify."
        )
        return

    site_name = getattr(settings, "WAGTAIL_SITE_NAME", "ClimWeb")
    kind = "superuser" if user.is_superuser else "user"
    subject = f"New {kind} account on {site_name}: {user.get_username()}"
    body = (
        f"A new {kind} account has been created on {site_name}.\n\n"
        f"Username:     {user.get_username()}\n"
        f"Name:         {user.get_full_name() or '-'}\n"
        f"Email:        {user.email or '-'}\n"
        f"Account type: {_account_type(user)}\n"
        f"Active:       {'Yes' if user.is_active else 'No'}\n"
        f"Created:      {user.date_joined:%Y-%m-%d %H:%M %Z}\n\n"
        f"Review the account and its groups here:\n{_edit_url(user)}\n\n"
        f"If you don't recognise this account, deactivate it straight away and "
        f"check who else has admin access."
    )
    try:
        send_mail(subject, body, recipients, fail_silently=True)
        logger.info(f"[USERS] Notified {len(recipients)} superuser(s) of new user {user.pk}")
    except Exception:
        logger.exception("[USERS] Could not send new-user notification email")


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def notify_superusers_of_new_user(sender, instance, created, raw=False, **kwargs):
    # `raw` is set while loading fixtures, e.g. restoring a backup; those
    # accounts aren't new.
    if not created or raw:
        return
    # After commit, so a rolled-back creation doesn't raise a false alarm and
    # the email reflects the account as saved.
    user_pk = instance.pk
    transaction.on_commit(lambda: notify_superusers(user_pk))
