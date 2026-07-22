"""
Backup to another server over SFTP/SSH — the in-CMS replacement for the old
rsync-over-SSH setup.

Auth uses an SSH key (recommended) or a password, both stored encrypted in the
DB. Keys can be generated in the CMS ("Generate SSH key"): we keep the private
half encrypted and show the public half for the admin to add to the destination
server's ``~/.ssh/authorized_keys``. The destination's host key is pinned on
first connect (trust-on-first-use) so later runs can detect a changed server.
"""
import io
import socket
import stat
from datetime import datetime

import paramiko
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from loguru import logger

from climweb.base.backups.google_drive import _newest_file, _site_label


class HostKeyChangedError(Exception):
    """Raised when the destination's SSH host key doesn't match the pinned one."""


# --------------------------------------------------------------------------- #
# Key handling
# --------------------------------------------------------------------------- #
def generate_keypair():
    """Return (private_openssh_pem, public_openssh_line) for a new Ed25519 key."""
    key = Ed25519PrivateKey.generate()
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_line = key.public_key().public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    ).decode("utf-8")
    return private_pem, public_line + " climweb-backup"


def _load_private_key(pem):
    """Load an OpenSSH/PEM private key string, trying common key types."""
    last_err = None
    for key_cls in (paramiko.Ed25519Key, paramiko.RSAKey,
                    paramiko.ECDSAKey, paramiko.DSSKey):
        try:
            return key_cls.from_private_key(io.StringIO(pem))
        except Exception as exc:  # wrong type / parse error — try the next
            last_err = exc
    raise ValueError(f"Unrecognised private key: {last_err}")


def public_line_from_private(pem):
    """Derive the public 'type base64 comment' line from a private key string."""
    k = _load_private_key(pem)
    return f"{k.get_name()} {k.get_base64()} climweb-backup"


# --------------------------------------------------------------------------- #
# Connection
# --------------------------------------------------------------------------- #
def _connect(backup_settings):
    """Open an SFTP session, pinning the host key on first use. May update and
    save ``backup_settings.sftp_host_key``."""
    host = backup_settings.sftp_host
    port = backup_settings.sftp_port or 22
    username = backup_settings.sftp_username

    sock = socket.create_connection((host, port), timeout=30)
    transport = paramiko.Transport(sock)
    transport.start_client(timeout=30)

    server_key = transport.get_remote_server_key()
    key_line = f"{server_key.get_name()} {server_key.get_base64()}"
    pinned = (backup_settings.sftp_host_key or "").strip()
    if pinned:
        if pinned != key_line:
            transport.close()
            raise HostKeyChangedError(
                "The destination server's SSH host key has changed. If this is "
                "expected, clear the pinned host key and reconnect; otherwise this "
                "could be a man-in-the-middle and the backup was aborted."
            )
    else:
        backup_settings.sftp_host_key = key_line
        backup_settings.save(update_fields=["sftp_host_key"])
        logger.info(f"[BACKUP] Pinned SFTP host key for {host}")

    if backup_settings.sftp_auth_method == "password":
        transport.auth_password(username, backup_settings.get_sftp_password())
    else:
        pkey = _load_private_key(backup_settings.get_sftp_private_key())
        transport.auth_publickey(username, pkey)

    return paramiko.SFTPClient.from_transport(transport), transport


def _ensure_remote_dir(sftp, path):
    """mkdir -p for a (possibly nested, relative or absolute) remote path."""
    parts = [p for p in path.split("/") if p]
    current = "/" if path.startswith("/") else "."
    for part in parts:
        current = current.rstrip("/") + "/" + part
        try:
            sftp.stat(current)
        except IOError:
            sftp.mkdir(current)
    return current


def _prune(sftp, remote_dir, name_prefix, keep):
    names = []
    try:
        for entry in sftp.listdir_attr(remote_dir):
            if entry.filename.startswith(name_prefix) and not stat.S_ISDIR(entry.st_mode):
                names.append(entry.filename)
    except IOError:
        return
    # Names are date-stamped, so lexical sort == chronological.
    for stale in sorted(names, reverse=True)[keep:]:
        sftp.remove(remote_dir.rstrip("/") + "/" + stale)
        logger.info(f"[BACKUP] Pruned old remote backup {stale}")


def test_connection(backup_settings):
    """Open and close a session — used by a manual 'test' action."""
    sftp, transport = _connect(backup_settings)
    try:
        _ensure_remote_dir(sftp, backup_settings.sftp_remote_path or "climweb-backups")
    finally:
        transport.close()


def upload_backups(backup_settings, backup_dir, run_media=None):
    """Upload the latest DB dump (always) and media archive (on the configured
    weekday) to the remote server over SFTP, then prune old copies. Overwrites
    same-named files in place, so repeated runs never leave duplicates."""
    site_label = _site_label(backup_settings)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    base_path = backup_settings.sftp_remote_path or "climweb-backups"

    sftp, transport = _connect(backup_settings)
    messages = []
    try:
        root = _ensure_remote_dir(sftp, base_path)
        db_dir = _ensure_remote_dir(sftp, root.rstrip("/") + "/db")

        db_file = (_newest_file(backup_dir, ".psql.bin")
                   or _newest_file(backup_dir, ".dump")
                   or _newest_file(backup_dir, ".sql"))
        if db_file:
            remote_name = f"{site_label}-db-{today}.psql.bin"
            sftp.put(db_file, db_dir.rstrip("/") + "/" + remote_name)
            _prune(sftp, db_dir, f"{site_label}-db-", backup_settings.db_retention_days)
            messages.append(f"db: {remote_name}")
        else:
            messages.append("db: no dump found")

        if run_media is None:
            run_media = datetime.utcnow().weekday() == backup_settings.media_upload_weekday

        if run_media:
            media_file = _newest_file(backup_dir, ".tar")
            if media_file:
                media_dir = _ensure_remote_dir(sftp, root.rstrip("/") + "/media")
                remote_name = f"{site_label}-media-{today}.tar"
                sftp.put(media_file, media_dir.rstrip("/") + "/" + remote_name)
                _prune(sftp, media_dir, f"{site_label}-media-",
                       backup_settings.media_retention_days)
                messages.append(f"media: {remote_name}")
            else:
                messages.append("media: no archive found")
    finally:
        transport.close()

    return "; ".join(messages)
