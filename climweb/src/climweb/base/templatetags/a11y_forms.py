"""
Template filters that render form fields accessibly (WCAG 2.1 AA): errors and help text
linked to their field, invalid fields marked, and personal-data fields given an
autocomplete token. Used by the bulma/forms templates.
"""
from django import forms, template

register = template.Library()

# Field-name hints -> HTML autocomplete tokens (WCAG 1.3.5, Identify Input Purpose).
# Matched against the field name, which for form-builder pages is the slugified label.
# Order matters: the first rule whose hint appears in the name wins.
AUTOCOMPLETE_RULES = [
    (("email",), "email"),
    (("first_name", "firstname", "given_name"), "given-name"),
    (("last_name", "lastname", "surname", "family_name"), "family-name"),
    (("full_name", "fullname", "your_name"), "name"),
    (("phone", "telephone", "mobile"), "tel"),
    (("organisation", "organization", "institution", "company", "affiliation"), "organization"),
    (("job_title",), "organization-title"),
    (("country",), "country-name"),
    (("city", "town"), "address-level2"),
    (("postal_code", "postcode", "zip_code"), "postal-code"),
    (("address",), "street-address"),
]

# Widgets where autocomplete makes sense
TEXT_LIKE_WIDGETS = (forms.TextInput, forms.EmailInput, forms.URLInput, forms.Textarea)


def autocomplete_token(field):
    widget = field.field.widget
    if "autocomplete" in widget.attrs or not isinstance(widget, TEXT_LIKE_WIDGETS):
        return None
    name = field.name.lower()
    if name == "name":
        return "name"
    for hints, token in AUTOCOMPLETE_RULES:
        if any(hint in name for hint in hints):
            return token
    if isinstance(widget, forms.EmailInput):
        return "email"
    return None


@register.filter
def describedby(field):
    """Ids of the field's error and help text, for aria-describedby."""
    ids = []
    if field.errors:
        ids.append(f"{field.auto_id}_errors")
    if field.help_text:
        ids.append(f"{field.auto_id}_help")
    return " ".join(ids)


@register.filter
def has_required_fields(form):
    """True when required fields are marked with an asterisk (required_css_class) and there is one."""
    return bool(getattr(form, "required_css_class", "")) and any(f.field.required for f in form.visible_fields())


@register.filter
def error_target(field):
    """Id to link to from the error summary: the input, or the fieldset for option groups."""
    if isinstance(field.field.widget, forms.RadioSelect):  # CheckboxSelectMultiple subclasses it
        return f"{field.auto_id}_group"
    return field.auto_id


@register.filter
def a11y_widget(field, css_class=""):
    """
    Render the field's widget with its error/help text linked (aria-describedby),
    aria-invalid when it has errors, and an autocomplete token for personal details.
    css_class is added to the widget's classes (plus "is-danger" when invalid), like
    django-bulma's addclass filter.
    """
    attrs = {}

    classes = field.field.widget.attrs.get("class", "")
    if css_class:
        classes = f"{classes} {css_class}"
    if field.errors:
        classes = f"{classes} is-danger"
        attrs["aria-invalid"] = "true"
    if classes.strip():
        attrs["class"] = classes.strip()

    ids = describedby(field)
    if ids:
        attrs["aria-describedby"] = ids

    token = autocomplete_token(field)
    if token:
        attrs["autocomplete"] = token

    return field.as_widget(attrs=attrs)
