from django.contrib.gis.db import models
from wagtail.models import Page, Site
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel,FieldRowPanel,InlinePanel,MultiFieldPanel
from wagtailgeowidget.panels import LeafletPanel
from django.utils.functional import cached_property
from django.template.response import TemplateResponse
from django.template.defaultfilters import truncatechars
from wagtailformkey.forms import WagtailCaptchaKeyFormBuilder, remove_wagtail_key_field
from wagtailgeowidget.helpers import geosgeometry_str_to_struct
import json
from django.urls import reverse
from .utils import get_duplicates
from wagtailcaptcha.forms import remove_captcha_field

# Create your models here.
from wagtailcaptcha.models import WagtailCaptchaEmailForm
from wagtail.contrib.forms.models import AbstractEmailForm,AbstractFormField
from modelcluster.fields import ParentalKey
from wagtail.contrib.routable_page.models import RoutablePageMixin, path


from core.mail import send_mail
from site_settings.models import OtherSettings


class FormField(AbstractFormField):
    page = ParentalKey(
        'ContactPage',
        on_delete = models.CASCADE,
        related_name='contact_form_fields'
    )


class ContactPage(WagtailCaptchaEmailForm,RoutablePageMixin):

    template = "contact/contact_page.html"
    max_count = 1


    location = models.CharField(help_text="Location of organisation", blank=False, null=True, max_length=250)
    thank_you_text = RichTextField(blank=True)

    subpage_types = []

    content_panels = AbstractEmailForm.content_panels +[
        MultiFieldPanel([
            LeafletPanel('location' ),

        ],heading="Location"),
        MultiFieldPanel([
        InlinePanel('contact_form_fields', label = 'Form Fields'),
        FieldPanel('thank_you_text'),
    ]),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('from_address', classname="col6"),
                FieldPanel('to_address', classname="col6")
            ]),
            FieldPanel('subject')
        ])
    ]    

    @cached_property
    def point(self):
        return json.dumps(geosgeometry_str_to_struct(self.location))

    @property
    def lat(self):
        return self.point['y']

    @property
    def lng(self):
        return self.point['x']

    class Meta:
        verbose_name = "Contact Page"
        verbose_name_plural = "Contact Pages"
        
    def get_form_fields(self):
        return self.contact_form_fields.all()

    def get_form_class(self):
        form_class = super(ContactPage, self).get_form_class()
        form_class.required_css_class = 'required'
        return form_class

    def save(self, *args, **kwargs):
        if not self.search_description and self.introduction_text:
            # Limit the search meta desc to google's 160 recommended chars
            self.search_description = truncatechars(self.introduction_text, 160)
        return super().save(*args, **kwargs)

    def serve(self, request, *args, **kwargs):
        if request.method == 'POST':
            form = self.get_form(request.POST, request.FILES, page=self, user=request.user)

            if form.is_valid():
                form_submission = None

                # see if we have any duplicated field values. Notorius with spammers !
                dups = get_duplicates(form.cleaned_data)

                # Check if the submitted key matches. This is a strategy to prevent automated submission with js
                wagtail_form_submitted_key = form.cleaned_data.get('wagtailkey')
                wagtail_form_key = OtherSettings.for_site(Site.find_for_request(request)).wagtail_form_key

                if not dups and (wagtail_form_submitted_key == wagtail_form_key):
                    remove_wagtail_key_field(form)
                    form_submission = self.process_form_submission(form)

                    # Send confirmation email
                    try:
                        self.send_confirmation_email(form.cleaned_data)
                    except:
                        pass
                else:
                    self.process_suspicious_form(form)

                return self.render_landing_page(request, form_submission, *args, **kwargs)
        else:
            form = self.get_form(page=self, user=request.user)

        context = self.get_context(request)
        context['form'] = form
        return TemplateResponse(
            request,
            self.get_template(request),
            context
        )

    @staticmethod
    def send_confirmation_email(form):
        email = form.get('email')
        subject = form.get('subject')

        if email and subject:
            message = "Thank you for getting in touch!\nWe appreciate you contacting us about {}. Our team will be " \
                      "getting back to you shortly.\nHave a great day!".format(subject)

            send_mail("Confirmation", message, [email], fail_silently=True, from_email="ORG - Contact Us")

    def process_suspicious_form(self, form):
        remove_captcha_field(form)
        if self.to_address:
            self.send_suspicious_form_to_admin(form)

    def send_mail(self, form):
        addresses = [x.strip() for x in self.to_address.split(',')]
        email = form.cleaned_data.get("email", None)
        options = {}
        if email:
            options["reply_to"] = [email]
        send_mail(self.subject, self.render_email(form), addresses, self.from_address, **options)

    def send_suspicious_form_to_admin(self, form):
        addresses = ['email@email.net']
        content = []
        for field in form:
            value = field.value()
            if isinstance(value, list):
                value = ', '.join(value)
            content.append('{}: {}'.format(field.label, value))
        content = '\n'.join(content)
        send_mail("POSSIBLE SPAM - {}".format(self.subject), content, addresses, self.from_address, )



   