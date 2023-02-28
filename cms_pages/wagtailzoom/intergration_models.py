import json

from django.core.cache import cache
from django.db import models
from django.forms.widgets import Input
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.contrib.forms.models import AbstractForm
from django.template import Context, Template

from cms_pages.wagtailzoom.api import ZoomApi, ZoomEventsApi
from core.mail import mail_developers
from datetime import datetime


class ZoomMeetingIntegrationWidget(Input):
    template_name = 'zoom_integration_widget.html'
    js_template_name = 'zoom_integration_js.html'

    def get_context(self, name, value, attrs):
        ctx = super(ZoomMeetingIntegrationWidget, self).get_context(name, value, attrs)

        json_value = self.get_zoom_json_value(value)
        ctx['widget']['value'] = json.dumps(json_value)
        ctx['widget']['extra_js'] = self.render_js(name, json_value)
        ctx['widget']['event_id'] = self.get_stored_event_id(json_value)

        return ctx

    def render_js(self, name, json_value):
        ctx = {
            'widget_name': name,
            'widget_js_name': name.replace('-', '_'),
        }

        return render_to_string(self.js_template_name, ctx)

    def get_zoom_json_value(self, value):
        if value:
            json_value = json.loads(value)
        else:
            json_value = json.loads('{}')
        if 'event_id' not in json_value:
            json_value['event_id'] = ""
        if 'email_field' not in json_value:
            json_value['email_field'] = ""
        if 'first_name_field' not in json_value:
            json_value['first_name_field'] = ""
        if 'last_name_field' not in json_value:
            json_value['last_name_field'] = ""
        return json_value

    def get_stored_event_id(self, value):
        if 'event_id' in value:
            return value['event_id']
        return ""


class ZoomMeetingIntegrationForm(AbstractForm, models.Model):
    class Meta:
        abstract = True

    zoom_json_data = models.TextField(
        blank=True,
        verbose_name=_("Zoom Settings")
    )

    enable_adding_registrants = models.BooleanField(default=False,
                                                    verbose_name="Enable registrations - Note: Works for zoom "
                                                                 "meetings or webinars with Registration enabled ",
                                                    help_text="Check to enable zoom integration")
    is_webinar = models.BooleanField(default=False,
                                     verbose_name="Is this a zoom webinar ? Leave unchecked if meeting",
                                     help_text="Is this a webinar ? Leave unchecked for meetings ")

    zoom_integration_panels = [
        FieldPanel('enable_adding_registrants'),
        FieldPanel('is_webinar'),
        FieldPanel('zoom_json_data', widget=ZoomMeetingIntegrationWidget()),
    ]

    def can_add_to_zoom(self):
        zoom_config = self.get_zoom_data()

        has_req_config = all([zoom_config['event_id'], zoom_config['email_field'], zoom_config['first_name_field'],
                              zoom_config['last_name_field']])

        return zoom_config and has_req_config

    def get_zoom_data(self):
        return json.loads(self.zoom_json_data)

    def get_zoom_event_id(self):
        if 'event_id' in self.get_zoom_data():
            return self.get_zoom_data()['event_id']
        return None

    def get_zoom_email_field_template(self):
        return "{}{}{}".format("{{", self.get_zoom_data()['email_field'], "}}")

    def get_zoom_first_name_field_template(self):
        return "{}{}{}".format("{{", self.get_zoom_data()['first_name_field'], "}}")

    def get_zoom_last_name_field_template(self):
        return "{}{}{}".format("{{", self.get_zoom_data()['last_name_field'], "}}")

    def format_zoom_form_submission(self, form):
        formatted_form_data = {}
        for k, v in form.cleaned_data.items():
            formatted_form_data[k.replace('-', '_')] = v
        return formatted_form_data

    def zoom_integration_operation(self, instance, **kwargs):
        success = False

        response = None

        if self.get_zoom_data()['email_field'] and self.get_zoom_data()['first_name_field'] and \
                self.get_zoom_data()['last_name_field']:

            zoom = ZoomApi()

            if zoom.is_active:
                rendered_dictionary = self.render_zoom_dictionary(
                    self.format_zoom_form_submission(kwargs['form']),
                )

                try:
                    dict_data = json.loads(rendered_dictionary)

                    event_id = self.get_zoom_event_id()

                    if self.is_webinar:
                        response = zoom.add_webinar_registrant(event_id, dict_data)
                    else:
                        response = zoom.add_meeting_registrant(event_id, dict_data)
                    # mark as success
                    success = True
                except Exception as e:
                    # mark as failed
                    success = False

                    data = json.dumps(self.get_zoom_data())

                    if self.is_webinar:
                        event_type = "webinar"
                    else:
                        event_type = "Meeting"

                    message = "Error \n {}\n  Rendered \n {}\n Zoom Form Data\n {}".format(str(e),
                                                                                           str(rendered_dictionary),
                                                                                           str(data))

                    mail_developers(subject="Error when adding user to zoom {} ".format(event_type), message=message)

        return success, response

    def render_zoom_dictionary(self, form_submission):
        rendered_dictionary_template = json.dumps({
            'email': self.get_zoom_email_field_template(),
            'first_name': self.get_zoom_first_name_field_template(),
            'last_name': self.get_zoom_last_name_field_template(),
        })

        rendered_dictionary = Template(rendered_dictionary_template).render(Context(form_submission))
        return rendered_dictionary


class ZoomEventsModel(models.Model):
    zoom_events_id = models.CharField(max_length=255, blank=True, null=True, help_text="Zoom Events Id")
    zoom_events_url = models.URLField(max_length=500, blank=True, null=True,
                                      help_text="URL to the Event's page on Zoom for Registration")

    panels = [
        FieldPanel('zoom_events_id'),
        FieldPanel('zoom_events_url'),
    ]

    class Meta:
        abstract = True

    @cached_property
    def zoom_events_details(self):
        if self.zoom_events_id:
            if cache.get(f'zoom-events-{self.zoom_events_id}'):
                return cache.get(f'zoom-events-{self.zoom_events_id}')

            zoom_events = ZoomEventsApi()

            try:
                sessions_res = zoom_events.get_event_sessions(self.zoom_events_id)
                speakers = zoom_events.get_event_speakers(self.zoom_events_id)
                sponsors = zoom_events.get_event_sponsors(self.zoom_events_id)

                sessions_by_date = {}
                sponsors_by_type = {}

                for session in sessions_res:
                    start_time = session.get("startTime", None)
                    start_time = datetime.fromtimestamp(start_time / 1000)

                    end_time = session.get("endTime", None)
                    end_time = datetime.fromtimestamp(end_time / 1000)

                    session["startTime"] = start_time
                    session["endTime"] = end_time

                    session_date = start_time.date()
                    st = start_time.strftime('%I:%M %p')
                    # et = end_time.strftime('%I:%M %p')
                    ct = f"{st}"

                    if sessions_by_date.get(session_date) is None:
                        sessions_by_date[session_date] = {}
                        sessions_by_date[session_date][ct] = [session]
                    else:
                        if sessions_by_date[session_date].get(ct) is None:
                            sessions_by_date[session_date][ct] = [session]
                        else:
                            sessions_by_date[session_date][ct].append(session)

                sponsor_types_mapping = {
                    "10": "Platinum Sponsors",
                    "20": "Gold Sponsors",
                    "30": "Silver Sponsors"
                }

                for sponsor in sponsors:
                    if sponsor.get("type"):
                        sponsor_type_no = str(sponsor.get("type"))
                        if sponsor_types_mapping.get(sponsor_type_no):
                            sponsor_type_name = sponsor_types_mapping.get(sponsor_type_no)
                            if sponsors_by_type.get(sponsor_type_name):
                                sponsors_by_type.get(sponsor_type_name).append(sponsor)
                            else:
                                sponsors_by_type[sponsor_type_name] = [sponsor]

                details = {
                    "sessions": sessions_by_date,
                    "speakers": speakers,
                    "sponsors": sponsors_by_type
                }

                # set cache
                cache.set(f'zoom-events-{self.zoom_events_id}', details)

                return details
            except Exception as e:
                print(e)
            return None

        return None