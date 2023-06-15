from django.db import models
from wagtail.documents.models import Document, document_served


class CustomDocumentModel(Document):
    # Custom field
    download_count = models.IntegerField(default=0, blank=True, null=True)


def increment_document_download_count(instance, **kwargs):
    instance.download_count = instance.download_count + 1
    instance.save()


# Count documents download times
document_served.connect(increment_document_download_count)
