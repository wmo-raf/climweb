"""
HTTP API used by climweb-sync running on a national met service server.

Endpoints
---------
GET  /api/product-sync/setup.sh              bootstrap installer script
POST /api/product-sync/setup/exchange/       one-time code -> token + settings
GET  /api/product-sync/ping/                 credential check
POST /api/product-sync/upload/               receive one file

Everything a source server needs is derived here from the Product snippet, so
the operator never transcribes a path. The destination is resolved with the
same logic the ingestion task uses, which is what keeps the two from drifting.
"""

import os
import tempfile

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from loguru import logger

from .sync_models import ProductSyncCredential, ProductSyncSetupCode

# A generous ceiling; individual sites can lower it in settings. Bulletins are
# typically well under 10 MB, and anything far larger is usually a mistake.
MAX_UPLOAD_BYTES = getattr(settings, "PRODUCT_SYNC_MAX_UPLOAD_BYTES", 100 * 1024 * 1024)

GITHUB_REPO = getattr(
    settings, "PRODUCT_SYNC_TOOL_REPO", "https://github.com/wmo-raf/climweb-product-sync"
)


# -----------------------------------------------------------------------------
# helpers
# -----------------------------------------------------------------------------
def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _bearer_token(request):
    header = request.META.get("HTTP_AUTHORIZATION", "")
    if header.startswith("Bearer "):
        return header[7:].strip()
    return ""


def _authenticate(request):
    """Return a credential or None. Callers must handle None themselves."""
    return ProductSyncCredential.authenticate(_bearer_token(request))


def _error(status, code, message):
    return JsonResponse({"error": code, "detail": message}, status=status)


def _env_response(data):
    """
    Render a flat dict as shell assignments.

    The client is a bash script on a met service server that may not have jq
    installed, so it asks for this instead of JSON. Values are single-quoted and
    embedded quotes are escaped, so the client can source the response safely.
    """
    lines = []
    for key, value in data.items():
        text = "" if value is None else str(value)
        escaped = text.replace("'", "'\\''")
        lines.append(f"{key.upper()}='{escaped}'")
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain; charset=utf-8")


def resolve_watch_root(watch_root):
    """Mirror of tasks.py::_resolve_watch_root, so both paths agree exactly."""
    if os.path.isabs(watch_root):
        return watch_root
    return os.path.join(settings.MEDIA_ROOT, watch_root)


def product_formats(product):
    """The file formats configured on this product's categories."""
    formats = []
    for category in product.categories.all():
        fmt = (category.category_format or "").lower().strip()
        if fmt and fmt not in formats:
            formats.append(fmt)
    return formats


def safe_destination(base_dir, relative_path):
    """
    Resolve relative_path inside base_dir, or return None if it escapes.

    relative_path comes from the network, so this is the boundary that stops a
    caller writing outside the watch folder. Rejecting the obvious '..' is not
    enough on its own: the final containment check is what actually holds, and
    it is done against the real path so an existing symlink cannot be used to
    step outside either.
    """
    if not relative_path:
        return None
    normalised = relative_path.replace("\\", "/").strip()
    if normalised.startswith("/") or ":" in normalised.split("/")[0]:
        return None

    parts = []
    for part in normalised.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            return None
        if part.startswith("."):
            # No dotfiles: nothing legitimate is named this way, and it keeps
            # things like .ssh or .htaccess off the table entirely.
            return None
        parts.append(part)
    if not parts:
        return None

    base_real = os.path.realpath(base_dir)
    candidate = os.path.join(base_real, *parts)

    # Check the containment of the resolved parent, since the file itself may
    # not exist yet.
    parent_real = os.path.realpath(os.path.dirname(candidate))
    if parent_real != base_real and not parent_real.startswith(base_real + os.sep):
        return None

    if os.path.islink(candidate):
        return None

    return candidate


# -----------------------------------------------------------------------------
# GET /api/product-sync/setup.sh
# -----------------------------------------------------------------------------
@require_GET
def setup_script(request):
    """
    The bootstrap script fetched by the one-line command shown in the admin.

    It only installs the tool and hands over to its own wizard; all the real
    logic lives in the versioned repository rather than in a string here.
    """
    base_url = request.build_absolute_uri("/").rstrip("/")
    script = f"""#!/usr/bin/env bash
# climweb-sync bootstrap — installs the sync tool and runs its setup wizard.
#   curl -fsSL {base_url}/api/product-sync/setup.sh | sudo bash -s CODE
set -euo pipefail

CODE="${{1:-}}"
SERVER="{base_url}"
REPO="{GITHUB_REPO}"

if [ "$(id -u)" -ne 0 ]; then
    echo "Please run this with sudo." >&2
    exit 1
fi

if [ -z "$CODE" ]; then
    echo "Usage: curl -fsSL $SERVER/api/product-sync/setup.sh | sudo bash -s YOUR-SETUP-CODE" >&2
    exit 1
fi

missing=""
for dep in curl tar awk find; do
    command -v "$dep" >/dev/null 2>&1 || missing="$missing $dep"
done
if [ -n "$missing" ]; then
    echo "Missing required commands:$missing" >&2
    echo "On Debian/Ubuntu: sudo apt install curl tar gawk findutils" >&2
    exit 1
fi

echo "Downloading the ClimWeb sync tool..."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

if ! curl -fsSL "$REPO/archive/refs/heads/main.tar.gz" -o "$tmp/tool.tar.gz"; then
    echo "Could not download the tool from $REPO." >&2
    echo "If this server has no access to GitHub, ask your ClimWeb administrator" >&2
    echo "for an offline copy and run ./install.sh from it instead." >&2
    exit 1
fi

tar -xzf "$tmp/tool.tar.gz" -C "$tmp"
cd "$tmp"/climweb-product-sync-*

./install.sh --no-schedule
exec climweb-sync setup --server "$SERVER" "$CODE"
"""
    return HttpResponse(script, content_type="text/x-shellscript; charset=utf-8")


# -----------------------------------------------------------------------------
# POST /api/product-sync/setup/exchange/
# -----------------------------------------------------------------------------
@csrf_exempt
@require_POST
def setup_exchange(request):
    """
    Trade a one-time setup code for a token and this product's settings.

    Deliberately unauthenticated — possession of the code is the credential.
    That is acceptable because a code is single-use, expires in 48 hours,
    is scoped to one product, and grants only the ability to upload files of
    one format into one folder.
    """
    code = request.POST.get("code") or ""
    hostname = request.POST.get("hostname") or ""
    fmt = request.POST.get("format") or ""

    setup_code = ProductSyncSetupCode.claim(code)
    if setup_code is None:
        logger.warning(
            f"[PRODUCT-SYNC] Rejected setup code from {_client_ip(request)}"
        )
        return _error(
            403,
            "invalid_code",
            "That setup code is not valid. It may have expired, or already been "
            "used. Ask whoever manages the website to generate a new one.",
        )

    product = setup_code.product

    if not product.variable_name:
        return _error(
            409,
            "product_not_configured",
            f"The product '{product.name}' has no Variable Name set in the CMS, "
            "so there is nowhere to put the files yet.",
        )

    formats = product_formats(product)
    if not formats:
        return _error(
            409,
            "product_not_configured",
            f"The product '{product.name}' has no file format configured on any "
            "of its categories.",
        )

    credential, token = ProductSyncCredential.issue(product, hostname)

    setup_code.used_at = timezone.now()
    setup_code.used_by_host = hostname[:255]
    setup_code.save(update_fields=["used_at", "used_by_host"])

    logger.info(
        f"[PRODUCT-SYNC] Setup code redeemed for '{product.name}' by "
        f"'{hostname}' ({_client_ip(request)})"
    )

    payload = {
        "product_name": product.name,
        "variable_name": product.variable_name,
        "formats": ",".join(formats),
        "format": formats[0],
        "ingestion_enabled": "true" if product.ingestion_enabled else "false",
        "watch_root": resolve_watch_root(product.watch_root or ""),
        "base_url": request.build_absolute_uri("/").rstrip("/"),
        "token": token,
        "credential_id": credential.pk,
    }

    if fmt == "env":
        return _env_response(payload)
    return JsonResponse(payload)


# -----------------------------------------------------------------------------
# GET /api/product-sync/ping/
# -----------------------------------------------------------------------------
@require_GET
def ping(request):
    credential = _authenticate(request)
    if credential is None:
        return _error(401, "invalid_token", "The token was not accepted.")

    credential.touch(ip=_client_ip(request))
    product = credential.product

    payload = {
        "status": "ok",
        "product_name": product.name,
        "variable_name": product.variable_name,
        "formats": ",".join(product_formats(product)),
        "ingestion_enabled": "true" if product.ingestion_enabled else "false",
    }
    if request.GET.get("format") == "env":
        return _env_response(payload)
    return JsonResponse(payload)


# -----------------------------------------------------------------------------
# POST /api/product-sync/upload/
# -----------------------------------------------------------------------------
@csrf_exempt
@require_POST
def upload(request):
    credential = _authenticate(request)
    if credential is None:
        return _error(401, "invalid_token", "The token was not accepted.")

    product = credential.product
    variable_name = (request.POST.get("variable_name") or "").strip()
    fmt = (request.POST.get("format") or "").strip().lower()
    relative_path = request.POST.get("relative_path") or ""
    upload_file = request.FILES.get("file")

    if upload_file is None:
        return _error(400, "no_file", "No file was included in the request.")

    # The credential is scoped to a product; a mismatched variable_name means
    # the client is misconfigured, and silently accepting it would put files
    # somewhere the operator does not expect.
    if variable_name and variable_name != product.variable_name:
        return _error(
            400,
            "wrong_product",
            f"This token is for '{product.variable_name}', not '{variable_name}'.",
        )

    allowed_formats = product_formats(product)
    if fmt not in allowed_formats:
        return _error(
            400,
            "bad_format",
            f"'{fmt}' is not a format configured for this product "
            f"(expected one of: {', '.join(allowed_formats) or 'none'}).",
        )

    # The extension must match the declared format, so a .php cannot be smuggled
    # in under format=pdf.
    extension = os.path.splitext(relative_path)[1].lstrip(".").lower()
    if extension != fmt:
        return _error(
            400,
            "bad_extension",
            f"The file extension '.{extension}' does not match the format '{fmt}'.",
        )

    if upload_file.size > MAX_UPLOAD_BYTES:
        return _error(
            413,
            "too_large",
            f"The file is {upload_file.size} bytes; the limit is {MAX_UPLOAD_BYTES}.",
        )

    if not product.watch_root or not product.variable_name:
        return _error(
            409,
            "product_not_configured",
            "This product has no watch root or variable name set in the CMS.",
        )

    base_dir = os.path.join(
        resolve_watch_root(product.watch_root), product.variable_name, fmt
    )
    destination = safe_destination(base_dir, relative_path)
    if destination is None:
        logger.warning(
            f"[PRODUCT-SYNC] Rejected unsafe path '{relative_path}' from "
            f"{_client_ip(request)} (credential {credential.pk})"
        )
        return _error(400, "bad_path", "That file path is not allowed.")

    try:
        os.makedirs(os.path.dirname(destination), exist_ok=True)
    except OSError as exc:
        logger.error(f"[PRODUCT-SYNC] Could not create {destination}: {exc}")
        return _error(500, "write_failed", "The server could not create the folder.")

    # Write to a temporary file in the same directory, then rename. The
    # ingestion scan runs on its own timer and would otherwise be able to pick
    # up a half-written bulletin.
    try:
        fd, tmp_path = tempfile.mkstemp(
            dir=os.path.dirname(destination), prefix=".upload-", suffix=".part"
        )
        try:
            with os.fdopen(fd, "wb") as handle:
                for chunk in upload_file.chunks():
                    handle.write(chunk)
            os.chmod(tmp_path, 0o644)
            existed = os.path.exists(destination)
            os.replace(tmp_path, destination)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
    except OSError as exc:
        logger.error(f"[PRODUCT-SYNC] Failed writing {destination}: {exc}")
        return _error(500, "write_failed", "The server could not save the file.")

    credential.touch(ip=_client_ip(request), uploaded=True)
    logger.info(f"[PRODUCT-SYNC] Received {destination} ({upload_file.size} bytes)")

    # Ingestion is intentionally left to the existing periodic task, so both
    # transports converge on one code path and there is a single behaviour to
    # reason about.
    return JsonResponse(
        {"status": "replaced" if existed else "stored", "path": relative_path},
        status=200 if existed else 201,
    )
