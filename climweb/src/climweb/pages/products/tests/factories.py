import factory
import wagtail_factories
from faker import Faker
from wagtail.rich_text import RichText

from climweb.base.models import ServiceCategory, Product, ProductCategory, ProductItemType
from .. import models
from ..blocks import ProductItemImageContentBlock, ProductItemDocumentContentBlock
from ...services.tests.factories import ServiceCategoryFactory

fake = Faker()


class ProductIndexPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.ProductIndexPage
    
    title = "Products Index Page"


class ProductItemTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductItemType
    
    name = factory.Faker("word")


class ProductCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductCategory
    
    name = factory.Faker("word")
    icon = factory.Faker("random_element", elements=["desktop", "comment", "date"])
    
    @factory.post_generation
    def product_item_types(self, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            for child in extracted:
                self.product_item_types.add(child)
        else:
            # Create a default set of inline children
            ProductItemTypeFactory.create_batch(2, category_id=self.id)
        
        self.save()


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product
    
    name = factory.Sequence(lambda n: f"Product {n}")
    
    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            for child in extracted:
                self.categories.add(child)
        else:
            # Create a default set of inline children
            ProductCategoryFactory.create_batch(2, product_id=self.id)
        self.save()


class ProductPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.ProductPage
    
    title = factory.Sequence(lambda n: f"Product {n}")
    introduction_title = factory.Sequence(lambda n: f"Product {n} Introduction")
    introduction_image = factory.SubFactory(wagtail_factories.ImageFactory)
    service = factory.SubFactory(ServiceCategoryFactory)
    product = factory.SubFactory(ProductFactory)
    
    @factory.lazy_attribute
    def introduction_text(self):
        p = fake.paragraph()
        return RichText(f"<p>{p}</p>")


class ProductItemImageContentBlockFactory(wagtail_factories.StructBlockFactory):
    class Meta:
        model = ProductItemImageContentBlock
    
    date = factory.Faker("date_time_this_year", before_now=True, after_now=False)
    image = factory.SubFactory(wagtail_factories.ImageChooserBlockFactory)
    
    @factory.lazy_attribute
    def description(self):
        p = fake.paragraph()
        return RichText(f"<p>{p}</p>")


class ProductItemDocumentContentBlockFactory(wagtail_factories.StructBlockFactory):
    class Meta:
        model = ProductItemDocumentContentBlock
    
    date = factory.Faker("date_time_this_year", before_now=True, after_now=False)
    document = factory.SubFactory(wagtail_factories.DocumentChooserBlockFactory)


class ProductItemStreamContentBlockFactory(wagtail_factories.StructBlockFactory):
    class Meta:
        model = models.ProductItemStreamContentBlock
    
    date = factory.Faker("date_time_this_year", before_now=True, after_now=False)
    
    # TODO: Add content blocks


class ProductItemPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.ProductItemPage
    
    title = factory.Sequence(lambda n: f"Product Item Page {n}")
    date = factory.Faker("date_time_this_year", before_now=True, after_now=False)
    
    products = wagtail_factories.StreamFieldFactory({
        "image_product": factory.SubFactory(ProductItemImageContentBlockFactory),
        "document_product": factory.SubFactory(ProductItemDocumentContentBlockFactory),
    })
