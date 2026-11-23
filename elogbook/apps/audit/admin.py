from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__username', 'user__email', 'action', 'ip_address')
    readonly_fields = ('user', 'action', 'timestamp', 'ip_address', 'user_agent', 'details')
    list_per_page = 50
    
    def has_add_permission(self, request):
        return False  