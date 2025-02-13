import wagtail_factories

from .. import models


class MailchimpMailingListSubscriptionPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.MailchimpMailingListSubscriptionPage
    
    title = "Subscribe"
    heading = "Subscribe to our mailing list"
    introduction_text = "Subscribe to our mailing list to receive updates on our latest news and events."
    list_id = "1234567890"
