"""Read container logs over a read-only Docker socket proxy.

The CMS container never touches /var/run/docker.sock directly. Instead a
`tecnativa/docker-socket-proxy` sidecar sits on the internal compose network with
only `CONTAINERS=1` and `LOGS=1` enabled, and this module talks to it over HTTP.
Nothing is published to the host, so no new port or subdomain is needed.

See `climweb-docker/setup-log-viewer.md` for the deployment side.
"""

import logging
import os
import re
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Timestamps docker prefixes onto each line when `timestamps=True`. RFC3339 with
# nanosecond precision, which sorts correctly as a plain string.
_TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T[\d:.]+Z)\s?(.*)$", re.DOTALL)

# Log levels we know how to colour/filter in the admin UI.
_LEVEL_RE = re.compile(
    r"\b(CRITICAL|FATAL|ERROR|WARNING|WARN|INFO|DEBUG)\b"
)

# Env var names whose *values* must never reach a browser, even if some library
# helpfully logged them. Matched case-insensitively as substrings.
_SECRET_KEY_HINTS = (
    "secret", "password", "passwd", "token", "api_key", "apikey", "private_key",
    "client_secret", "credential", "sentry_dsn", "database_url", "redis_url",
)

CACHE_KEY_CONTAINERS = "climweb_log_viewer_containers"


class LogViewerError(Exception):
    """Raised for any condition the admin UI should show as a friendly message."""


class LogViewerDisabled(LogViewerError):
    pass


def is_enabled():
    return bool(getattr(settings, "CLIMWEB_LOG_VIEWER_ENABLED", False))


def _docker_host():
    host = getattr(settings, "CLIMWEB_DOCKER_HOST", "") or ""
    if not host:
        raise LogViewerDisabled(
            "No Docker socket proxy is configured (CLIMWEB_DOCKER_HOST is empty)."
        )
    return host


def get_client():
    """Return a docker client pointed at the socket proxy.

    `docker` is an optional dependency: an instance that has not enabled the log
    viewer should not be forced to install it.
    """
    if not is_enabled():
        raise LogViewerDisabled("The log viewer is disabled on this instance.")

    # Resolve config before touching the optional dependency, so a
    # half-configured instance reports the useful error rather than an import one.
    host = _docker_host()

    try:
        import docker
    except ImportError as exc:  # pragma: no cover - depends on install profile
        raise LogViewerError(
            "The `docker` Python package is not installed in this image."
        ) from exc

    try:
        return docker.DockerClient(
            base_url=host,
            timeout=getattr(settings, "CLIMWEB_LOG_VIEWER_TIMEOUT", 10),
        )
    except Exception as exc:
        raise LogViewerError(f"Could not reach the Docker socket proxy: {exc}") from exc


# ---------------------------------------------------------------------------
# Container allow-list
# ---------------------------------------------------------------------------

def _allowed_names():
    """Explicit allow-list from settings, if the deployment set one."""
    return [
        n.strip()
        for n in getattr(settings, "CLIMWEB_LOG_VIEWER_CONTAINERS", []) or []
        if n.strip()
    ]


def _name_prefix():
    return getattr(settings, "CLIMWEB_LOG_VIEWER_NAME_PREFIX", "climweb")


def list_containers(use_cache=True):
    """Containers whose logs this instance is allowed to show.

    Defaults to everything in the ClimWeb stack (name prefix `climweb`) so a
    fresh deployment works with no extra config, but an explicit
    CLIMWEB_LOG_VIEWER_CONTAINERS list always wins.
    """
    if use_cache:
        cached = cache.get(CACHE_KEY_CONTAINERS)
        if cached is not None:
            return cached

    client = get_client()
    allowed = _allowed_names()
    prefix = _name_prefix()

    try:
        containers = client.containers.list(all=True)
    except Exception as exc:
        raise LogViewerError(f"Could not list containers: {exc}") from exc

    result = []
    for container in containers:
        name = container.name
        if allowed:
            if name not in allowed:
                continue
        elif prefix and not name.startswith(prefix):
            continue
        result.append({
            "name": name,
            "status": container.status,
            "image": (container.image.tags or [""])[0] if container.image else "",
        })

    result.sort(key=lambda c: (c["name"] != "climweb", c["name"]))
    cache.set(CACHE_KEY_CONTAINERS, result, 30)
    return result


def resolve_container(name):
    """Look a container up *through* the allow-list.

    Never pass a user-supplied name straight to the Docker API: that would let
    any CMS superuser read the logs of unrelated containers sharing the host.
    """
    if not name:
        raise LogViewerError("No container was selected.")

    permitted = {c["name"] for c in list_containers()}
    if name not in permitted:
        raise LogViewerError(f"'{name}' is not a container this instance may read.")

    client = get_client()
    try:
        return client.containers.get(name)
    except Exception as exc:
        raise LogViewerError(f"Could not open container '{name}': {exc}") from exc


# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------

def _secret_values():
    """Values from the process environment that must be masked in log output.

    Tracebacks and third-party libraries leak connection strings surprisingly
    often, and the whole point of this feature is to put logs in front of people
    who do *not* have shell access to the server.
    """
    values = set()
    for key, value in os.environ.items():
        if not value or len(value) < 8:
            continue
        lowered = key.lower()
        if any(hint in lowered for hint in _SECRET_KEY_HINTS):
            values.add(value)
            # Connection strings: also mask the password component on its own.
            match = re.match(r"^[a-z+]+://[^:/@]+:([^@]+)@", value, re.IGNORECASE)
            if match and len(match.group(1)) >= 6:
                values.add(match.group(1))

    for extra in getattr(settings, "CLIMWEB_LOG_VIEWER_EXTRA_REDACTIONS", []) or []:
        if extra and len(extra) >= 6:
            values.add(extra)

    # Longest first, so overlapping values mask completely.
    return sorted(values, key=len, reverse=True)


def redact(text, secrets=None):
    if not text:
        return text
    for secret in (_secret_values() if secrets is None else secrets):
        if secret in text:
            text = text.replace(secret, "[redacted]")
    return text


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------

def _parse_rfc3339(value):
    """Parse a docker log timestamp.

    Docker emits nanosecond precision (9 fractional digits) but
    `datetime.fromisoformat` only accepts 3 or 6, so the fraction has to be
    truncated first — otherwise every `since` silently fails to parse and the
    viewer re-fetches the whole tail on every poll.
    """
    text = value.strip().replace("Z", "+00:00")
    match = re.match(r"^(.*?\.\d{6})\d*(.*)$", text)
    if match:
        text = match.group(1) + match.group(2)
    return datetime.fromisoformat(text)


def _parse_line(raw):
    """Split a docker log line into its timestamp, level and message."""
    line = raw.rstrip("\r\n")
    if not line:
        return None

    timestamp = ""
    message = line
    match = _TS_RE.match(line)
    if match:
        timestamp, message = match.group(1), match.group(2)

    level_match = _LEVEL_RE.search(message[:200])
    level = level_match.group(1).upper() if level_match else ""
    if level == "WARN":
        level = "WARNING"
    if level == "FATAL":
        level = "CRITICAL"

    return {"ts": timestamp, "level": level, "message": message}


def fetch_logs(container_name, tail=200, since=None, max_lines=2000):
    """Return parsed, redacted log lines for one container.

    `since` is an RFC3339 timestamp string (the `ts` of the last line the client
    already has). Docker's `since` filter has one-second granularity, so the
    caller still has to drop anything it has already seen — the view does that
    with a string comparison, which is safe for RFC3339.
    """
    container = resolve_container(container_name)

    tail = max(1, min(int(tail or 200), max_lines))

    kwargs = {"stdout": True, "stderr": True, "timestamps": True}
    if since:
        try:
            since_dt = _parse_rfc3339(since)
            # Step back a second: docker's `since` is inclusive at second
            # granularity and we would rather over-fetch and dedupe.
            kwargs["since"] = since_dt.astimezone(timezone.utc) - timedelta(seconds=1)
            kwargs["tail"] = max_lines
        except ValueError:
            kwargs["tail"] = tail
    else:
        kwargs["tail"] = tail

    try:
        raw = container.logs(**kwargs)
    except Exception as exc:
        raise LogViewerError(f"Could not read logs for '{container_name}': {exc}") from exc

    text = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else str(raw)

    secrets = _secret_values()
    lines = []
    for raw_line in text.splitlines():
        parsed = _parse_line(raw_line)
        if parsed is None:
            continue
        parsed["message"] = redact(parsed["message"], secrets)
        lines.append(parsed)

    return lines[-max_lines:]


def fetch_logs_text(container_name, tail=1000):
    """Flat text for the download button."""
    lines = fetch_logs(container_name, tail=tail, max_lines=tail)
    return "\n".join(
        f"{line['ts']} {line['message']}".strip() for line in lines
    )
