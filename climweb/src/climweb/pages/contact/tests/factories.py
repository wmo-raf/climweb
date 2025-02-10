import wagtail_factories

from .. import models


class ContactUsPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.ContactPage
    
    title = "Contact Us"
    name = "Some Place"
    location = "0,0"
