import string
from functools import cached_property

from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from wagtail import blocks
from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.admin.panels import InlinePanel, FieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page, Orderable

from base.mixins import MetadataPageMixin
from base.models import AbstractIntroPage
from base.utils import paginate
from pages.glossary.blocks import LocalDefinitionBlock

alphabet_list_lower = list(string.ascii_lowercase)
alphabet_list_upper = list(string.ascii_uppercase)


class GlossaryIndexPage(AbstractIntroPage):
    parent_page_types = ['home.HomePage']
    subpage_types = ['glossary.GlossaryItemDetailPage']
    template = "glossary/glossary_index_page.html"
    show_in_menus_default = True

    max_count = 1

    content_panels = Page.content_panels + [
        *AbstractIntroPage.content_panels,
        InlinePanel("languages", heading=_("Languages"), label=_("Language"),
                    help_text=_("Optional languages that terms will be defined in")),
        InlinePanel("contributors", heading=_("Contributors"), label=_("Contributor"),
                    help_text=_("List of local terminology definition contributors"))
    ]

    @cached_property
    def all_terms(self):
        terms = GlossaryItemDetailPage.objects.child_of(self).filter(live=True).order_by("title")
        return terms

    def filter_terms(self, request):
        terms = self.all_terms

        letter = request.GET.get("letter")
        search = request.GET.get('q')
        local = request.GET.get('local')

        filters = models.Q()

        if letter:
            letter = str(letter).lower()
            if letter and letter in alphabet_list_lower:
                filters &= models.Q(title__istartswith=letter)

        if search:
            filters &= models.Q(title__icontains=search)

        if local:
            # exclude terms without local definition
            terms = terms.exclude(local_definitions__exact=[])

        return terms.filter(filters).distinct()

    def filter_and_paginate_terms(self, request):
        page = request.GET.get('page')

        filtered_terms = self.filter_terms(request)

        paginated_terms = paginate(filtered_terms, page, 10)

        return paginated_terms

    @cached_property
    def alphabet_letters(self):
        return alphabet_list_upper

    def get_context(self, request, *args, **kwargs):
        context = super(GlossaryIndexPage, self).get_context(request, *args, **kwargs)
        context.update({
            "glossary_terms": self.filter_and_paginate_terms(request)
        })
        return context


class GlossaryLanguage(Orderable):
    parent = ParentalKey(GlossaryIndexPage, on_delete=models.CASCADE, related_name="languages")
    name = models.CharField(max_length=100, verbose_name=_("Language name"))


class GlossaryContributor(Orderable):
    parent = ParentalKey(GlossaryIndexPage, on_delete=models.CASCADE, related_name="contributors")
    name = models.CharField(max_length=100, verbose_name=_("Contributor name"), help_text=_("Name of Contributor"))
    organisation = models.CharField(blank=True, null=True, max_length=100, verbose_name=_("Organisation"),
                                    help_text=_("Optional name of the contributor's organisation, if applicable"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"),
                                   help_text=_("Optional details about the contributor or their organisation"))
    contact = models.TextField(blank=True, null=True, verbose_name=_("Contact details"),
                               help_text=_("Optional contact details of the contributor or organisation "))
    url = models.URLField(blank=True, null=True, verbose_name=_("Link"),
                          help_text=_("Optional link to more details about the contributor or organisation"))

    @property
    def name_org(self):
        name = self.name
        org = self.organisation
        if org:
            return f"{name} - {org}"
        else:
            return name


class GlossaryItemDetailPageForm(WagtailAdminPageForm):
    title = forms.CharField(max_length=255, label=_("Term"), help_text=_("The term to define"),
                            widget=forms.TextInput(attrs={'placeholder': _("Term*")}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        parent_page = kwargs.get("parent_page")
        languages = parent_page.specific.languages.all()
        language_choices = [(lang.pk, lang.name) for lang in languages]

        contributors = parent_page.specific.contributors.all()
        contributor_choices = [(contrib.pk, contrib.name_org) for contrib in contributors]

        local_definitions_field = self.fields.get("local_definitions")

        for block_type, block in local_definitions_field.block.child_blocks.items():
            for key, val in block.child_blocks.items():
                if key == "language":
                    label = val.label or key
                    local_definitions_field.block.child_blocks[block_type].child_blocks[
                        key] = blocks.ChoiceBlock(
                        choices=language_choices)
                    local_definitions_field.block.child_blocks[block_type].child_blocks[
                        key].name = "language"
                    local_definitions_field.block.child_blocks[block_type].child_blocks[key].label = label

                if key == "contributors":
                    label = val.label or key
                    local_definitions_field.block.child_blocks[block_type].child_blocks[
                        key] = blocks.StreamBlock(
                        [("contributor", blocks.ChoiceBlock(choices=contributor_choices, label=_("Contributor")))],
                        required=False)
                    local_definitions_field.block.child_blocks[block_type].child_blocks[
                        key].name = "contributors"
                    local_definitions_field.block.child_blocks[block_type].child_blocks[key].label = label

        self.fields["local_definitions"] = local_definitions_field


class GlossaryItemDetailPage(MetadataPageMixin, Page):
    parent_page_types = ['glossary.GlossaryIndexPage']
    subpage_types = []
    template = "glossary/glossary_item_detail_page.html"
    show_in_menus_default = True
    base_form_class = GlossaryItemDetailPageForm

    brief_definition = models.TextField(verbose_name=_("Brief definition"),
                                        help_text=_("Summarized definition of the term"))
    detail_description = RichTextField(blank=True, null=True, verbose_name=_("Detailed description"),
                                       help_text=_("Detailed definition and description of the term. "
                                                   "This should provide more information of the term, "
                                                   "including images and other materials where available"))

    local_definitions = StreamField([
        ('definitions', LocalDefinitionBlock(label="Local Definition"))
    ], blank=True, null=True, use_json_field=True, verbose_name=_("Local Definitions"))

    content_panels = Page.content_panels + [
        FieldPanel("brief_definition"),
        FieldPanel("detail_description"),
        FieldPanel("local_definitions"),
    ]
