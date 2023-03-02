import datetime
import json
from collections import OrderedDict
from itertools import chain

from dateutil.parser import isoparse
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import mail_managers
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.forms import CheckboxSelectMultiple
from django.template.defaultfilters import truncatechars
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel
from timezone_field import TimeZoneField
from wagtail.admin.panels import (FieldPanel, InlinePanel, MultiFieldPanel, PageChooserPanel,)
from wagtail.admin.panels import TabbedInterface, ObjectList 
from wagtail.admin.mail import send_mail
from wagtail.api import APIField
from wagtail.contrib.forms.forms import WagtailAdminFormPageForm
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from wagtail.fields import StreamField, RichTextField
from wagtail.models import Page
from wagtail.signals import page_published
from wagtail.snippets.models import register_snippet
from wagtail.utils.decorators import cached_classmethod
from wagtailcaptcha.models import WagtailCaptchaEmailForm

from cms_pages.mailchimper.intergration_models import MailchimpSubscriberIntegrationForm   
from cms_pages.wagtailzoom.intergration_models import ZoomMeetingIntegrationForm, ZoomEventsModel
from cms_pages.wagtailzoom.models import ZoomBatchRegistration

from core import blocks 
from core.models import EventType
from core.utils import get_pytz_gmt_offset_str
from core.utils import get_years, paginate, query_param_to_list, get_first_non_empty_p_string, get_object_or_none
from organisation_pages.events.blocks import PanelistBlock, EventSponsorBlock, SessionBlock
from .views import CustomSubmissionsListView

SUMMARY_RICHTEXT_FEATURES = getattr(settings, "SUMMARY_RICHTEXT_FEATURES")


class EventIndexPage(Page):
    template = 'event_index_page.html'
    subpage_types = ['events.EventPage']
    parent_page_types = ['home.HomePage']
    max_count = 1
    show_in_menus = True

    banner_image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name="Banner Image",
        help_text="A high quality image related to your organisation events/trainings",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    banner_title = models.CharField(max_length=255)
    banner_subtitle = models.CharField(max_length=255)

    call_to_action_button_text = models.CharField(max_length=100, blank=True, null=True)
    call_to_action_related_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    events_per_page = models.PositiveIntegerField(default=6, validators=[
        MinValueValidator(6),
        MaxValueValidator(20),
    ], help_text="How many events should be visible on the all events section ?")

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel('banner_image'),
                FieldPanel('banner_title'),
                FieldPanel('banner_subtitle'),
                FieldPanel('call_to_action_button_text'),
                PageChooserPanel('call_to_action_related_page', )
            ],
            heading="Banner Section",
        ),
        MultiFieldPanel(
            [
                FieldPanel('events_per_page'),
            ],
            heading="Other Settings",
        ), ]

    @property
    def filters(self):
        event_types = EventType.objects.all()

        return {'event_types': event_types, 'year': get_years(), }

    def get_featured_event(self):

        queryset = self.all_events.filter(is_archived=False)

        featured_event = queryset.filter(featured=True).first()

        if featured_event:
            return featured_event
        else:
            featured_event = queryset.first()

        return featured_event

    def filter_events(self, request):
        events = self.all_events

        years = query_param_to_list(request.GET.get("year"))
        event_types = query_param_to_list(request.GET.get("event_type"))
        archive = request.GET.get("archive")

        is_archived = False
        # events in the past
        if archive == "True":
            is_archived = True

        filters = models.Q()

        filters &= models.Q(is_archived=is_archived)

        if years:
            filters &= models.Q(date_from__year__in=years)
        if event_types:
            filters &= models.Q(event_type__in=event_types)

        return events.filter(filters)

    def filter_and_paginate_events(self, request):
        page = request.GET.get('page')

        filtered_events = self.filter_events(request)

        paginated_events = paginate(filtered_events, page, self.events_per_page)

        return paginated_events

    @property
    def all_events(self):
        return EventPage.objects.live().filter(is_hidden=False).order_by('-date_from')

    def get_context(self, request, *args, **kwargs):
        context = super(EventIndexPage, self).get_context(
            request, *args, **kwargs)

        context['featured_event'] = self.get_featured_event()

        context['events'] = self.filter_and_paginate_events(request)

        return context

    def save(self, *args, **kwargs):
        # if not self.search_image and self.banner_image:
        #     self.search_image = self.banner_image
        if not self.search_description and self.banner_subtitle:
            # Limit the search meta desc to google's 160 recommended chars
            self.search_description = truncatechars(self.banner_subtitle, 160)
        return super().save(*args, **kwargs)


class EventPage( Page, ZoomEventsModel):
    IMAGE_PLACEMENT_CHOICES = (
        ('side', "Side by Side with Text"),
        ('top', "At the top before text"),
    )

    MEETING_PLATFORM_CHOICES = (
        ('zoom', 'Zoom'),
    )

    template = 'event_page.html'
    parent_page_types = ['events.EventIndexPage', ]
    subpage_types = ['events.EventRegistrationPage']

    event_type = models.ForeignKey(EventType, on_delete=models.PROTECT)
    category = ParentalManyToManyField('core.ServiceCategory', verbose_name="Service Categories")
    projects = ParentalManyToManyField('projects.ProjectPage', blank=True, verbose_name="Relevant Projects")
    date_from = models.DateTimeField(verbose_name="Event begin date",
                                     help_text="Day of the event. If multi-day, then this should be the first day")
    date_to = models.DateTimeField(blank=True, null=True,
                                   verbose_name="End date - Note: Not Required if this is a one day Event",
                                   help_text="Not required if this is a one day event")
    timezone = TimeZoneField(default='Africa/Nairobi', help_text="Timezone", choices_display="WITH_GMT_OFFSET",  use_pytz=True)

    location = models.CharField(max_length=100, help_text="Where will the event take place ?")
    cost = models.CharField(max_length=100, blank=True, null=True,
                            help_text="What is the cost for participating in this event ? Leave blank if free")
    description = RichTextField(help_text="A description of the event ", features=SUMMARY_RICHTEXT_FEATURES)
    agenda_document = models.ForeignKey(
        'core.CustomDocumentModel',
        verbose_name="Downloadable agenda document",
        help_text="Agenda document, preferably in PDF format",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name="Event Image",
        help_text="An image for this event, can be a poster or any relevant image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    image_placement = models.CharField(max_length=50, choices=IMAGE_PLACEMENT_CHOICES, default='top')
    form_template = models.ForeignKey('events.EventRegistrationFormTemplate', on_delete=models.SET_NULL, blank=True,
                                      null=True, default=1)

    featured = models.BooleanField(
        default=False,
        help_text="Show this event in the events landing page as featured ?", )

    is_hidden = models.BooleanField(
        default=False,
        help_text="Make this event hidden in events page or elsewhere", )

    is_visible_on_homepage = models.BooleanField(
        default=False,
        help_text="Show this event on the homepage ?", )

    panelists = StreamField([
        ('panelist', PanelistBlock()),
    ], null=True, blank=True, use_json_field=True)

    sessions = StreamField([
        ('session', SessionBlock()),
    ], null=True, blank=True, use_json_field=True)

    additional_materials = StreamField([
        ('additional_material', blocks.AdditionalMaterialBlock()),
    ], null=True, blank=True, use_json_field=True)
    sponsors = StreamField([
        ('sponsor', EventSponsorBlock()),
    ], null=True, blank=True, verbose_name="Acknowledgement/sponsors", use_json_field=True)

    is_archived = models.BooleanField(default=False)
    registration_open = models.BooleanField(default=True)
    youtube_video_id = models.CharField(max_length=100, blank=True,
                                        help_text="Youtube Video ID if the event is being livestreamed")
    meeting_platform = models.CharField(verbose_name="Meeting Registration Integration Platform",
                                        max_length=100,
                                        blank=True, choices=MEETING_PLATFORM_CHOICES,
                                        help_text="Platform for Event", default="zoom")

    content_panels = Page.content_panels + [
        FieldPanel('event_type'),
        FieldPanel('category', widget=CheckboxSelectMultiple),
        FieldPanel('projects', widget=CheckboxSelectMultiple),
        FieldPanel('date_from'),
        FieldPanel('date_to'),
        FieldPanel('timezone'),
        FieldPanel('description'),
        FieldPanel('agenda_document'),
        FieldPanel('image'),
        # SnippetChooserPanel('form_template'), Do not allow editing because it is misused
        FieldPanel('location'),
        FieldPanel('cost'),
        # FieldPanel('meeting_platform'), Hide this too for now since we dont use other integration platform but zoom
        FieldPanel('panelists'),
        FieldPanel('sessions'),
        FieldPanel('additional_materials'),
        FieldPanel('registration_open'),
        FieldPanel('featured'),
        FieldPanel('is_hidden'),
        FieldPanel('is_visible_on_homepage'),
        FieldPanel('sponsors'),
        # FieldPanel('youtube_video_id'),
    ]

    api_fields = [
        APIField('event_type'),
        APIField('category'),
        APIField('projects'),
        APIField('date_from'),
        APIField('date_to'),
        APIField('description'),
        APIField('image'),
        APIField('location'),
        APIField('cost'),
        APIField('additional_materials'),
    ]

    zoom_events_panel = [
        MultiFieldPanel(
            ZoomEventsModel.panels,
            heading="Zoom Events Settings",
        ),
    ]

    # This is where all the tabs are created
    edit_handler = TabbedInterface(
        [
            ObjectList(content_panels, heading='Content'),
            ObjectList(Page.promote_panels, heading=_('SEO'), classname="seo"),
            ObjectList(Page.settings_panels, heading=_('Settings'), classname="settings"),
            ObjectList(zoom_events_panel, heading='Zoom Events Settings'),
        ]
    )

    class Meta:
        ordering = ['-date_from', ]

    @property
    def count_down(self):
        if self.date_to:
            days = (self.date_from - timezone.now()).days

            if days > 0:
                return days

        return None

    @cached_property
    def registration_page(self):
        return self.get_first_child()

    @cached_property
    def sessions_data(self):
        sessions_list = list(self.sessions)
        sessions_list.sort(key=lambda s: s.value.get("start_time"))

        sessions_by_date = {}

        for session in sessions_list:
            start_time = session.value.get("start_time")
            st = start_time.strftime('%I:%M %p')
            ct = f"{st}"
            session_date = start_time.date()

            if sessions_by_date.get(session_date) is None:
                sessions_by_date[session_date] = {}
                sessions_by_date[session_date][ct] = [session]
            else:
                if sessions_by_date[session_date].get(ct) is None:
                    sessions_by_date[session_date][ct] = [session]
                else:
                    sessions_by_date[session_date][ct].append(session)

        return sessions_by_date

    @cached_property
    def event_title(self):
        return self.title

    @cached_property
    def is_ended(self):
        end_date = self.date_to
        if not end_date:
            end_date = self.date_from
        return timezone.now() > end_date

    @cached_property
    def in_progress(self):
        start_date = self.date_from
        end_date = self.date_to

        if start_date and end_date:
            return start_date < timezone.now() < end_date

        return None

    @cached_property
    def tz_gmt_offset(self):
        return get_pytz_gmt_offset_str(self.timezone)

    def save(self, *args, **kwargs):
        # if not self.search_image and self.image:
        #     self.search_image = self.image
        if not self.search_description and self.description:
            p = get_first_non_empty_p_string(self.description)
            if p:
                # Limit the search meta desc to google's 160 recommended chars
                self.search_description = truncatechars(p, 160)
        return super().save(*args, **kwargs)


# Custom page form to enable using a template to pre-populate  form fields
class EventPageCustomForm(WagtailAdminFormPageForm):
    # Override the __init__ function to update 'initial' form values
    def __init__(self, data=None, files=None, parent_page=None, *args, **kwargs):
        # update the kwargs BEFORE the init of the super form class
        instance = kwargs.get('instance')

        # only update the initial value when creating a new page
        if not instance.id:
            # check if we have parent page and parent page has form template selected
            if parent_page and parent_page.form_template:

                form_template = parent_page.form_template

                template_form_fields = form_template.form_fields.all()

                registration_form_fields = []

                for template_form_field in template_form_fields:
                    template_field_obj = template_form_field.to_dict()

                    reg_field = EventRegistrationFormField(**template_field_obj)
                    registration_form_fields.append(reg_field)

                instance.registration_form_fields = registration_form_fields
                instance.validation_field = form_template.validation_field

            # Ensure you call the super class __init__
        super(EventPageCustomForm, self).__init__(data, files, *args, **kwargs)
        self.parent_page = parent_page


class EventRegistrationPage(WagtailCaptchaEmailForm, MailchimpSubscriberIntegrationForm, ZoomMeetingIntegrationForm):
    base_form_class = EventPageCustomForm
    submissions_list_view_class = CustomSubmissionsListView

    template = 'event_registration_page.html'
    landing_page_template = 'form_thank_you_landing.html'
    parent_page_types = ['events.EventPage']
    subpage_types = []
    max_count_per_parent = 1

    additional_information = models.TextField(blank=True, null=True,
                                              help_text="Optional Additional information/details",
                                              verbose_name="Additional Information - (Optional)")
    registration_limit = models.PositiveIntegerField(blank=True, null=True,
                                                     help_text="Number of available registrations",
                                                     verbose_name="Registration Limit - "
                                                                  "(Leave blank if no limit)")

    thank_you_text = models.TextField(blank=True, null=True,
                                      help_text="Text to display after successful submission")
    validation_field = models.CharField(max_length=100, blank=True,
                                        help_text="A field on the form to check if is already submitted so as to "
                                                  "prevent multiple submissions by one person. This is usually the "
                                                  "email address field in snake casing format", default="email_address")

    send_confirmation_email = models.BooleanField(default=False,
                                                  help_text="Should we send a confirmation/follow up email ?")
    email_field = models.CharField(max_length=100, blank=True,
                                   help_text="The field in the form that corresponds to the email to use. "
                                             "Should be snake_cased")
    email_confirmation_message = RichTextField(features=SUMMARY_RICHTEXT_FEATURES, blank=True,
                                               help_text="Message to send to the user. For example zoom links")
    batch_zoom_reg_enabled = models.BooleanField(default=False,
                                                 verbose_name="Batch Zoom Registration Enabled - "
                                                              "Leave unchecked for direct zoom registrations",
                                                 help_text="Enable batch option for adding registrants to zoom later")

    content_panels = AbstractEmailForm.content_panels + [
        FieldPanel('additional_information'),
        # FieldPanel('registration_limit'),
        InlinePanel('registration_form_fields', label="Form fields"),
        FieldPanel('validation_field'),

        MultiFieldPanel([
            FieldPanel('to_address', heading="Email addresses"),
            FieldPanel('subject'),
        ], "Staff Email Notification Settings - When someone registers"),

        # MultiFieldPanel([
        #     FieldPanel('send_confirmation_email'),
        #     FieldPanel('email_field'),
        #     FieldPanel('email_confirmation_message'),
        # ], "Confirmation Email Settings - Confirmation / follow up email to the user after registration"),

        FieldPanel('thank_you_text', heading="Message to show on website after suscessful submission"),

        # FieldPanel('batch_zoom_reg_enabled'), // Hide this for now TODO: Do we still need it ?
    ]

    @cached_property
    def event(self):
        return self.get_parent().specific

    @cached_classmethod
    def get_edit_handler(cls):
        """
        Override to "lazy load" the panels overriden by subclasses.
        """

        panels = [
            ObjectList(cls.content_panels, heading=_('Content')),
            ObjectList(cls.promote_panels, heading=_('SEO'), classname="seo"),
            ObjectList(cls.settings_panels, heading=_('Settings'), classname="settings"),
        ]

        if cls.integration_panels:
            panels.append(ObjectList(
                cls.integration_panels,
                heading='Mailchimp Integration',
                classname='mailchimp-integration'
            ))

        if cls.zoom_integration_panels:
            panels.append(ObjectList(
                cls.zoom_integration_panels,
                heading='Zoom Integration',
                classname='zoom-integration'
            ))

        return TabbedInterface(panels).bind_to_model(model=cls)

    def get_form_fields(self):
        return self.registration_form_fields.all()

    def get_data_fields(self):
        data_fields = super().get_data_fields()
        meeting_platform = self.event.meeting_platform

        if meeting_platform == "zoom" and self.enable_adding_registrants:
            data_fields.append(('added_to_zoom', _('Added to Zoom')), )

        return data_fields

    def get_form_class(self):
        form_class = super(EventRegistrationPage, self).get_form_class()
        form_class.required_css_class = 'required'
        return form_class

    def should_process_form(self, request, form_data):
        should_process = True
        if self.validation_field:
            validation_field = self.validation_field.replace('-', '_')
            submission_class = self.get_submission_class()
            form_validation_value = form_data.get(validation_field)
            if form_validation_value:
                queryset = submission_class.objects.filter(form_data__icontains=form_validation_value, page=self)
                if queryset.exists():
                    message = "The registration with {} - {} had already been submitted. " \
                              "This means you are already added to the list. " \
                              "Contact us if you think this is a mistake.".format(
                        validation_field.replace('_', ' '),
                        form_validation_value)
                    messages.add_message(request, messages.ERROR, message)

                    # We have a duplicate. Do not continue to process form
                    should_process = False
            else:
                # send managers an email so that they check that a correct field is set
                mail_managers(subject="Incorrect form validation field found !",
                              message="We found an incorrect validation field  - {} - set for the form page {}. Please "
                                      "make sure the correct field is set to avoid duplicate submissions and "
                                      "stop these messages from being sent".format(self.validation_field,
                                                                                   self.title),
                              fail_silently=True)

                # save the submission meanwhile
                should_process = True
        return should_process

    def post_process_submission(self, form, form_submission):
        meeting_platform = self.event.meeting_platform

        if meeting_platform is not None:
            if meeting_platform == "zoom" and self.enable_adding_registrants:
                success, response = self.zoom_integration_operation(self, form=form)
                # Mark submission as success. Usefull for counting successful zoom registrations
                if success:
                    form_data = json.loads(form_submission.form_data)
                    # add custom tracking field
                    form_data['added_to_zoom'] = True
                    form_data = json.dumps(form_data, cls=DjangoJSONEncoder)
                    form_submission.form_data = form_data
                    form_submission.save()

           
        if self.send_confirmation_email and self.email_field and self.email_confirmation_message:
            form_data = form.cleaned_data
            email = form_data.get(self.email_field.replace('-', '_'))

            if email:
                send_mail("Registration Confirmation", '', [email], fail_silently=True,
                          html_message=self.email_confirmation_message)

    def save(self, *args, **kwargs):
        parent = self.get_parent().specific

        # Get meta items from parent
        if parent.search_description:
            self.search_description = parent.search_description
        # if parent.search_image:
        #     self.search_image = parent.search_image

        return super().save(*args, **kwargs)


class EventRegistrationFormField(AbstractFormField):
    page = ParentalKey(EventRegistrationPage,
                       on_delete=models.CASCADE,
                       related_name="registration_form_fields")


@register_snippet
class EventRegistrationFormTemplate(ClusterableModel):
    template_name = models.CharField(max_length=200)
    validation_field = models.CharField(max_length=200, default='email_address')

    panels = [
        FieldPanel('template_name'),
        InlinePanel('form_fields', label="Form fields"),
        FieldPanel('validation_field'),
    ]

    def __str__(self):
        return self.template_name


class EventRegistrationFormTemplateField(AbstractFormField):
    form_template = ParentalKey(EventRegistrationFormTemplate, on_delete=models.CASCADE, related_name="form_fields")

    EXCLUDE = ['id', 'clean_name', 'form_template']

    def to_dict(self):
        opts = self._meta
        data = {}
        for f in chain(opts.concrete_fields):
            if f.name not in self.EXCLUDE:
                data[f.name] = f.value_from_object(self)
        return data


def on_event_published(sender, **kwargs):
    event_page = kwargs['instance']

    if event_page.zoom_events_id:
        cache.delete(f'zoom-events-{event_page.zoom_events_id}')


def on_event_reg_published(sender, **kwargs):
    event_reg_page = kwargs['instance']

    if event_reg_page.batch_zoom_reg_enabled and event_reg_page.can_add_to_zoom():
        zoom_batch = ZoomBatchRegistration.objects.get_or_create(event_registration_page=event_reg_page)
    else:
        zoom_batch = get_object_or_none(ZoomBatchRegistration, event_registration_page=event_reg_page)
        if zoom_batch:
            zoom_batch.delete()
            zoom_batch = None


page_published.connect(on_event_published, sender=EventPage)
page_published.connect(on_event_reg_published, sender=EventRegistrationPage)