from django.apps import AppConfig


class AuditLogsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit_logs'
    verbose_name = 'Audit Logs'  # This will be shown in the admin interface
