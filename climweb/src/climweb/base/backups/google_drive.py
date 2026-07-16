"""
Google Drive OAuth + upload helpers.

A single Google Cloud OAuth *application* (client id/secret configured via
environment variables) serves every ClimWeb deployment. Each site connects its
own Google account through the browser flow and we store only that account's
refresh token (encrypted). Uploads use the ``drive.file`` scope, so ClimWeb can
only see files it created — never the rest of the user's Drive.
"""
import os
from datetime import datetime

from django.conf import settings
from django.urls import reverse
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from loguru import logger

# drive.file: per-file access to files created by this app only.
# openid/email: so we can display which account was connected.
SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
]

TOKEN_URI = "https://oauth2.googleapis.com/token"
AUTH_URI = "https://accounts.google.com/o/oauth2/auth"


def get_redirect_uri():
    base = getattr(settings, "WAGTAILADMIN_BASE_URL", "").rstrip("/")
    return base + reverse("backup-google-callback")


def _client_config(client_id, client_secret):
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": AUTH_URI,
            "token_uri": TOKEN_URI,
            "redirect_uris": [get_redirect_uri()],
        }
    }


def build_flow(client_id, client_secret, state=None):
    return Flow.from_client_config(
        _client_config(client_id, client_secret),
        scopes=SCOPES,
        redirect_uri=get_redirect_uri(),
        state=state,
    )


def credentials_from_refresh_token(refresh_token, client_id, client_secret):
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=TOKEN_URI,
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return creds


def _drive_service(refresh_token, client_id, client_secret):
    creds = credentials_from_refresh_token(refresh_token, client_id, client_secret)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _get_or_create_folder(service, name, parent_id=None):
    query = (
        "mimeType='application/vnd.google-apps.folder' "
        f"and name='{name}' and trashed=false"
    )
    if parent_id:
        query += f" and '{parent_id}' in parents"
    resp = service.files().list(q=query, fields="files(id)", spaces="drive").execute()
    files = resp.get("files", [])
    if files:
        return files[0]["id"]

    metadata = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        metadata["parents"] = [parent_id]
    folder = service.files().create(body=metadata, fields="id").execute()
    return folder["id"]


def _upload_file(service, local_path, remote_name, folder_id):
    media = MediaFileUpload(local_path, resumable=True)
    metadata = {"name": remote_name, "parents": [folder_id]}
    service.files().create(body=metadata, media_body=media, fields="id").execute()


def _prune(service, folder_id, name_prefix, keep):
    """Keep only the ``keep`` most recent files whose name starts with prefix."""
    resp = service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="files(id, name, createdTime)",
        orderBy="createdTime desc",
        spaces="drive",
    ).execute()
    matching = [f for f in resp.get("files", []) if f["name"].startswith(name_prefix)]
    for stale in matching[keep:]:
        service.files().delete(fileId=stale["id"]).execute()
        logger.info(f"[BACKUP] Pruned old remote backup {stale['name']}")


def _newest_file(backup_dir, suffix):
    candidates = [
        os.path.join(backup_dir, f)
        for f in os.listdir(backup_dir)
        if f.endswith(suffix)
    ]
    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)


def fetch_account_email(credentials):
    try:
        service = build("oauth2", "v2", credentials=credentials, cache_discovery=False)
        return service.userinfo().get().execute().get("email", "")
    except Exception as exc:  # pragma: no cover - best-effort display only
        logger.warning(f"[BACKUP] Could not fetch account email: {exc}")
        return ""


def upload_backups(backup_settings, backup_dir, run_media=None):
    """
    Upload the latest DB dump (always) and media archive (on the configured
    weekday) to the connected Google Drive account, then prune old copies.

    Returns a human-readable status string. Raises on hard failures so the
    caller can record ``failed`` status.
    """
    refresh_token = backup_settings.get_refresh_token()
    if not refresh_token:
        raise RuntimeError("No connected Google account.")

    client_id, client_secret = backup_settings.resolved_client_credentials()
    if not (client_id and client_secret):
        raise RuntimeError("Google OAuth Client ID/Secret are not configured.")

    site_label = _site_label(backup_settings)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    service = _drive_service(refresh_token, client_id, client_secret)

    root_id = _get_or_create_folder(service, backup_settings.remote_folder)
    db_folder_id = _get_or_create_folder(service, "db", root_id)

    messages = []

    db_file = _newest_file(backup_dir, ".psql.bin")
    if not db_file:
        db_file = _newest_file(backup_dir, ".dump") or _newest_file(backup_dir, ".sql")
    if db_file:
        remote_name = f"{site_label}-db-{today}.psql.bin"
        _upload_file(service, db_file, remote_name, db_folder_id)
        _prune(service, db_folder_id, f"{site_label}-db-", backup_settings.db_retention_days)
        messages.append(f"db: {remote_name}")
    else:
        messages.append("db: no dump found")

    if run_media is None:
        run_media = datetime.utcnow().weekday() == backup_settings.media_upload_weekday

    if run_media:
        media_file = _newest_file(backup_dir, ".tar")
        if media_file:
            media_folder_id = _get_or_create_folder(service, "media", root_id)
            remote_name = f"{site_label}-media-{today}.tar"
            _upload_file(service, media_file, remote_name, media_folder_id)
            _prune(service, media_folder_id, f"{site_label}-media-",
                   backup_settings.media_retention_days)
            messages.append(f"media: {remote_name}")
        else:
            messages.append("media: no archive found")

    return "; ".join(messages)


def _site_label(backup_settings):
    site = getattr(backup_settings, "site", None)
    raw = (getattr(site, "site_name", None) or getattr(site, "hostname", None)
           or "climweb")
    return "".join(c if c.isalnum() else "-" for c in raw.lower()).strip("-") or "climweb"
