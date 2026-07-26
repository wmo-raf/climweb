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
import os

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseForbidden, StreamingHttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from loguru import logger
from wagtail.admin import messages

from climweb.base.backups import google_drive as gd
from climweb.base.models.backup_settings import BackupSettings

SESSION_STATE_KEY = "backup_gdrive_oauth_state"


@login_required
def backup_help(request):
    """Render the Google Drive backup setup guide inside the CMS admin."""
    return render(request, "admin/backup_help.html")


def _provider_module(backup_settings):
    if backup_settings.provider == "sftp":
        from climweb.base.backups import sftp as mod
    else:
        mod = gd
    return mod


def _human_size(num):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(num) < 1024 or unit == "TB":
            return f"{num:.0f} {unit}" if unit == "B" else f"{num:.1f} {unit}"
        num /= 1024


@login_required
def backup_browser(request):
    """Read-only list of the backups already stored on the configured provider,
    with per-file download links. Superuser only — full DB dumps are sensitive."""
    if not request.user.is_superuser:
        return HttpResponseForbidden("Superuser access required to browse backups.")

    backup_settings = BackupSettings.for_request(request)
    context = {
        "provider": backup_settings.get_provider_display(),
        "ready": backup_settings.provider_ready(),
        "db_files": [],
        "media_files": [],
        "error": None,
    }
    if backup_settings.provider_ready():
        try:
            listing = _provider_module(backup_settings).list_backups(backup_settings)
            for kind in ("db", "media"):
                rows = [{
                    "name": f["name"],
                    "size_h": _human_size(f["size"]),
                    "modified": f["modified"],
                    "download_url": reverse("backup-download") + f"?kind={kind}&ref={f['ref']}",
                } for f in listing.get(kind, [])]
                context["db_files" if kind == "db" else "media_files"] = rows
        except Exception as exc:
            logger.exception("[BACKUP] Could not list backups")
            context["error"] = str(exc)

    return render(request, "admin/backup_browser.html", context)


@login_required
def backup_download(request):
    """Stream a single backup file from the provider as a download."""
    if not request.user.is_superuser:
        return HttpResponseForbidden("Superuser access required to download backups.")

    backup_settings = BackupSettings.for_request(request)
    ref = request.GET.get("ref", "")
    if not ref or not backup_settings.provider_ready():
        raise Http404("Backup not found.")

    module = _provider_module(backup_settings)
    filename = os.path.basename(ref.replace("\\", "/")) or "backup"
    try:
        stream = module.download_stream(backup_settings, ref)
        # Pull the first chunk eagerly so connection/permission errors surface here
        # as a clean 404 rather than mid-stream.
        first = next(stream, b"")

        def _iter():
            if first:
                yield first
            yield from stream

        response = StreamingHttpResponse(_iter(), content_type="application/octet-stream")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    except Exception as exc:
        logger.exception("[BACKUP] Backup download failed")
        raise Http404(str(exc))


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

        if gd.DRIVE_SCOPE not in gd.granted_scopes(flow):
            messages.error(
                request,
                "Google Drive access was not granted. Please click Connect again "
                "and make sure the Google Drive permission checkbox is ticked on "
                "the consent screen before continuing.",
            )
            return redirect(settings_url)

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
def sftp_generate_key(request):
    """Generate an Ed25519 keypair; store the private half encrypted and show the
    public half to add to the destination server."""
    from climweb.base.backups import sftp as sftp_mod

    backup_settings = BackupSettings.for_request(request)
    try:
        private_pem, public_line = sftp_mod.generate_keypair()
        backup_settings.set_sftp_private_key(private_pem, public_line)
        backup_settings.sftp_auth_method = "key"
        backup_settings.save()
        messages.success(
            request,
            "SSH key generated. Copy the public key shown below into the destination "
            "server's ~/.ssh/authorized_keys, then run a backup to test.",
        )
    except Exception as exc:
        logger.exception("[BACKUP] SSH key generation failed")
        messages.error(request, f"Could not generate SSH key: {exc}")
    return redirect(_settings_url())


@login_required
def sftp_clear_key(request):
    backup_settings = BackupSettings.for_request(request)
    backup_settings.clear_sftp_key()
    backup_settings.save()
    messages.success(request, "SSH key removed.")
    return redirect(_settings_url())


@login_required
def sftp_clear_hostkey(request):
    backup_settings = BackupSettings.for_request(request)
    backup_settings.sftp_host_key = ""
    backup_settings.save()
    messages.success(
        request,
        "Pinned host key cleared. The destination's host key will be re-pinned on "
        "the next connection.",
    )
    return redirect(_settings_url())


@login_required
def run_backup_now(request):
    """Trigger the full backup + cloud upload immediately, in the background."""
    backup_settings = BackupSettings.for_request(request)
    if not (backup_settings.enabled and backup_settings.provider_ready()):
        messages.error(
            request,
            "Configure and enable a backup destination before running a backup.",
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
