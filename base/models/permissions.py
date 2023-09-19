from django.db import models


class MenuPermission(models.Model):
    class Meta:
        default_permissions = ([])

        permissions = (
            ('can_view_geomanager_menu', 'Can view Geomanager menu'),
            ('can_view_survey_menu', 'Can View Survey menu'),
            ('can_view_alerts_menu', 'Can view CAP Alerts Menu'),
            ('can_view_forecast_menu', 'Can view Forecast Menu')
        )
