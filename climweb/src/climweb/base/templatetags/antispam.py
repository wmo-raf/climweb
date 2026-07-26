from django import template
from django.utils.safestring import mark_safe

from climweb.base.anti_spam import (
    HONEYPOT_FIELD_NAME,
    TIMESTAMP_FIELD_NAME,
    make_timestamp,
)

register = template.Library()


@register.simple_tag
def antispam_protect():
    """Render hidden anti-spam inputs to place inside a public <form>.

    - A honeypot text field that is visually hidden and removed from tab order
      and the accessibility tree, so real users never fill it while naive bots
      that populate every field give themselves away.
    - A signed timestamp so the server can reject forms submitted implausibly
      fast after the page loaded.

    Both are read from the raw POST data by
    ``climweb.base.anti_spam.get_spam_reason`` and never stored on the
    submission.
    """
    html = (
        '<div aria-hidden="true" '
        'style="position:absolute !important;left:-9999px !important;'
        'top:-9999px !important;width:1px !important;height:1px !important;'
        'overflow:hidden !important;">'
        '<label for="id_{hp}">Leave this field blank</label>'
        '<input type="text" name="{hp}" id="id_{hp}" value="" '
        'tabindex="-1" autocomplete="off">'
        "</div>"
        '<input type="hidden" name="{ts}" value="{tsval}">'
    ).format(
        hp=HONEYPOT_FIELD_NAME,
        ts=TIMESTAMP_FIELD_NAME,
        tsval=make_timestamp(),
    )
    return mark_safe(html)
