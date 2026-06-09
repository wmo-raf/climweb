from django import forms
from wagtail.admin.views.generic.chooser import BaseFilterForm
from wagtailmodelchooser import Chooser, registry
from wagtailmodelchooser.viewsets import (
    DeconstructibleChooserBlock,
    ModelChooseView,
    ModelResultsView,
)


class TitleSearchFilterForm(BaseFilterForm):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Search by title…"}),
        label="Search",
    )

    def filter(self, objects):
        q = self.cleaned_data.get("q", "").strip()
        if q:
            objects = objects.filter(title__icontains=q)
        return objects


class SearchableChooseView(ModelChooseView):
    filter_form_class = TitleSearchFilterForm


class SearchableResultsView(ModelResultsView):
    filter_form_class = TitleSearchFilterForm


class SearchableChooser(Chooser):
    """
    Drop-in replacement for Chooser that enables title-based text search in the
    chooser modal.  Use for models that are not Wagtail-indexed but have a
    `title` field.
    """

    choose_view_class = SearchableChooseView
    results_view_class = SearchableResultsView


def searchable_viewset_factory(chooser):
    """
    Replacement for wagtailmodelchooser.viewsets.viewset_factory that reads
    choose_view_class / results_view_class from the Chooser instance so
    SearchableChooser subclasses get the search-enabled views.
    """
    from wagtail.admin.viewsets.chooser import ChooserViewSet

    model_name = chooser.model.__name__
    nice_name = chooser.model._meta.verbose_name

    choose_view = getattr(chooser, "choose_view_class", ModelChooseView)
    results_view = getattr(chooser, "results_view_class", ModelResultsView)

    return type(
        f"{model_name}ChooserViewSet",
        (ChooserViewSet,),
        {
            "model": chooser.model,
            "icon": chooser.icon,
            "choose_one_text": f"Choose {nice_name}",
            "choose_another_text": f"Choose another {nice_name}",
            "link_to_chosen_text": f"Edit this {nice_name}",
            "choose_view_class": choose_view,
            "choose_results_view_class": results_view,
            "base_block_class": DeconstructibleChooserBlock,
        },
    )(f"{model_name.lower()}_chooser")


def register_searchable_chooser(model, icon="map"):
    """
    Like register_model_chooser but registers a SearchableChooser so the
    model's chooser modal includes a title search box.
    """
    name = f"{model._meta.object_name}Chooser"
    chooser_cls = type(name, (SearchableChooser,), {"model": model, "icon": icon})
    registry.register_chooser(chooser_cls)
    return model
