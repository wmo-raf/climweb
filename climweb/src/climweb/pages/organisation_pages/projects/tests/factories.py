import factory
import wagtail_factories

from .. import models


class ProjectsIndexPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.ProjectIndexPage
    
    title = "Projects"
    banner_title = "Our Projects"
    banner_image = factory.SubFactory(wagtail_factories.ImageFactory)
    
    introduction_title = "Explore our projects"
    introduction_text = factory.Faker('paragraph')


class ProjectPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.ProjectPage
    
    title = factory.Faker('sentence')
    banner_title = "Our Projects"
    banner_image = factory.SubFactory(wagtail_factories.ImageFactory)
    
    introduction_title = "Explore our projects"
    introduction_text = factory.Faker('paragraph')
    
    full_name = factory.Faker("sentence")
    begin_date = factory.Faker("date")
    end_date = factory.Faker("date")
