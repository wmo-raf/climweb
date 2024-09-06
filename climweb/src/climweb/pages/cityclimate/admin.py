from django.contrib import admin

from .models import DataValue


class DataValueAdmin(admin.ModelAdmin):
    pass


admin.site.register(DataValue, DataValueAdmin)
