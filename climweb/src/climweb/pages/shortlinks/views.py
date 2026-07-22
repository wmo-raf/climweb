from urllib.parse import urlparse

from django.core.cache import cache
from django.db.models import F
from django.http import Http404, JsonResponse
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_POST
from wagtail.models import Site

from .models import ShortLink

# Simple, dependency-free IP-based throttle for the share endpoint, backed by
# whatever CACHES["default"] already is (Redis in this project). Avoids pulling
# in django-ratelimit just for this. The limit is generous because the endpoint
# only ever shortens URLs on our own domain (see _is_allowed_url), so the abuse
# surface is small - this is really just to stop runaway DB spam.
SHORTEN_RATE_LIMIT = 60
SHORTEN_RATE_LIMIT_WINDOW = 60 * 60  # seconds (1 hour)


@require_GET
def redirect_short_link(request, short_code):
    try:
        link = ShortLink.objects.get(short_code=short_code, is_active=True)
    except ShortLink.DoesNotExist:
        raise Http404("Short link not found")

    # Avoid re-fetching/re-saving the whole instance just to bump a counter
    ShortLink.objects.filter(pk=link.pk).update(click_count=F("click_count") + 1)

    return redirect(link.target_url)


def _get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        # Leftmost address is the original client (nginx appends to this header)
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _allowed_hosts(request):
    """Hostnames we're willing to create short links for: the current request
    host plus every configured Wagtail Site hostname."""
    hosts = {request.get_host().split(":")[0]}
    hosts.update(Site.objects.values_list("hostname", flat=True))
    return hosts


def _is_allowed_url(request, url):
    """Only allow shortening of same-site http(s) URLs. Because the button
    always shortens the page the visitor is currently on, a well-behaved client
    only ever submits our own URLs; this check stops the endpoint being abused
    to mint short links pointing at arbitrary external (e.g. phishing) sites."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return False
    return parsed.hostname in _allowed_hosts(request)


@require_POST
def create_short_link(request):
    url = (request.POST.get("url") or "").strip()

    if not url:
        return JsonResponse({"error": _("No URL provided.")}, status=400)

    if not _is_allowed_url(request, url):
        return JsonResponse(
            {"error": _("Only links on this website can be shortened.")}, status=400
        )

    # Reuse an existing short link for this exact URL if we already have one,
    # so the same page always maps to the same short link.
    link = ShortLink.objects.filter(target_url=url).order_by("created_at").first()
    created = False

    if link is None:
        # Only rate-limit actual creation - repeat requests for an
        # already-shortened URL are cheap lookups and shouldn't count.
        cache_key = f"shortlinks:shorten:{_get_client_ip(request)}"
        if cache.get(cache_key, 0) >= SHORTEN_RATE_LIMIT:
            return JsonResponse(
                {"error": _("Too many short links created from this location. "
                            "Please try again later.")},
                status=429,
            )

        link = ShortLink.objects.create(target_url=url, source=ShortLink.Source.PUBLIC)
        created = True

        try:
            cache.incr(cache_key)
        except ValueError:
            cache.set(cache_key, 1, timeout=SHORTEN_RATE_LIMIT_WINDOW)

    return JsonResponse(
        {"short_url": link.get_short_url(request), "created": created}
    )
