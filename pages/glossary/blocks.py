from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.blocks import StructValue


class LocalDefinitionStructValue(StructValue):
    def language_name(self):
        from .models import GlossaryLanguage
        language_pk = self.get("language")
        try:
            p = GlossaryLanguage.objects.get(pk=language_pk)
        except ObjectDoesNotExist:
            return None
        return p.name

    def contributor_names(self):
        from .models import GlossaryContributor
        contributor_list = self.get("contributors")
        contributor_ids = [val for val in contributor_list]
        try:
            contributors = GlossaryContributor.objects.filter(pk__in=contributor_ids)
        except Exception:
            return []
        return contributors


class LocalDefinitionBlock(blocks.StructBlock):
    language = blocks.CharBlock(required=True, label=_("Language"))
    definition = blocks.RichTextBlock(help_text=_("Definition of the term in the local language"))
    contributors = blocks.ListBlock(blocks.CharBlock(required=False, label=_("Contributor")), required=False,
                                    label=_("Contributor"))

    class Meta:
        value_class = LocalDefinitionStructValue
