from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from wagtail.documents.models import Document, document_served
from wagtail.images import get_image_model_string

from climweb.base.utils import get_first_page_of_pdf_as_image


class CustomDocumentModel(Document):
    # Custom field
    download_count = models.IntegerField(default=0, blank=True, null=True)
    thumbnail = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    
    def get_thumbnail(self):
        """
        Create a thumbnail for the document if it doesn't exist.
        Currently, we only generate a thumbnail for PDF files
        """
        if not self.thumbnail and self.file_extension.endswith('pdf'):
            document_title = self.title
            try:
                current_time = timezone.localtime(timezone.now()).strftime("%Y-%m-%d-%H-%M-%S")
                file_name = f"f{slugify(document_title)}-{current_time}-thumbnail.jpg"
                thumbnail = get_first_page_of_pdf_as_image(self.file.path, title=document_title, file_name=file_name)
                if thumbnail:
                    self.thumbnail = thumbnail
                    self.save()
            except:
                # do nothing if thumbnail generation fails
                pass
        
        return self.thumbnail


def increment_document_download_count(instance, **kwargs):
    instance.download_count = instance.download_count + 1
    instance.save()


# Count documents download times
document_served.connect(increment_document_download_count)
