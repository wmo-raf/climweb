import os

from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.vary import vary_on_headers
from wagtail.admin.forms.search import SearchForm
from wagtail.models import Collection
from wagtail.images.models import SourceImageIOError

from integrations.webicons.forms import WebIconForm
from integrations.webicons.models import WebIcon
from wagtail.search import index as search_index
from wagtail.admin import messages
from wagtail.admin.auth import PermissionPolicyChecker, permission_denied

from integrations.webicons.permissions import permission_policy

permission_checker = PermissionPolicyChecker(permission_policy)


@permission_checker.require_any('add', 'change', 'delete')
@vary_on_headers('X-Requested-With')
def index(request):
    # Get webicons (filtered by user permission)

    webicons = permission_policy.instances_user_has_any_permission_for(
        request.user, ['change', 'delete']
    ).order_by('-created_at')

    # Search
    query_string = None

    if 'q' in request.GET:
        form = SearchForm(request.GET, placeholder=("Search images"))
        if form.is_valid():
            query_string = form.cleaned_data['q']

            webicons = webicons.search(query_string)
    else:
        form = SearchForm(placeholder=("Search images"))

    # Filter by collection
    current_collection = None
    collection_id = request.GET.get('collection_id')
    if collection_id:
        try:
            current_collection = Collection.objects.get(id=collection_id)
            webicons = webicons.filter(collection=current_collection)
        except (ValueError, Collection.DoesNotExist):
            pass

    paginator = Paginator(webicons, per_page=20)
    webicons = paginator.get_page(request.GET.get('p'))

    collections = permission_policy.collections_user_has_any_permission_for(
        request.user, ['add', 'change']
    )
    if len(collections) < 2:
        collections = None

    # Create response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'webicons/icons/results.html', {
            'icons': webicons,
            'query_string': query_string,
            'is_searching': bool(query_string),
        })
    else:
        return render(request, 'webicons/icons/index.html', {
            'icons': webicons,
            'query_string': query_string,
            'is_searching': bool(query_string),
            'search_form': form,
            'collections': collections,
            'current_collection': current_collection,
            'user_can_add': permission_policy.user_has_permission(request.user, 'add'),
        })


@permission_checker.require('add')
def add(request):
    if request.method == 'POST':
        icon = WebIcon()
        form = WebIconForm(request.POST, request.FILES, instance=icon, user=request.user)

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

            messages.success(request, ("Icon '{0}' added.").format(icon.title), buttons=[
                messages.button(reverse('webicons:edit', args=(icon.id,)), ('Edit'))
            ])
            return redirect('webicons:index')
        else:
            messages.error(request, ("The icon could not be created due to errors."))
    else:
        form = WebIconForm(user=request.user)

    return render(request, "webicons/icons/add.html", {
        'form': form,
    })


@permission_checker.require('change')
def edit(request, icon_id):
    icon = get_object_or_404(WebIcon, id=icon_id)

    if not permission_policy.user_has_permission_for_instance(request.user, 'change', icon):
        return permission_denied(request)

    if request.method == 'POST':
        original_file = icon.file

        form = WebIconForm(request.POST, request.FILES, instance=icon, user=request.user)

        if form.is_valid():
            if 'file' in form.changed_data:
                # Set new image file size
                icon.file_size = icon.file.size

                # Set new image file hash
                icon.file.seek(0)
                icon._set_file_hash(icon.file.read())
                icon.file.seek(0)

            form.save()
            if 'file' in form.changed_data:
                # if providing a new image file, delete the old one and all renditions.
                # NB Doing this via original_file.delete() clears the file field,
                # which definitely isn't what we want...
                original_file.storage.delete(original_file.name)

            # Reindex the image to make sure all tags are indexed
            search_index.insert_or_update_object(icon)

            messages.success(request, ("Icon '{0}' updated.").format(icon.title), buttons=[
                messages.button(reverse('webicons:edit', args=(icon.id,)), ('Edit again'))
            ])

            return redirect('webicons:index')
        else:
            messages.error(request, ("The icon could not be saved due to errors."))
    else:
        form = WebIconForm(instance=icon, user=request.user)

    if icon.is_stored_locally():
        # Give error if image file doesn't exist
        if not os.path.isfile(icon.file.path):
            messages.error(request, (
                "The source icon file could not be found. Please change the source or delete the icon."
            ).format(icon.title), buttons=[
                messages.button(reverse('webicons:delete', args=(icon.id,)),('Delete'))
            ])

    try:
        filesize = icon.get_file_size()
    except SourceImageIOError:
        filesize = None

    return render(request, "webicons/icons/edit.html", {
        'icon': icon,
        'form': form,
        'filesize': filesize,
        'user_can_delete': permission_policy.user_has_permission_for_instance(
            request.user, 'delete', icon
        ),
    })


@permission_checker.require('delete')
def delete(request, image_id):
    icon = get_object_or_404(WebIcon, id=image_id)

    if not permission_policy.user_has_permission_for_instance(request.user, 'delete', icon):
        return permission_denied(request)

    if request.method == 'POST':
        icon.delete()
        messages.success(request, ("Icon '{0}' deleted.").format(icon.title))
        return redirect('webicons:index')

    return render(request, "webicons/icons/confirm_delete.html", {
        'icon': icon,
    })
