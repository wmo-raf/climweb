import random
import string

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.api.v2.utils import get_full_url
from wagtail.models import Site
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import EditView, SnippetViewSet

SHORT_CODE_ALPHABET = string.ascii_letters + string.digits
SHORT_CODE_LENGTH = 6


def generate_short_code(length=SHORT_CODE_LENGTH):
    return "".join(random.choices(SHORT_CODE_ALPHABET, k=length))


class ShortLink(models.Model):
    class Source(models.TextChoices):
        ADMIN = "admin", _("Created in admin")
        PUBLIC = "public", _("Submitted via public form")

    source = models.CharField(
        max_length=10,
        choices=Source.choices,
        default=Source.ADMIN,
        editable=False,
        verbose_name=_("Source"),
        help_text=_("Whether this link was created by a logged-in editor or submitted anonymously via the public form."),
    )
    short_code = models.CharField(
        max_length=15,
        unique=True,
        blank=True,
        verbose_name=_("Short code"),
        help_text=_(
            "Leave blank to auto-generate. Only letters, numbers, - and _ are allowed. "
            "This is the part that appears after /s/ in the short link."
        ),
    )
    target_url = models.URLField(
        max_length=2000,
        verbose_name=_("Target URL"),
        help_text=_("The full URL this short link should redirect visitors to."),
    )
    label = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Label"),
        help_text=_("Optional note to help editors remember what this link is for."),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Untick to disable this short link without deleting it."),
    )
    click_count = models.PositiveIntegerField(default=0, editable=False, verbose_name=_("Click count"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Created by"),
    )

    panels = [
        FieldPanel("target_url"),
        FieldPanel("short_code"),
        FieldPanel("label"),
        FieldPanel("is_active"),
    ]

    class Meta:
        verbose_name = _("Short Link")
        verbose_name_plural = _("Short Links")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.short_code} -> {self.target_url}"

    def save(self, *args, **kwargs):
        if not self.short_code:
            code = generate_short_code()
            while ShortLink.objects.filter(short_code=code).exists():
                code = generate_short_code()
            self.short_code = code

        super().save(*args, **kwargs)

    def get_short_url(self, request=None):
        """
        Returns the full, absolute short URL. Pass a `request` when one is
        available (e.g. from a view) for the most accurate host/scheme;
        otherwise falls back to the default Wagtail Site's root URL, which
        is what makes `full_short_url` usable from the admin listing/edit
        views where no request-aware helper is otherwise available.
        """
        relative_url = reverse("shortlink_redirect", args=[self.short_code])

        if request is not None:
            return get_full_url(request, relative_url)

        try:
            root_url = Site.objects.get(is_default_site=True).root_url
        except Site.DoesNotExist:
            return relative_url

        return f"{root_url.rstrip('/')}{relative_url}"

    @property
    def full_short_url(self):
        return self.get_short_url()

    full_short_url.fget.short_description = _("Short URL")


class ShortLinkEditView(EditView):
    edit_template_name = "shortlinks/shortlink_edit.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["full_short_url"] = self.object.full_short_url
        return context


class ShortLinkViewSet(SnippetViewSet):
    model = ShortLink
    icon = "link"
    menu_label = _("Short Links")
    menu_name = "shortlinks"
    add_to_admin_menu = True
    edit_view_class = ShortLinkEditView
    list_display = (
        "short_code", "full_short_url", "target_url", "label", "source", "click_count", "is_active", "created_at",
    )
    list_filter = ("source", "is_active")
    search_fields = ("short_code", "target_url", "label")


register_snippet(ShortLinkViewSet)
