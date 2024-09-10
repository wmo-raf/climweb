from django.contrib import admin

from .models import Airport, AirportCategory, Message

admin.site.register(Airport)
admin.site.register(AirportCategory)
admin.site.register(Message)
