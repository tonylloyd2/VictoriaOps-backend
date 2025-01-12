from django.contrib import admin
from .models import AuditLog
from core.admin import admin_site

# Register your models here.

class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'app_label', 'model_name', 'object_repr', 'ip_address')
    list_filter = ('action', 'app_label', 'timestamp', 'user')
    search_fields = ('user__username', 'object_repr', 'action_details')
    readonly_fields = ('timestamp', 'user', 'action', 'ip_address', 'user_agent', 
                      'content_type', 'object_id', 'action_details', 'app_label', 
                      'model_name', 'object_repr')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete audit logs
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return False

# Register with our custom admin site
admin_site.register(AuditLog, AuditLogAdmin)
