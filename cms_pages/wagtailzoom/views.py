from celery.result import AsyncResult
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.generic import DetailView

from cms_pages.wagtailzoom.forms import ZoomBatchRegistrationForm
from cms_pages.wagtailzoom.models import ZoomBatchRegistration
from cms_pages.wagtailzoom.tasks import batch_register_to_zoom
 

class ZoomEventView(DetailView):
    model = ZoomBatchRegistration
    template_name = "zoom_event_reg_detail.html"
    context_object_name = "event"


@login_required
def run_batch_register(request):
    # request should be ajax and method should be POST.
    if request.is_ajax and request.method == "POST":

        # get the form data
        form = ZoomBatchRegistrationForm(request.POST)
        # save the data and after fetch the object in instance

        if form.is_valid():

            data = form.cleaned_data

            pk = data.get('zoom_reg_page')

            # run batch register
            task = batch_register_to_zoom.delay(pk)

            return JsonResponse({"status": "STARTED", "task_id": task.id}, status=200)

        else:
            # some form errors occured.
            return JsonResponse({"error": form.errors}, status=400)

    # some error occured
    return JsonResponse({"error": ""}, status=400)


@login_required
def get_task_status(request, task_id):
    result = AsyncResult(task_id)

    response = {
        'status': result.state,
        'details': result.info
    }

    return JsonResponse({**response}, status=200)