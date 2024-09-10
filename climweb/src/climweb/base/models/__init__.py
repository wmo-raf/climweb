from django.utils.translation import gettext_lazy as _

from climweb.base.models.abstracts import *
from climweb.base.models.custom import *
from climweb.base.models.permissions import *
from climweb.base.models.site_settings import *
from climweb.base.models.snippets import *


class FormFileSubmission(models.Model):
    FILE_TYPE_CHOICES = (
        ('image', 'Image'),
        ('document', 'Document'),
    )

    file = models.FileField(upload_to='form_files/%Y/%m/%d')
    file_type = models.CharField(max_length=255, choices=FILE_TYPE_CHOICES, default='image')

    class Meta:
        verbose_name = _('File Submission')
        verbose_name_plural = _('File Submissions')
