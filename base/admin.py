from django.contrib import admin

from .models import VersionUpgradeStatus


class VersionUpgradeStatusAdmin(admin.ModelAdmin):
    list_display = ["__str__", "checkpoint", "success"]


admin.site.register(VersionUpgradeStatus, VersionUpgradeStatusAdmin)
