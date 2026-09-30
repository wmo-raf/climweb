import ipaddress

from django.conf import settings


def _valid_ip(value):
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return None


def client_ip(request):
    """The client address as seen by the outermost of our own proxies.

    Each proxy appends the address it received the request from to
    X-Forwarded-For (nginx's `$proxy_add_x_forwarded_for`), so with N proxies in
    front of Django the client is the Nth entry from the right. Anything to the
    left of that was supplied by the client and could be forged, so it is never
    used. N comes from AXES_IPWARE_PROXY_COUNT.

    Used as AXES_CLIENT_IP_CALLABLE. Returns None rather than an unparseable
    value, since axes stores the result in a GenericIPAddressField.
    """
    proxy_count = getattr(settings, "AXES_IPWARE_PROXY_COUNT", 0) or 0
    forwarded = [
        address.strip()
        for address in request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")
        if address.strip()
    ]
    if proxy_count and forwarded:
        # Fewer entries than proxies means the request skipped a proxy we
        # expected; the leftmost entry is then the best we have.
        return _valid_ip(forwarded[-min(proxy_count, len(forwarded))])
    return _valid_ip(request.META.get("REMOTE_ADDR", ""))
