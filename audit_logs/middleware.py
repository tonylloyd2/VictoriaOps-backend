from django.utils.deprecation import MiddlewareMixin
from django.contrib.contenttypes.models import ContentType
from .models import AuditLog
import json

class AuditLogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Store the request start time
        request.audit_start_time = request.META.get('time', None)

    def process_response(self, request, response):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return response

        # Skip static files and admin media
        if request.path.startswith(('/static/', '/media/')):
            return response

        # Determine the action based on the request method
        method_to_action = {
            'GET': 'VIEW',
            'POST': 'CREATE',
            'PUT': 'UPDATE',
            'PATCH': 'UPDATE',
            'DELETE': 'DELETE'
        }
        
        action = method_to_action.get(request.method, 'OTHER')

        # Try to get the model information from the request
        try:
            if hasattr(request, 'resolver_match') and request.resolver_match:
                app_label = request.resolver_match.app_name or ''
                model_name = request.resolver_match.url_name or ''
            else:
                app_label = ''
                model_name = ''

            # Create the audit log entry
            AuditLog.objects.create(
                user=request.user,
                action=action,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                app_label=app_label,
                model_name=model_name,
                action_details={
                    'path': request.path,
                    'method': request.method,
                    'query_params': dict(request.GET.items()),
                    'status_code': response.status_code,
                }
            )
        except Exception as e:
            # Log the error but don't interrupt the response
            print(f"Error creating audit log: {str(e)}")

        return response
