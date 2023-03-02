import hashlib
import os
from contextlib import contextmanager

from django.conf import settings
from django.db import models
from wagtail.models import CollectionMember,ReferenceIndex
from wagtail.images.models import SourceImageIOError
from wagtail.search import index
from wagtail.search.queryset import SearchableQuerySetMixin


class WebIconQuerySet(SearchableQuerySetMixin, models.QuerySet):
    pass


class WebIcon(CollectionMember, index.Indexed, models.Model):
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(verbose_name=('created at'), auto_now_add=True, db_index=True)
    uploaded_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=('uploaded by user'),
        null=True, blank=True, editable=False, on_delete=models.SET_NULL
    )

    file = models.FileField()

    file_size = models.PositiveIntegerField(null=True, editable=False)

    # A SHA-1 hash of the file contents
    file_hash = models.CharField(max_length=40, blank=True, editable=False)

    search_fields = [
        index.SearchField('title', partial_match=True, boost=10),
        index.AutocompleteField('title'),
        index.FilterField('title'),
        index.FilterField('uploaded_by_user'),
    ]

    objects = WebIconQuerySet.as_manager()

    def __str__(self):
        return self.title

    @property
    def url(self):
        return self.file.url

    def is_stored_locally(self):
        """
        Returns True if the image is hosted on the local filesystem
        """
        try:
            self.file.path

            return True
        except NotImplementedError:
            return False

    def get_file_size(self):
        if self.file_size is None:
            try:
                self.file_size = self.file.size
            except Exception as e:
                # File not found
                #
                # Have to catch everything, because the exception
                # depends on the file subclass, and therefore the
                # storage being used.
                raise SourceImageIOError(str(e))

            self.save(update_fields=['file_size'])

        return self.file_size

    def get_usage(self):
        return ReferenceIndex.get_references_to(self).group_by_source_object()


    def _set_file_hash(self, file_contents):
        self.file_hash = hashlib.sha1(file_contents).hexdigest()

    def get_file_hash(self):
        if self.file_hash == '':
            with self.open_file() as f:
                self._set_file_hash(f.read())

            self.save(update_fields=['file_hash'])

        return self.file_hash

    @contextmanager
    def open_file(self):
        # Open file if it is closed
        close_file = False
        try:
            icon_file = self.file

            if self.file.closed:
                # Reopen the file
                if self.is_stored_locally():
                    self.file.open('rb')
                else:
                    # Some external storage backends don't allow reopening
                    # the file. Get a fresh file instance. #1397
                    storage = self._meta.get_field('file').storage
                    icon_file = storage.open(self.file.name, 'rb')

                close_file = True
        except IOError as e:
            # re-throw this as a SourceImageIOError so that calling code can distinguish
            # these from IOErrors elsewhere in the process
            raise SourceImageIOError(str(e))

        # Seek to beginning
        icon_file.seek(0)

        try:
            yield icon_file
        finally:
            if close_file:
                icon_file.close()

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    @property
    def default_alt_text(self):
        # by default the alt text field (used in rich text insertion) is populated
        # from the title. Subclasses might provide a separate alt field, and
        # override this
        return self.title

    def is_editable_by_user(self, user):
        from wagtail.images.permissions import permission_policy
        return permission_policy.user_has_permission_for_instance(user, 'change', self)

    class Meta:
        ordering = ('-id',)
