"""
A read-only Wagtail panel showing backup connection status and actions on the
Backup Settings page. It adapts to the selected provider (Google Drive or SFTP).
"""
from django.urls import reverse
from wagtail.admin.panels import Panel


class BackupConnectionPanel(Panel):
    class BoundPanel(Panel.BoundPanel):
        template_name = "admin/panels/backup_connection_panel.html"

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)
            instance = self.instance
            context.update({
                "provider": instance.provider,
                "enabled": instance.enabled,
                "ready": instance.provider_ready(),
                "last_backup_at": instance.last_backup_at,
                "last_backup_status": instance.get_last_backup_status_display(),
                "last_backup_message": instance.last_backup_message,
                # Google Drive
                "is_connected": instance.is_connected,
                "account_email": instance.google_account_email,
                "oauth_configured": instance.is_oauth_app_configured(),
                "connect_url": reverse("backup-google-connect"),
                "disconnect_url": reverse("backup-google-disconnect"),
                # SFTP
                "sftp_configured": instance.is_sftp_configured(),
                "sftp_public_key": instance.sftp_public_key,
                "sftp_host_key": instance.sftp_host_key,
                "sftp_host": instance.sftp_host,
                "sftp_generate_url": reverse("backup-sftp-generate-key"),
                "sftp_clear_key_url": reverse("backup-sftp-clear-key"),
                "sftp_clear_hostkey_url": reverse("backup-sftp-clear-hostkey"),
                # shared
                "run_now_url": reverse("backup-run-now"),
                "help_url": reverse("backup-help"),
                "browser_url": reverse("backup-browser"),
                "is_superuser": getattr(getattr(self, "request", None), "user", None)
                and self.request.user.is_superuser,
            })
            return context
