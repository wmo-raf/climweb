"""Email notifications when a backup fails."""
from django.conf import settings
from loguru import logger

from climweb.base.mail import send_mail


def _recipients(backup_settings):
    """Per-site notify_email if set, else the Django ADMINS list."""
    if getattr(backup_settings, "notify_email", ""):
        return [backup_settings.notify_email]
    return [addr for _name, addr in getattr(settings, "ADMINS", []) if addr]


def _site_name(backup_settings):
    site = getattr(backup_settings, "site", None)
    return (getattr(site, "site_name", None)
            or getattr(site, "hostname", None) or "ClimWeb")


def notify_failure(backup_settings, message):
    """Best-effort failure email. Never raises."""
    recipients = _recipients(backup_settings)
    if not recipients:
        logger.warning("[BACKUP] Backup failed but no notification recipients are "
                       "configured (set a notify email or Django ADMINS).")
        return
    site_name = _site_name(backup_settings)
    subject = f"Backup failed for {site_name}"
    body = (
        f"A ClimWeb backup failed for {site_name}.\n\n"
        f"Details:\n{message}\n\n"
        f"Open Settings → Backup in the CMS admin to see the status and retry."
    )
    try:
        send_mail(subject, body, recipients, fail_silently=True)
        logger.info(f"[BACKUP] Sent failure notification to {recipients}")
    except Exception:
        logger.exception("[BACKUP] Could not send failure notification email")
