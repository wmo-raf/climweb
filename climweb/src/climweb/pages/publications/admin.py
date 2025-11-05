from django.contrib import admin
from .models import PageView


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ['content_object', 'ip_address', 'timestamp', 'session_key']
    list_filter = ['content_type', 'timestamp']
    readonly_fields = ['content_type', 'object_id', 'content_object', 'ip_address', 'user_agent', 'timestamp', 'session_key']
    search_fields = ['ip_address']
    
    def has_add_permission(self, request):
        return False  # Prevent manual creation of page views
