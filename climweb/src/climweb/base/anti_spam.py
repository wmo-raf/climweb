"""
Lightweight, layered anti-spam helpers for public form pages.

reCAPTCHA alone no longer reliably stops form spam (bots use captcha-solving
services and headless browsers to submit valid tokens). These checks add three
cheap, high-signal filters on top of the existing captcha:

    1. Honeypot   - a hidden field only bots fill in.
    2. Timing     - reject forms submitted implausibly fast after page load.
    3. Link flood - reject messages stuffed with URLs / anchor tags.

The honeypot and timestamp inputs are rendered by the ``antispam_protect``
template tag (see base/templatetags/antispam.py) and read back from the raw
POST data, so they never touch the stored form submission. Call
``get_spam_reason(request, form)`` from a form page's ``serve()`` after
``form.is_valid()`` and route flagged submissions to the existing
"suspicious form" path.
"""

import re
import time

from django.conf import settings
from django.core import signing

# --- Tunable thresholds (override in Django settings if needed) ---
# Minimum seconds between rendering the form and submitting it. Humans virtually
# never fill and submit a contact form faster than this; bots often do.
MIN_SUBMIT_SECONDS = int(getattr(settings, "ANTISPAM_MIN_SUBMIT_SECONDS", 3))
# Max number of link-like tokens allowed across all text fields before a
# submission is treated as spam.
MAX_LINKS = int(getattr(settings, "ANTISPAM_MAX_LINKS", 2))

# Field names used by the antispam_protect template tag. Named to look
# fillable to bots while being unlikely to collide with editor-created fields.
HONEYPOT_FIELD_NAME = "contact_url"
TIMESTAMP_FIELD_NAME = "form_loaded_at"

_signer = signing.Signer(salt="climweb.base.anti_spam.form-timestamp")

# Matches the link forms seen in real form spam: bare URLs, www. hosts,
# HTML anchor tags and BBCode-style [url]/[link] tags.
_LINK_RE = re.compile(r"(https?://|www\.|<\s*a\s|\[\s*(?:url|link))", re.IGNORECASE)


def make_timestamp():
    """Return a signed, tamper-evident token encoding the current time.

    Embedded in the form when it is rendered so the server can measure how long
    the visitor took to submit.
    """
    return _signer.sign(str(int(time.time())))


def _submitted_too_fast(token):
    """True only if ``token`` is a valid signed timestamp AND the form was
    submitted faster than a human plausibly could.

    Missing or tampered tokens return False so a stripped/forged field never
    blocks a legitimate user on its own; the honeypot and link checks cover
    those cases.
    """
    if not token:
        return False
    try:
        loaded_at = int(_signer.unsign(token))
    except (signing.BadSignature, ValueError, TypeError):
        return False
    return (time.time() - loaded_at) < MIN_SUBMIT_SECONDS


def _count_links(cleaned_data):
    count = 0
    for value in cleaned_data.values():
        if isinstance(value, str):
            count += len(_LINK_RE.findall(value))
    return count


def get_spam_reason(request, form):
    """Return a short reason string if the submission looks like spam, else None.

    Call after ``form.is_valid()``. ``form`` must expose ``cleaned_data``.
    """
    post = getattr(request, "POST", {})

    # 1. Honeypot: a hidden field only bots fill in.
    if post.get(HONEYPOT_FIELD_NAME, "").strip():
        return "honeypot filled"

    # 2. Timing: submitted implausibly fast after the page loaded.
    if _submitted_too_fast(post.get(TIMESTAMP_FIELD_NAME, "")):
        return "submitted too fast"

    # 3. Link flood: link-stuffed message bodies.
    cleaned = getattr(form, "cleaned_data", None) or {}
    if _count_links(cleaned) > MAX_LINKS:
        return "too many links"

    return None
