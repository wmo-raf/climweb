from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from wagtail.admin.views.pages.create import CreateView
from wagtail.blocks import StreamValue

from .cap import build_area_info_blocks


class CreateAlertFromGeometryView(CreateView):
    """
    Wagtail page CreateView that opens the standard 'add CAP alert' editor with the
    Alert Information area pre-filled from a GeoJSON geometry.

    The MapViewer submits the geometry via POST (a hidden form targeting a new
    tab) to avoid GET URL length limits; a GET fallback is kept for manual
    testing. In both cases nothing is written to the database — POST here only
    re-renders the prefilled add form, it does NOT run the CreateView create
    logic. Saving/publishing happens through the normal Wagtail add page flow
    (the rendered form posts to ``wagtailadmin_pages:add`` with its own CSRF
    token), so all validation and the usual field prefills apply as normal.
    """

    def _prefilled_form_response(self, request):
        info_blocks = build_area_info_blocks(request)
        if info_blocks:
            self.page.info = StreamValue(
                self.page.info.stream_block, info_blocks, is_lazy=True
            )
        return super().get(request)

    def get(self, request):
        return self._prefilled_form_response(request)

    def post(self, request):
        # Render the prefilled form; deliberately NOT super().post() (no create).
        return self._prefilled_form_response(request)


@csrf_exempt
@login_required
def create_alert_from_geometry(request):
    """
    Entry point used by the MapViewer 'Create CAP alert' button. Resolves the CAP
    alert list page and renders the pre-filled add form via
    :class:`CreateAlertFromGeometryView`. Permissions are enforced by the underlying
    Wagtail CreateView (``can_add_subpage``).

    The geometry is submitted as the ``geometry`` form field (POST body, URL-encoded
    GeoJSON) so large polygons don't hit GET URL length limits; a GET ``geometry``
    query param is still accepted for manual testing. A bare geometry, a Feature or a
    FeatureCollection is accepted. An optional ``areaDesc`` field is used as the area
    description.

    ``csrf_exempt`` is safe here: this view only renders the prefilled add form and
    writes nothing to the database (``@login_required`` still applies), while the
    actual page creation posts to the CSRF-protected ``wagtailadmin_pages:add``.
    """
    from capcomposer.cap.models import CapAlertListPage

    cap_list_page = CapAlertListPage.objects.live().first()

    if not cap_list_page:
        return HttpResponseBadRequest(
            _("No CAP alert list page found. Please create one before adding alerts.")
        )

    return CreateAlertFromGeometryView.as_view()(
        request,
        content_type_app_name="cap",
        content_type_model_name="capalertpage",
        parent_page_id=cap_list_page.id,
    )
