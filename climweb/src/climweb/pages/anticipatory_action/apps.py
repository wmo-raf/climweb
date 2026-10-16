from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AnticipatoryActionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'climweb.pages.anticipatory_action'
    verbose_name = _("Anticipatory Action")
