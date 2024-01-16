from django.core.mail import mail_admins
from django.db import models
from django.template.defaultfilters import truncatechars
from django.template.response import TemplateResponse
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import MultiFieldPanel, FieldRowPanel, FieldPanel, InlinePanel
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from wagtailcaptcha.forms import remove_captcha_field
from wagtailcaptcha.models import WagtailCaptchaEmailForm

from base.mixins import MetadataPageMixin
from pages.contact.utils import get_duplicates


class DataRequestPage(MetadataPageMixin, WagtailCaptchaEmailForm):
    required_css_class = 'required'

    template = 'datarequest.html'
    parent_page_types = ['home.HomePage']
    subpage_types = []
    max_count = 1
    show_in_menus_default = True
    landing_page_template = 'form_thank_you_landing.html'

    introduction_title = models.TextField()
    introduction_subtitle = models.TextField(blank=True, null=True)
    illustration_image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name="Illustration Image",
        help_text="Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    thank_you_text = models.TextField(blank=True, null=True)

    content_panels = AbstractEmailForm.content_panels + [
        FieldPanel("introduction_title"),
        FieldPanel("introduction_subtitle"),
        FieldPanel('illustration_image'),
        InlinePanel('datarequest_form_fields', label="Form fields"),
        FieldPanel('thank_you_text'),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('from_address', classname="col6"),
                FieldPanel('to_address', classname="col6"),
            ]),
            FieldPanel('subject'),
        ], "Email"),
    ]

    def get_form_fields(self):
        return self.datarequest_form_fields.all()

    def get_form_class(self):
        form_class = super(DataRequestPage, self).get_form_class()
        form_class.required_css_class = 'required'
        return form_class

    def save(self, *args, **kwargs):
        if not self.search_description and self.introduction_subtitle:
            # Limit the search meta desc to google's 160 recommended chars
            self.search_description = truncatechars(self.introduction_subtitle, 160)
        return super().save(*args, **kwargs)

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
                    form_submission = self.process_form_submission(form)
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

    def process_suspicious_form(self, form):
        remove_captcha_field(form)
        try:
            self.send_suspicious_form_to_admin(form)
        except Exception:
            pass

    def send_suspicious_form_to_admin(self, form):
        content = []
        for field in form:
            value = field.value()
            if isinstance(value, list):
                value = ', '.join(value)
            content.append('{}: {}'.format(field.label, value))
        content = '\n'.join(content)
        mail_admins("POSSIBLE SPAM (DATA REQUEST PAGE)- {}".format(self.subject), content, fail_silently=True)


class DataRequestFormField(AbstractFormField):
    page = ParentalKey(DataRequestPage, on_delete=models.CASCADE, related_name="datarequest_form_fields")
