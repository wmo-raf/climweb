import json

from django.contrib.gis.db import models
from django.core.mail import mail_admins
from django.template.response import TemplateResponse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import MultiFieldPanel, FieldRowPanel, FieldPanel, InlinePanel
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from wagtail.fields import RichTextField
from wagtailcaptcha.forms import remove_captcha_field
from wagtailcaptcha.models import WagtailCaptchaEmailForm
from wagtailgeowidget import geocoders
from wagtailgeowidget.helpers import geosgeometry_str_to_struct
from wagtailgeowidget.panels import LeafletPanel, GeoAddressPanel

from climweb.base.mail import send_mail
from climweb.base.mixins import MetadataPageMixin
from climweb.base.seo_utils import get_homepage_meta_image, get_homepage_meta_description
from climweb.base.utils import get_duplicates


class ContactPage(MetadataPageMixin, WagtailCaptchaEmailForm):
    template = 'contact/contact_page.html'
    parent_page_types = ['home.HomePage']
    subpage_types = []
    max_count = 1
    show_in_menus_default = True
    landing_page_template = 'form_thank_you_landing.html'
    
    # don't cache this page because it has a form
    cache_control = 'no-cache'
    
    name = models.CharField(max_length=255, null=True, blank=False, unique=True, verbose_name=_("Location"),
                            help_text=_("Location of organisation"))
    location = models.CharField(max_length=250, blank=False, null=True, verbose_name=_("Coordinates of organisation"),
                                help_text=_("Coordinates of organisation"))
    thank_you_text = RichTextField(blank=True, verbose_name=_("Thank you message"))
    
    @cached_property
    def point(self):
        return json.dumps(geosgeometry_str_to_struct(self.location))
    
    @property
    def lat(self):
        return self.point['y']
    
    @property
    def lng(self):
        return self.point['x']
    
    content_panels = AbstractEmailForm.content_panels + [
        GeoAddressPanel("name", geocoder=geocoders.NOMINATIM),
        LeafletPanel("location", address_field="name"),
        InlinePanel('contact_us_form_fields', label="Form fields"),
        FieldPanel('thank_you_text'),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('from_address', classname="col6"),
                FieldPanel('to_address', classname="col6"),
            ]),
            FieldPanel('subject'),
        ], _("Email")),
    ]
    
    def get_meta_image(self):
        return get_homepage_meta_image(self.get_site())
    
    def get_meta_description(self):
        return get_homepage_meta_description(self.get_site())
    
    def get_form_fields(self):
        return self.contact_us_form_fields.all()
    
    def get_form_class(self):
        form_class = super(ContactPage, self).get_form_class()
        form_class.required_css_class = 'required'
        return form_class
    
    def serve(self, request, *args, **kwargs):
        if request.method == 'POST':
            form = self.get_form(request.POST, request.FILES, page=self, user=request.user)
            
            if form.is_valid():
                form_submission = None
                
                try:
                    # see if we have any duplicated field values. Notorious with spammers !
                    duplicate_fields = get_duplicates(form.cleaned_data)
                except Exception:
                    duplicate_fields = []
                
                if not duplicate_fields:
                    # remove_wagtail_key_field(form)
                    form_submission = self.process_form_submission(form)
                    
                    # Send confirmation email
                    try:
                        self.send_confirmation_email(form.cleaned_data)
                    except Exception:
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
            message = "Thank you for getting in touch!\nWe appreciate you contacting us. Our team will" \
                      "get back to you as soon as possible. Thanks!"
            
            send_mail("Confirmation", message, [email], fail_silently=True, from_email="Contact Us")
    
    def process_suspicious_form(self, form):
        remove_captcha_field(form)
        try:
            self.send_suspicious_form_to_admin(form)
        except Exception as e:
            pass
            
            # override send_mail to extract sender email from form, to use in 'reply_to'
            # This will allow replying to the sender directly from the email client
    
    def send_mail(self, form):
        addresses = [x.strip() for x in self.to_address.split(',')]
        email = form.cleaned_data.get("email", None)
        options = {
            "fail_silently": True,
        }
        if email:
            options["reply_to"] = [email]
        send_mail(self.subject, self.render_email(form), addresses, self.from_address, **options)
    
    def send_suspicious_form_to_admin(self, form):
        content = []
        for field in form:
            value = field.value()
            if isinstance(value, list):
                value = ', '.join(value)
            content.append('{}: {}'.format(field.label, value))
        content = '\n'.join(content)
        
        mail_admins("POSSIBLE SPAM (CONTACT US PAGE) - {}".format(self.subject), content, fail_silently=True)
    
    class Meta:
        verbose_name = _("Contact Page")


class ContactFormField(AbstractFormField):
    page = ParentalKey(ContactPage,
                       on_delete=models.CASCADE,
                       related_name="contact_us_form_fields")
