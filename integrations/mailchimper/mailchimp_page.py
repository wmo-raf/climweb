from django.db import models
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel, PageChooserPanel


class BaseMailChimpPage(models.Model):
    """
    Abstract MailChimp page definition.
    """
    list_id = models.CharField(('MailChimp List ID'), max_length=50,
                               help_text=('Enter the MailChimp list ID to use for this form'))
    double_optin = models.BooleanField(('Double Opt-In'), default=True,
                                       help_text=('Use double opt-in process for new subscribers'))
    thank_you_text = models.TextField(blank=True, null=True, help_text="Message to show on successful submission")

    class Meta(object):
        abstract = True

    def serve(self, request):
        """
        Serves the page as a MailChimpView.

        :param request: the request object.
        :rtype: django.http.HttpResponse.
        """

        from .views import MailChimpView

        view = MailChimpView.as_view(page_instance=self)
        return view(request)

    content_panels = [
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('list_id'),
                FieldPanel('double_optin')
            ], classname='label-above'),
        ], (u'MailChimp Settings')),
        FieldPanel('thank_you_text')
    ]