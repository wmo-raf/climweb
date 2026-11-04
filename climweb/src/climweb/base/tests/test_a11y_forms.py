from django import forms
from django.template import Context, Template
from django.test import SimpleTestCase

from climweb.base.templatetags.a11y_forms import autocomplete_token, describedby, error_target


class SampleForm(forms.Form):
    required_css_class = "required"

    full_name = forms.CharField()
    email = forms.EmailField()
    phone_number = forms.CharField(required=False)
    organisation = forms.CharField(required=False, help_text="Where you work")
    station_name = forms.CharField(required=False)
    message = forms.CharField(widget=forms.Textarea)
    topic = forms.ChoiceField(choices=[("a", "A"), ("b", "B")], widget=forms.RadioSelect)
    interests = forms.MultipleChoiceField(choices=[("x", "X"), ("y", "Y")], widget=forms.CheckboxSelectMultiple,
                                          required=False)
    country = forms.ChoiceField(choices=[("ke", "Kenya")], required=False)


def render(form):
    return Template("{% load bulma_tags %}{{ form|bulma }}").render(Context({"form": form}))


class TestAutocomplete(SimpleTestCase):
    def test_tokens_from_field_names(self):
        form = SampleForm()
        self.assertEqual(autocomplete_token(form["full_name"]), "name")
        self.assertEqual(autocomplete_token(form["email"]), "email")
        self.assertEqual(autocomplete_token(form["phone_number"]), "tel")
        self.assertEqual(autocomplete_token(form["organisation"]), "organization")

    def test_no_token_for_unrelated_or_non_text_fields(self):
        form = SampleForm()
        self.assertIsNone(autocomplete_token(form["station_name"]))  # "name" alone must not match
        self.assertIsNone(autocomplete_token(form["topic"]))
        self.assertIsNone(autocomplete_token(form["country"]))  # a select, not free text


class TestDescribedBy(SimpleTestCase):
    def test_links_help_text(self):
        self.assertEqual(describedby(SampleForm()["organisation"]), "id_organisation_help")

    def test_links_errors_and_help(self):
        form = SampleForm(data={"organisation": ""})
        form.is_valid()
        self.assertEqual(describedby(form["full_name"]), "id_full_name_errors")

    def test_error_target_is_fieldset_for_option_groups(self):
        form = SampleForm()
        self.assertEqual(error_target(form["email"]), "id_email")
        self.assertEqual(error_target(form["topic"]), "id_topic_group")
        self.assertEqual(error_target(form["interests"]), "id_interests_group")


class TestRenderedForm(SimpleTestCase):
    def test_every_control_has_a_label_and_groups_have_legends(self):
        html = render(SampleForm())
        for field_id in ("id_full_name", "id_email", "id_message", "id_country"):
            self.assertIn(f'for="{field_id}"', html)
        self.assertIn('<fieldset class="field" id="id_topic_group"', html)
        self.assertIn('<fieldset class="field" id="id_interests_group"', html)
        self.assertEqual(html.count("<legend"), 2)

    def test_autocomplete_and_help_are_rendered(self):
        html = render(SampleForm())
        self.assertIn('autocomplete="email"', html)
        self.assertIn('aria-describedby="id_organisation_help"', html)
        self.assertIn('id="id_organisation_help"', html)
        self.assertIn("Fields marked with an asterisk (*) are required.", html)

    def test_invalid_submission_shows_linked_error_summary(self):
        form = SampleForm(data={})
        self.assertFalse(form.is_valid())
        html = render(form)
        self.assertIn('class="message is-danger form-error-summary" role="alert" tabindex="-1"', html)
        self.assertIn('href="#id_email"', html)
        self.assertIn('href="#id_topic_group"', html)
        self.assertIn('aria-invalid="true"', html)
        self.assertIn('id="id_email_errors"', html)

    def test_no_summary_or_invalid_markers_when_valid_form_unbound(self):
        html = render(SampleForm())
        self.assertNotIn("form-error-summary", html)
        self.assertNotIn("aria-invalid", html)
