from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.utils.encoding import force_str
from django.views.decorators.http import require_POST
from django.views.decorators.vary import vary_on_headers
from wagtail.admin.auth import PermissionPolicyChecker
from wagtail.models import Collection
from wagtail.search.backends import get_search_backends

from cms_pages.webicons.forms import WebIconForm
from cms_pages.webicons.models import WebIcon
from cms_pages.webicons.permissions import permission_policy

permission_checker = PermissionPolicyChecker(permission_policy)


@permission_checker.require('add')
@vary_on_headers('X-Requested-With')
def add(request):
    collections = permission_policy.collections_user_has_permission_for(request.user, 'add')
    if len(collections) < 2:
        collections = None

    if request.method == 'POST':
        if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return HttpResponseBadRequest("Cannot POST to this view without AJAX")

        if not request.FILES:
            return HttpResponseBadRequest("Must upload a file")

        # Build a form for validation
        form = WebIconForm({
            'title': request.FILES['files[]'].name,
            'collection': request.POST.get('collection'),
        }, {
            'file': request.FILES['files[]'],
        }, user=request.user)

        if form.is_valid():
            # Save it
            icon = form.save(commit=False)
            icon.uploaded_by_user = request.user
            icon.file_size = icon.file.size
            icon.file.seek(0)
            icon._set_file_hash(icon.file.read())
            icon.file.seek(0)

            icon.save()

            # Success! Send back an edit form for this image to the user
            return JsonResponse({
                'success': True,
                'icon_id': int(icon.id),
                'form': render_to_string('webicons/multiple/edit_form.html', {
                    'icon': icon,
                    'form': WebIconForm(
                        instance=icon, prefix='icon-%d' % icon.id, user=request.user
                    ),
                }, request=request),
            })
        else:
            # Validation error
            return JsonResponse({
                'success': False,
                # https://github.com/django/django/blob/stable/1.6.x/django/forms/util.py#L45
                'error_message': '\n'.join(['\n'.join([force_str(i) for i in v]) for k, v in form.errors.items()]),
            })
    else:
        # Instantiate a dummy copy of the form that we can retrieve validation messages and media from;
        # actual rendering of forms will happen on AJAX POST rather than here
        form = WebIconForm(user=request.user)

        return render(request, 'webicons/multiple/add.html', {
            'max_filesize': form.fields['file'].max_upload_size,
            'help_text': form.fields['file'].help_text,
            'allowed_extensions': ['svg'],
            'error_max_file_size': form.fields['file'].error_messages['file_too_large_unknown_size'],
            'error_accepted_file_types': form.fields['file'].error_messages['invalid_image'],
            'collections': collections,
            'form_media': form.media,
        })


@require_POST
def edit(request, icon_id, callback=None):
    icon = get_object_or_404(WebIcon, id=icon_id)

    if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return HttpResponseBadRequest("Cannot POST to this view without AJAX")

    if not permission_policy.user_has_permission_for_instance(request.user, 'change', icon):
        raise PermissionDenied

    form = WebIconForm(
        request.POST, request.FILES, instance=icon, prefix='icon-' + str(icon_id), user=request.user
    )

    if form.is_valid():
        form.save()

        # Reindex the image to make sure all tags are indexed
        for backend in get_search_backends():
            backend.add(icon)

        return JsonResponse({
            'success': True,
            'icon_id': int(icon_id),
        })
    else:
        return JsonResponse({
            'success': False,
            'icon_id': int(icon_id),
            'form': render_to_string('webicons/multiple/edit_form.html', {
                'icon': icon,
                'form': form,
            }, request=request),
        })


@require_POST
def delete(request, icon_id):
    icon = get_object_or_404(WebIcon, id=icon_id)

    if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return HttpResponseBadRequest("Cannot POST to this view without AJAX")

    if not permission_policy.user_has_permission_for_instance(request.user, 'delete', icon):
        raise PermissionDenied

    icon.delete()

    return JsonResponse({
        'success': True,
        'icon_id': int(icon_id),
    })
