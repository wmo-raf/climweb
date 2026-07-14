from django.db.models import F
from django.http import Http404
from django.shortcuts import redirect
from django.views.decorators.http import require_GET

from .models import ShortLink


@require_GET
def redirect_short_link(request, short_code):
    try:
        link = ShortLink.objects.get(short_code=short_code, is_active=True)
    except ShortLink.DoesNotExist:
        raise Http404("Short link not found")

    # Avoid re-fetching/re-saving the whole instance just to bump a counter
    ShortLink.objects.filter(pk=link.pk).update(click_count=F("click_count") + 1)

    return redirect(link.target_url)
