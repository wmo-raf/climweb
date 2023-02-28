from celery.result import AsyncResult
from django.db import models
from django.utils.functional import cached_property
from wagtail.contrib.forms.models import FormSubmission


class ZoomBatchRegistration(models.Model):
    event_registration_page = models.OneToOneField('events.EventRegistrationPage', on_delete=models.CASCADE)
    task_id = models.CharField(max_length=200, blank=True, null=True)
    task_complete = models.BooleanField(default=False)

    def __str__(self):
        return self.event_registration_page.title

    @cached_property
    def submissions(self):
        return FormSubmission.objects.filter(page=self.event_registration_page)

    @cached_property
    def submissions_count(self):
        return self.submissions.count()

    @cached_property
    def event_id(self):
        zoom_data = self.event_registration_page.get_zoom_data()

        event_id = zoom_data.get('event_id', None)

        return event_id

    @cached_property
    def event_type(self):
        is_webinar = self.event_registration_page.is_webinar

        if is_webinar:
            return "Webinar"
        else:
            return "Meeting"

    @cached_property
    def email_field(self):
        zoom_data = self.event_registration_page.get_zoom_data()

        return zoom_data.get('email_field', None)

    @cached_property
    def first_name_field(self):
        zoom_data = self.event_registration_page.get_zoom_data()

        return zoom_data.get('first_name_field', None)

    @cached_property
    def last_name_field(self):
        zoom_data = self.event_registration_page.get_zoom_data()

        return zoom_data.get('last_name_field', None)

    @cached_property
    def latest_status(self):
        if self.task_id:
            result = AsyncResult(self.task_id).state
            return {'state': result.state, 'info': result.info}
        return None

    @property
    def processed_submissions_count(self):
        return self.submissions.filter(form_data__contains='"added_to_zoom": true').count()

    @cached_property
    def pending_submissions(self):
        return self.submissions.exclude(form_data__contains='"added_to_zoom": true')

    @cached_property
    def pending_submissions_count(self):
        return self.pending_submissions.count()