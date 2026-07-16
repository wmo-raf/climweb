"""
A read-only Wagtail panel that shows the Google Drive connection status and a
Connect / Disconnect button, rendered on the Backup Settings page.
"""
from django.urls import reverse
from wagtail.admin.panels import Panel


class GoogleDriveConnectPanel(Panel):
    class BoundPanel(Panel.BoundPanel):
        template_name = "admin/panels/google_drive_connect_panel.html"

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)
            instance = self.instance
            context.update({
                "is_connected": instance.is_connected,
                "account_email": instance.google_account_email,
                "last_backup_at": instance.last_backup_at,
                "last_backup_status": instance.get_last_backup_status_display(),
                "last_backup_message": instance.last_backup_message,
                "oauth_configured": instance.is_oauth_app_configured(),
                "connect_url": reverse("backup-google-connect"),
                "disconnect_url": reverse("backup-google-disconnect"),
                "run_now_url": reverse("backup-run-now"),
                "help_url": reverse("backup-help"),
                "enabled": instance.enabled,
            })
            return context
