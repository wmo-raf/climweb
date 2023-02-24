import uuid
from django.utils.functional import cached_property
from django.contrib.gis.db import models
from wagtail.core.models import Page
from wagtail.core.models import Orderable
from modelcluster.fields import ParentalKey
# from Inlinepanel.edit_handlers import InlinePanel
from django.utils.text import slugify

from wagtail.admin.edit_handlers import MultiFieldPanel, FieldPanel, InlinePanel,FieldRowPanel
from .widgets import  BasemapPolygonWidget
        
            
# Create your models here.
class AlertList(Page):
    subpage_types = [
        'capeditor.Alert',  # appname.ModelName
    ]
    parent_page_type = [
        'wagtailcore.Page'  # appname.ModelName
    ]
    

class Alert(Page):

    templates = "alert.html"

    STATUS_CHOICES = (
        ("draft", "Draft - A preliminary template or draft, not actionable in its current form"),
        ("actual", "Actual - Actionable by all targeted recipients"),
        ("test", "Test - Technical testing only, all recipients disregard"),
        ("exercise",
         "Exercise - Actionable only by designated exercise participants; exercise identifier SHOULD appear in note"),
        ("system", "System - For messages that support alert network internal functions"),
    )

    MESSAGE_TYPE_CHOICES = (
        ('alert', "Alert - Initial information requiring attention by targeted recipients"),
        ('update', "Update - Updates and supercedes the earlier message(s) identified in referenced alerts"),
        ('cancel', "Cancel - Cancels the earlier message(s) identified in references"),
        ('ack', "Acknowledge - Acknowledges receipt and acceptance of the message(s) identified in references field"),
        ('error',
         "Error -  Indicates rejection of the message(s) identified in references; explanation SHOULD "
         "appear in note field"),
    )

    SCOPE_CHOICES = (
        ('public', "Public - For general dissemination to unrestricted audiences"),
        ('restricted',
         "Restricted - For dissemination only to users with a known operational requirement as in the restriction field"),
        ('private', "Private - For dissemination only to specified addresses as in the addresses field in the alert"),
    )

    LANGUAGE_CHOICES = (
        ('en', "English"),
    )

    CATEGORY_CHOICES = (
        ('geo', "Geophysical"),
        ('met', "Meteorological"),
        ('safety', "General emergency and public safety"),
        ('security', "Law enforcement, military, homeland and local/private security"),
        ('rescue', "Rescue and recovery"),
        ('fire', "Fire suppression and rescue"),
        ('health', "Medical and public health"),
        ('env', "Pollution and other environmental"),
        ('transport', "Public and private transportation"),
        ('infra', "Utility, telecommunication, other non-transport infrastructure"),
        ('cbrne', "Chemical, Biological, Radiological, Nuclear or High-Yield Explosive threat or attack"),
        ('other', "Other events"),
    )

    URGENCY_CHOICES = (
        ('immediate', "Immediate - Responsive action SHOULD be taken immediately"),
        ('expected', "Expected - Responsive action SHOULD be taken soon (within next hour)"),
        ('future', "Future - Responsive action SHOULD be taken in the near future"),
        ('past', "Past - Responsive action is no longer required"),
        ('unknown', "Unknown - Urgency not known"),
    )

    SEVERITY_CHOICES = (
        ('extreme', "Extreme - Extraordinary threat to life or property"),
        ('severe', "Severe - Significant threat to life or property"),
        ('moderate', "Moderate - Possible threat to life or property"),
        ('minor', "Minor - Minimal to no known threat to life or property"),
        ('unknown', "Unknown - Severity unknown"),
    )

    CERTAINTY_CHOICES = (
        ('observed', "Observed - Determined to have occurred or to be ongoing"),
        ('likely', "Likely - Likely (percentage > ~50%)"),
        ('possible', "Possible - Possible but not likely (percentage <= ~50%)"),
        ('unlikely', "Unlikely - Not expected to occur (percentage ~ 0)"),
        ('unknown', "Unknown - Certainty unknown"),
    )

    identifier = models.UUIDField(default=uuid.uuid4, editable=False,
                                  help_text="Unique ID. Auto generated on creation.")
    sender = models.EmailField(max_length=255,
                              help_text=" Identifies the originator of an alert. "
                                        "This can be an email of the institution for example", default='grace@gmail.com')
    sent = models.DateTimeField(help_text="Time and date of origination of the alert")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES,
                              help_text="The code denoting the appropriate handling of the alert", default='actual')
    message_type = models.CharField(max_length=100, choices=MESSAGE_TYPE_CHOICES,
                                    help_text="The code denoting the nature of the alert message",  default='alert')
    scope = models.CharField(max_length=100,
                             choices=SCOPE_CHOICES,
                             help_text="The code denoting the intended distribution of the alert message",  default='public')
    source = models.TextField(blank=True, null=True, help_text="The text identifying the source of the alert message")
    restriction = models.TextField(blank=True, null=True,
                                   help_text="The text describing the rule for limiting distribution of the "
                                             "restricted alert message. Used when scope value is Restricted")
    code = models.CharField(max_length=100, blank=True, null=True,
                            help_text="The code denoting the special handling of the alert message")
    note = models.TextField(blank=True, null=True,
                            help_text="The text describing the purpose or significance of the alert message."
                                      "The message note is primarily intended for use with "
                                      "<status> 'Exercise' and <msgType> 'Error'")
    language = models.CharField(max_length=100, choices=LANGUAGE_CHOICES, default='en', blank=True, null=True,
                                help_text="The code denoting the language of the alert message")
    category = models.CharField(max_length=100,  default='met',
                                choices=CATEGORY_CHOICES,
                                help_text="The code denoting the category of the subject event of the alert message")
    event = models.CharField(max_length=100,
                             help_text="The text denoting the type of the subject event of the alert message", blank=True, null=True)
    urgency = models.CharField(max_length=100,
                               choices=URGENCY_CHOICES,
                               help_text="The code denoting the urgency of the subject event of the alert message", default="immediate")
    severity = models.CharField(max_length=100,
                                choices=SEVERITY_CHOICES,
                                help_text="The code denoting the severity of the subject event of the alert message", default="extreme")
    certainty = models.CharField(max_length=100,
                                 choices=CERTAINTY_CHOICES,
                                 help_text="The code denoting the certainty of the subject event of the alert message", default="likely")
    audience = models.TextField(blank=True, null=True,
                                help_text="The text describing the intended audience of the alert message")


    # eventCode

    effective = models.DateTimeField(blank=True, null=True,
                                     help_text="The effective time of the information of the alert message")
    onset = models.DateTimeField(blank=True, null=True,
                                 help_text="The expected time of the beginning of the subject event "
                                           "of the alert message")
    expires = models.DateTimeField(blank=True, null=True,
                                   help_text="The expiry time of the information of the alert message")
    headline = models.TextField(blank=True, null=True, help_text="The text headline of the alert message")
    description = models.TextField(blank=True, null=True,
                                   help_text="The text describing the subject event of the alert message")
    instruction = models.TextField(blank=True, null=True,
                                   help_text="The text describing the recommended action to be taken by "
                                             "recipients of the alert message")
    web = models.URLField(blank=True, null=True,
                          help_text="The identifier of the hyperlink associating "
                                    "additional information with the alert message")
    contact = models.TextField(blank=True, null=True,
                               help_text="The text describing the contact for follow-up and "
                                         "confirmation of the alert message")

    # parameter

    # area_desc = models.TextField(help_text="The text describing the affected area of the alert message",
    #                              verbose_name="Affected areas / Regions", blank=True, null=True)
    altitude = models.CharField(max_length=100,
                                blank=True,
                                null=True,
                                help_text="The specific or minimum altitude of the affected area of the alert message")
    ceiling = models.CharField(max_length=100,
                               blank=True,
                               null=True,
                               help_text="The maximum altitude of the affected area of the alert message."
                                         "MUST NOT be used except in combination with the altitude element. ") 

                                                         
    content_panels = Page.content_panels + [

        MultiFieldPanel([
            FieldRowPanel([
            FieldPanel('sender'),
            FieldPanel('sent'),
            ]),
            
            FieldPanel('status',),
            FieldPanel('message_type', classname="message"),
            InlinePanel('references', heading="Earlier Reference Alerts -  If applicable", label="Alert", classname="references"),

            FieldPanel('note', classname='note'),

            FieldPanel('scope'),
            FieldPanel('restriction',classname="restriction" ),
            InlinePanel('addresses', heading="Intended Recipients (If scope is Private) ", label="Recipient", classname="addresses"),


        ], heading="Alert Identification (Sender, Message Type, Scope)", classname="collapsed"),

        MultiFieldPanel([
            FieldRowPanel([
            FieldPanel('language'),
            FieldPanel('event'),

            ]),
            FieldPanel('category'),
            FieldPanel('urgency'),
            FieldPanel('severity'),
            FieldPanel('certainty'),
            InlinePanel('response_types', heading="Response Types ", label="Response Type"),        
            FieldPanel('audience'),
            # FieldPanel('eventCode'),
            FieldRowPanel([
                FieldPanel('effective'),
                FieldPanel('onset'),
            ]),
            FieldPanel('expires'),

            
        ], heading="Alert Categorization (Category, Urgency, Severity, Certainity, Response & Dates)", classname="collapsed"),

        MultiFieldPanel([
            FieldPanel('headline'),
            FieldPanel('description'),
            FieldPanel('instruction'),

            FieldRowPanel([
                FieldPanel('web'),
                FieldPanel('contact'),
            ])
        ], heading ="Alert Delivery Message (Headline, Description, Intsructions, Contact & Website)", classname="collapsed"),

        MultiFieldPanel([
            InlinePanel('alert_areas', label="Alert Area"),
        ], heading="Alert Areas", classname="collapsed"),
        

    #     InlinePanel('incidents', heading="Related Incidents -  If applicable", label="Incident"),


    #     FieldPanel('code'),

    #     # FieldPanel('parameter'),
    #     InlinePanel('resources', heading="Resources ", label="Resource"),

    #     FieldPanel('altitude'),
    #     FieldPanel('ceiling'),
    ]

    subpage_types = [
        # 'capeditor.Alert',  # appname.ModelName
    ]
    parent_page_type = [
        'wagtailcore.Page'  # appname.ModelName
    ]

    # def clean(self):
    #     super().clean()
    #     new_title = f'{self.event} - {self.sent}'
    #     self.title = new_title
    #     self.slug = slugify(new_title)


class AlertAddress(Orderable):
    alert = ParentalKey('Alert', related_name="addresses")
    name = models.TextField(help_text="Name of the recipient")
    address = models.TextField(blank=True, null=True, help_text="Address/Email/Contact")

    def __str__(self):
        return self.name


class AlertReference(Orderable):
    alert = ParentalKey('Alert', related_name='references')
    ref_alert = models.ForeignKey('Alert', blank=True, null=True, on_delete=models.PROTECT,
                                  help_text="Earlier alert referenced by this alert")

    def __str__(self):
        return f'{self.ref_alert.sender},{self.ref_alert.identifier},{self.ref_alert.sent}'


class AlertIncident(Orderable):
    alert = ParentalKey(Alert, related_name='incidents', on_delete=models.CASCADE, )
    title = models.CharField(max_length=255, help_text="Title of the incident referent of the alert")
    description = models.TextField(help_text="Description of the incident")

    def __str__(self):
        return self.title


class AlertResponseType(Orderable):
    RESPONSE_TYPE_CHOICES = (
        ("shelter", "Shelter - Take shelter in place or per instruction"),
        ("evacuate", "Evacuate - Relocate as instructed in the instruction"),
        ("prepare", "Prepare - Relocate as instructed in the instruction"),
        ("execute", "Execute - Execute a pre-planned activity identified in instruction"),
        ("avoid", "Avoid - Avoid the subject event as per the instruction"),
        ("monitor", "Monitor - Attend to information sources as described in instruction"),
        ("assess", "Assess - Evaluate the information in this message - DONT USE FOR PUBLIC ALERTS"),
        ("all_clear",
         "All Clear - The subject event no longer poses a threat or concern and any follow on action is described in instruction"),
        ("None", "No action recommended"),
    )

    alert = ParentalKey('Alert', related_name='response_types')
    response_type = models.CharField(max_length=100, choices=RESPONSE_TYPE_CHOICES,
                                     help_text="The code denoting the type of action recommended for the "
                                               "target audience")


class AlertResource(Orderable):
    alert = ParentalKey('Alert', related_name='resources')
    resource_type = models.CharField(max_length=100, blank=True, null=True,
                                     help_text="Resource type whether is image, file etc")
    resource_desc = models.TextField(help_text="The text describing the type and content of the resource file")
    file = models.ForeignKey(
        'wagtaildocs.Document',
        help_text="File, Document etc",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    link = models.URLField(blank=True, null=True, help_text="The identifier of the hyperlink for the resource file")
    derefUri = models.TextField(blank=True, null=True,
                                help_text="The base-64 encoded data content of the resource file")
    digest = models.TextField(blank=True, null=True,
                              help_text="The code representing the digital digest ('hash') computed "
                                        "from the resource file")

    panels = [
        FieldPanel('resource_type'),
        FieldPanel('resource_desc'),
        FieldPanel('file'),
        FieldPanel('link'),
    ]

    @property
    def mime_type(self):
        return None


    @property
    def size(self):
        return None


class AlertArea(Orderable):
    alert = ParentalKey('Alert', related_name='alert_areas',  on_delete=models.PROTECT)
    area_desc = models.CharField(max_length=100, help_text="The text describing the affected area of the alert message",
                                 verbose_name="Affected areas / Regions",null=True)
   
    area = models.PolygonField(help_text="The paired values of points defining a polygon that delineates the affected "
                                         "area of the alert message", null=True, srid=4326)

                                        
    panels = [
        FieldPanel('area_desc'),
        FieldPanel('area', widget=BasemapPolygonWidget() ),
    ]   


class AlertGeocode(models.Model):
    alert = ParentalKey('Alert', related_name='geocodes')
    name = models.CharField(max_length=100, help_text="Name for the geocode")
    value = models.CharField(max_length=255, help_text="Value of the geocode")
