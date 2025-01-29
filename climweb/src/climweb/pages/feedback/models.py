from django.core.mail import mail_admins
from django.db import models
from django.template.defaultfilters import truncatechars
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import MultiFieldPanel, FieldRowPanel, FieldPanel, InlinePanel
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from wagtailcaptcha.forms import remove_captcha_field
from wagtailcaptcha.models import WagtailCaptchaEmailForm

from climweb.base.mail import send_mail
from climweb.base.mixins import MetadataPageMixin
from climweb.base.utils import get_duplicates


class FeedbackPage(MetadataPageMixin, WagtailCaptchaEmailForm):
    required_css_class = 'required'

    template = 'feedback.html'
    parent_page_types = ['home.HomePage']
    subpage_types = []
    max_count = 1
    show_in_menus_default = True
    landing_page_template = 'form_thank_you_landing.html'

    # don't cache this page because it has a form
    cache_control = 'no-cache'

    introduction_title = models.CharField(verbose_name=_("Introduction Title"))
    introduction_subtitle = models.TextField(blank=True, null=True, verbose_name=_("Introduction Subtitle"))
    illustration = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Illustration")
    )
    thank_you_text = models.TextField(blank=True, null=True, verbose_name=_("Thank you Text"))

    content_panels = AbstractEmailForm.content_panels + [
        FieldPanel("introduction_title"),
        FieldPanel("introduction_subtitle"),
        FieldPanel('illustration'),
        InlinePanel('feedback_form_fields', label="Form fields"),
        FieldPanel('thank_you_text'),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('from_address', classname="col6"),
                FieldPanel('to_address', classname="col6"),
            ]),
            FieldPanel('subject'),
        ], _("Email")),
    ]

    def get_form_fields(self):
        return self.feedback_form_fields.all()

    def get_form_class(self):
        form_class = super(FeedbackPage, self).get_form_class()
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

    # override send_mail to extract sender email from form, to use in 'reply_to'
    # This will allow replying to the sender directly from the email client
    def send_mail(self, form):
        addresses = [x.strip() for x in self.to_address.split(',')]
        email = form.cleaned_data.get("email", None)
        options = {}
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

        mail_admins("POSSIBLE SPAM (FEEDBACK PAGE) - {}".format(self.subject), content, fail_silently=True)


class FeedbackFormField(AbstractFormField):
    page = ParentalKey(FeedbackPage,
                       on_delete=models.CASCADE,
                       related_name="feedback_form_fields")
