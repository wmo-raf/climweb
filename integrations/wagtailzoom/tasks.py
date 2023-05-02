import json

from celery import shared_task
from django.core.serializers.json import DjangoJSONEncoder

from integrations.wagtailzoom.api import ZoomApi
from integrations.wagtailzoom.models import ZoomBatchRegistration
import time
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def batch_register_to_zoom(self, batch_id):
    # get zoom batch reg page
    zoom_batch = ZoomBatchRegistration.objects.get(pk=batch_id)

    logger.info(zoom_batch)

    # get form submissions data
    pending_submissions = zoom_batch.pending_submissions

    total_count = zoom_batch.submissions_count

    event_type = zoom_batch.event_type
    event_id = zoom_batch.event_id

    email_field = zoom_batch.email_field
    first_name_field = zoom_batch.first_name_field
    last_name_field = zoom_batch.last_name_field

    # save this task id
    zoom_batch.task_id = self.request.id
    zoom_batch.save()

    # check if the compulsory zoom form fields mapping is defined
    if email_field and first_name_field:

        zoom = ZoomApi()

        # for each submission
        for i, submission in enumerate(pending_submissions):
            form_data = json.loads(submission.form_data)

            # check if we have email and first_name data, and user not yet added to zoom
            if form_data.get(email_field) and form_data.get(first_name_field):

                zoom_data = {
                    "email": form_data.get(email_field),
                    "first_name": form_data.get(first_name_field)
                }

                if zoom.is_active:
                    try:
                        if event_type == 'Webinar':
                            zoom.add_webinar_registrant(event_id, zoom_data)
                        else:
                            zoom.add_meeting_registrant(event_id, zoom_data)

                        # Mark as added to zoom and save
                        form_data['added_to_zoom'] = True
                        submission.form_data = json.dumps(form_data, cls=DjangoJSONEncoder)
                        submission.save()

                        count = zoom_batch.processed_submissions_count + 1

                        self.update_state(state='PROGRESS',
                                          meta={'processed': count,
                                                "email": zoom_data['email'],
                                                'total': total_count})
                    except Exception as e:
                        print(e)