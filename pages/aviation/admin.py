from django.contrib import admin

# Register your models here.
from pages.aviation.models import Station, StationCategory, Message

admin.site.register(Station)
admin.site.register(StationCategory)
admin.site.register(Message)
