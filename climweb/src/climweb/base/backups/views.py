"""
Admin views implementing the Google Drive "Connect" button OAuth flow.

Flow:
  1. ``google_drive_connect``  -> redirect the admin user to Google's consent
     screen (offline access so we receive a refresh token).
  2. ``google_drive_callback`` -> Google redirects back with a code; we exchange
     it, store the encrypted refresh token on this site's BackupSettings, and
     record which account was connected.
  3. ``google_drive_disconnect`` -> forget the stored token.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from loguru import logger
from wagtail.admin import messages

from climweb.base.backups import google_drive as gd
from climweb.base.models.backup_settings import BackupSettings

SESSION_STATE_KEY = "backup_gdrive_oauth_state"


def _settings_url():
    # Wagtail settings edit page for BackupSettings (site-scoped variant resolves
    # to the current site automatically).
    return reverse(
        "wagtailsettings:edit",
        args=["base", "backupsettings"],
    )


@login_required
def google_drive_connect(request):
    backup_settings = BackupSettings.for_request(request)
    if not backup_settings.is_oauth_app_configured():
        messages.error(
            request,
            "Enter your Google OAuth Client ID and Secret on the Backup settings "
            "page (and save) before using the Connect button.",
        )
        return redirect(_settings_url())

    client_id, client_secret = backup_settings.resolved_client_credentials()
    flow = gd.build_flow(client_id, client_secret)
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    request.session[SESSION_STATE_KEY] = state
    return redirect(auth_url)


@login_required
def google_drive_callback(request):
    settings_url = _settings_url()

    if request.GET.get("error"):
        messages.error(request, f"Google authorisation was cancelled: {request.GET['error']}")
        return redirect(settings_url)

    state = request.session.get(SESSION_STATE_KEY)
    backup_settings = BackupSettings.for_request(request)
    try:
        client_id, client_secret = backup_settings.resolved_client_credentials()
        flow = gd.build_flow(client_id, client_secret, state=state)

        # Behind a TLS-terminating proxy (nginx) Django sees the request as http,
        # so build_absolute_uri() yields an http:// URL and oauthlib rejects it
        # with "(insecure_transport) OAuth 2 MUST utilize https". The public
        # callback is always https, so force the scheme before handing it to
        # oauthlib.
        authorization_response = request.build_absolute_uri()
        if authorization_response.startswith("http://"):
            authorization_response = "https://" + authorization_response[len("http://"):]

        flow.fetch_token(authorization_response=authorization_response)
        credentials = flow.credentials

        if not credentials.refresh_token:
            messages.error(
                request,
                "Google did not return a refresh token. Remove ClimWeb from your "
                "Google account permissions and try connecting again.",
            )
            return redirect(settings_url)

        email = gd.fetch_account_email(credentials)

        backup_settings.set_refresh_token(credentials.refresh_token, email=email)
        backup_settings.save()

        messages.success(request, f"Google Drive connected as {email or 'your account'}.")
    except Exception as exc:
        logger.exception("[BACKUP] Google Drive OAuth callback failed")
        messages.error(request, f"Could not connect Google Drive: {exc}")
    finally:
        request.session.pop(SESSION_STATE_KEY, None)

    return redirect(settings_url)


@login_required
def google_drive_disconnect(request):
    backup_settings = BackupSettings.for_request(request)
    backup_settings.clear_connection()
    backup_settings.enabled = False
    backup_settings.save()
    messages.success(request, "Google Drive disconnected.")
    return redirect(_settings_url())


@login_required
def run_backup_now(request):
    """Trigger the full backup + cloud upload immediately, in the background."""
    backup_settings = BackupSettings.for_request(request)
    if not (backup_settings.enabled and backup_settings.is_connected):
        messages.error(
            request,
            "Connect a Google account and enable cloud backups before running a backup.",
        )
        return redirect(_settings_url())

    # Imported lazily to avoid importing Celery task wiring at module load.
    from climweb.base.tasks import run_backup

    try:
        run_backup.delay()
        messages.success(
            request,
            "Backup started. It runs in the background — refresh this page in a "
            "minute to see the result under 'Last upload'.",
        )
    except Exception as exc:
        logger.exception("[BACKUP] Could not enqueue manual backup")
        messages.error(request, f"Could not start backup: {exc}")

    return redirect(_settings_url())
