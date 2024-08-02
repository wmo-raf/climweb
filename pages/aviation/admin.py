from django.contrib import admin

# Register your models here.
from pages.aviation.models import Airport, AirportCategory, Message

admin.site.register(Airport)
admin.site.register(AirportCategory)
admin.site.register(Message)
