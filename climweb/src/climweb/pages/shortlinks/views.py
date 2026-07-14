from django.core.cache import cache
from django.db.models import F
from django.http import Http404
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET
from django.views.generic import FormView

from .forms import PublicShortLinkForm
from .models import ShortLink

# Simple, dependency-free IP-based throttle for the public form, backed by
# whatever CACHES["default"] already is (Redis in this project). Avoids
# pulling in django-ratelimit just for this one view.
PUBLIC_FORM_RATE_LIMIT = 5
PUBLIC_FORM_RATE_LIMIT_WINDOW = 60 * 60  # seconds (1 hour)


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


class PublicShortenLinkView(FormView):
    """
    Public, unauthenticated page that lets any visitor submit a URL and get
    a short link back. Protected against automated abuse with a CAPTCHA
    (on the form itself) and a per-IP rate limit (below), since anything
    submitted here is publicly reachable at /s/<code>/ on our own domain.
    """

    template_name = "shortlinks/public_shorten.html"
    form_class = PublicShortLinkForm

    def _rate_limit_cache_key(self):
        return f"shortlinks:public-submit:{_get_client_ip(self.request)}"

    def _is_rate_limited(self):
        return cache.get(self._rate_limit_cache_key(), 0) >= PUBLIC_FORM_RATE_LIMIT

    def _register_submission(self):
        cache_key = self._rate_limit_cache_key()
        try:
            cache.incr(cache_key)
        except ValueError:
            # Key doesn't exist yet (or already expired) - start a fresh window
            cache.set(cache_key, 1, timeout=PUBLIC_FORM_RATE_LIMIT_WINDOW)

    def post(self, request, *args, **kwargs):
        if self._is_rate_limited():
            form = self.get_form()
            form.add_error(
                None,
                _("You've reached the limit for creating short links from this location. "
                  "Please try again later."),
            )
            return self.form_invalid(form)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        self._register_submission()
        self.created_link = form.save()
        # Re-render the same page with the result rather than redirecting,
        # so we can show the generated short link inline.
        return self.render_to_response(self.get_context_data(form=self.get_form_class()(), success=True))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if getattr(self, "created_link", None):
            context["short_url"] = self.created_link.full_short_url
        return context
