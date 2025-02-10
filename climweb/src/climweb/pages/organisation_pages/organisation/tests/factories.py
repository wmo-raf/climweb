import wagtail_factories

from .. import models


class OrganisationIndexPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.OrganisationIndexPage
    
    title = "Organisation"
