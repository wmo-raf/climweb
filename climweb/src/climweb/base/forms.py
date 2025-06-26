from django import forms
from django.core.validators import FileExtensionValidator
from django.template.defaultfilters import filesizeformat
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from wagtail.api.v2.utils import get_full_url
from wagtail.contrib.forms.forms import FormBuilder
from wagtail.contrib.forms.views import SubmissionsListView
from wagtail.images.fields import WagtailImageField

from climweb.base.models import FormFileSubmission


class CMSUpgradeForm(forms.Form):
    current_version = forms.CharField(max_length=100, required=True, widget=forms.HiddenInput)
    latest_version = forms.CharField(max_length=100, required=True, widget=forms.HiddenInput)


class FormImageField(WagtailImageField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_upload_size = 2 * 1024 * 1024
        self.max_upload_size_text = filesizeformat(self.max_upload_size)
        
        # Help text
        self.help_text = _("Supported formats: %(supported_formats)s. Maximum filesize: %(max_upload_size)s.") % {
            "supported_formats": self.supported_formats_text,
            "max_upload_size": self.max_upload_size_text,
        }


def PDFFileExtensionValidator(value):
    allowed_extensions = ['pdf']
    return FileExtensionValidator(allowed_extensions)(value)


def FileSizeValidator(value):
    max_upload_size = 5 * 1024 * 1024
    if value.size > max_upload_size:
        raise forms.ValidationError(
            _("File size must be under %(max_upload_size)s. Current file size is %(current_file_size)s"),
            params={
                "max_upload_size": filesizeformat(max_upload_size),
                "current_file_size": filesizeformat(value.size),
            },
        )


class FormDocumentField(forms.FileField):
    default_validators = [PDFFileExtensionValidator, FileSizeValidator]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_upload_size = 5 * 1024 * 1024
        self.max_upload_size_text = filesizeformat(self.max_upload_size)
        
        # Help text
        self.help_text = _("Supported formats: PDF. Maximum filesize: %(max_upload_size)s.") % {
            "max_upload_size": self.max_upload_size_text,
        }


class CustomSubmissionsListView(SubmissionsListView):
    
    def get_file_submission_url(self, file_submission_pk):
        file_submission = FormFileSubmission.objects.get(pk=file_submission_pk)
        return get_full_url(self.request, file_submission.file.url)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if not self.is_export:
            # generate a list of field types, the first being the injected 'submission date'
            field_types = ['submission_date'] + [field.field_type for field in self.form_page.get_form_fields()]
            data_rows = context['data_rows']
            
            for data_row in data_rows:
                fields = data_row['fields']
                for idx, (value, field_type) in enumerate(zip(fields, field_types)):
                    if field_type == 'image' or field_type == 'document' and value:
                        file_submission = FormFileSubmission.objects.get(pk=value)
                        full_url = get_full_url(self.request, file_submission.file.url)
                        
                        file_path = file_submission.file.name
                        file_name = file_path.split('/')[-1]
                        
                        if field_type == 'image':
                            
                            fields[idx] = format_html(
                                "<div><img alt='Uploaded image - {}' src='{}' "
                                "style='height:100px;width;100px;object-fit;contain;' /> "
                                "<div> <a href='{}' target='_blank' >{}</a></div></div>",
                                file_submission.file.name,
                                full_url,
                                full_url,
                                file_name
                            )
                        else:
                            fields[idx] = format_html(
                                "<a href='{}' target='_blank'>{}</a>",
                                full_url,
                                file_name
                            )
        
        return context
    
    def get_preprocess_function(self, field, value, export_format):
        fields_by_type = {field.clean_name: field.field_type for field in self.form_page.get_form_fields()}
        field_type = fields_by_type.get(field)
        
        # If the field_type is an image or document, we need to return a function that will return
        # the full URL of the file
        if field_type == 'image' or field_type == 'document':
            preprocess_fn = self.get_file_submission_url
        else:
            preprocess_fn = super().get_preprocess_function(field, value, export_format)
        
        return preprocess_fn


class CustomFormBuilder(FormBuilder):
    def create_image_field(self, field, options):
        return FormImageField(**options)
    
    def create_document_field(self, field, options):
        return FormDocumentField(**options)
