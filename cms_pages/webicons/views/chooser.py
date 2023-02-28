from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from wagtail.admin.auth import PermissionPolicyChecker
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail import hooks
from wagtail.models import Collection
from wagtail.search import index as search_index

from cms_pages.webicons.forms import WebIconForm
from cms_pages.webicons.models import WebIcon
from cms_pages.webicons.permissions import permission_policy

permission_checker = PermissionPolicyChecker(permission_policy)

CHOOSER_PAGE_SIZE = getattr(settings, 'WAGTAILIMAGES_CHOOSER_PAGE_SIZE', 12)


def get_chooser_js_data():
    """construct context variables needed by the chooser JS"""
    return {
        'step': 'chooser',
        'error_label': ("Server Error"),
        'error_message': ("Report this error to your webmaster with the following information:"),
        'tag_autocomplete_url': reverse('wagtailadmin_tag_autocomplete'),
    }


def get_icon_result_data(icon):
    """
    helper function: given an icon, return the json data to pass back to the
    icon chooser panel
    """

    return {
        'id': icon.id,
        'edit_link': reverse('webicons:edit', args=(icon.id,)),
        'title': icon.title,
        'preview': {
            'url': icon.url,
        }
    }


def get_chooser_context(request):
    """Helper function to return common template context variables for the main chooser view"""

    collections = Collection.objects.all()
    if len(collections) < 2:
        collections = None

    return {
        'searchform': SearchForm(),
        'is_searching': False,
        'query_string': None,
        'will_select_format': request.GET.get('select_format'),
        'collections': collections,
    }


def chooser(request):
    if permission_policy.user_has_permission(request.user, 'add'):
        uploadform = WebIconForm(user=request.user, prefix='icon-chooser-upload')
    else:
        uploadform = None

    icons = WebIcon.objects.order_by('-created_at')

    # allow hooks to modify the queryset
    for hook in hooks.get_hooks('construct_icon_chooser_queryset'):
        icons = hook(icons, request)

    if (
            'q' in request.GET or 'p' in request.GET
            or 'collection_id' in request.GET
    ):
        # this request is triggered from search or pagination';
        # we will just render the results.html fragment
        collection_id = request.GET.get('collection_id')
        if collection_id:
            icons = icons.filter(collection=collection_id)

        searchform = SearchForm(request.GET)
        if searchform.is_valid():
            q = searchform.cleaned_data['q']

            icons = icons.search(q)
            is_searching = True
        else:
            is_searching = False
            q = None

        # Pagination
        paginator = Paginator(icons, per_page=CHOOSER_PAGE_SIZE)
        icons = paginator.get_page(request.GET.get('p'))

        return render(request, "webicons/chooser/results.html", {
            'icons': icons,
            'is_searching': is_searching,
            'query_string': q,
        })
    else:
        paginator = Paginator(icons, per_page=CHOOSER_PAGE_SIZE)
        icons = paginator.get_page(request.GET.get('p'))

        context = get_chooser_context(request)
        context.update({
            'icons': icons,
            'uploadform': uploadform,
        })
        return render_modal_workflow(
            request, 'webicons/chooser/chooser.html', None, context,
            json_data=get_chooser_js_data()
        )


def icon_chosen(request, icon_id):
    icon = get_object_or_404(WebIcon, id=icon_id)

    return render_modal_workflow(
        request, None, None,
        None, json_data={'step': 'icon_chosen', 'result': get_icon_result_data(icon)}
    )


@permission_checker.require('add')
def chooser_upload(request):
    if request.method == 'POST':
        icon = WebIcon(uploaded_by_user=request.user)
        form = WebIconForm(
            request.POST, request.FILES, instance=icon, user=request.user, prefix='icon-chooser-upload'
        )

        if form.is_valid():
            # Set image file size
            icon.file_size = icon.file.size

            # Set image file hash
            icon.file.seek(0)
            icon._set_file_hash(icon.file.read())
            icon.file.seek(0)

            form.save()

            # Reindex the image to make sure all tags are indexed
            search_index.insert_or_update_object(icon)

            # return the icon details now
            return render_modal_workflow(
                request, None, None,
                None, json_data={'step': 'icon_chosen', 'result': get_icon_result_data(icon)}
            )
    else:
        form = WebIconForm(user=request.user, prefix='icon-chooser-upload')

    icons = WebIcon.objects.order_by('-created_at')

    # allow hooks to modify the queryset
    for hook in hooks.get_hooks('construct_icon_chooser_queryset'):
        icons = hook(icons, request)

    paginator = Paginator(icons, per_page=CHOOSER_PAGE_SIZE)
    icons = paginator.get_page(request.GET.get('p'))

    context = get_chooser_context(request)
    context.update({
        'icons': icons,
        'uploadform': form,
    })
    return render_modal_workflow(
        request, 'webicons/chooser/chooser.html', None, context,
        json_data=get_chooser_js_data()
    )
