import wagtail_factories

from .. import models


class WebStoryListPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.WebStoryListPage
    
    title = "Web Stories"
