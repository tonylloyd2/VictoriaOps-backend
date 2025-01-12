from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.template.response import TemplateResponse
from django.urls import NoReverseMatch, reverse
from django.apps import apps

# Import all admin configurations
from products.admin import (
    ProductAdmin, CategoryAdmin, ProductSpecificationAdmin,
    ProductComponentAdmin, ProductDocumentAdmin
)
from inventory.admin import (
    SupplierAdmin, WarehouseAdmin, StorageLocationAdmin,
    RawMaterialAdmin, StockAdmin, StockMovementAdmin
)
from orders.admin import (
    OrderAdmin, OrderItemAdmin, PaymentAdmin, MaterialRequirementAdmin
)
from hr_management.admin import (
    EmployeeAdmin, DepartmentAdmin, PositionAdmin, AttendanceAdmin,
    LeaveRequestAdmin, PerformanceReviewAdmin, SkillAdmin,
    CertificationAdmin, EducationAdmin, TrainingAdmin,
    TrainingParticipantAdmin
)
from production.admin import (
    ProductionLineAdmin, ProductionOrderAdmin, ProductionBatchAdmin,
    MaterialConsumptionAdmin, QualityCheckAdmin, MaintenanceLogAdmin
)
from analytics.admin import (
    AnalyticsEventAdmin, KPIAdmin, AlertAdmin, ReportAdmin,
    DataAggregationAdmin
)

# Import all models
from products.models import (
    Product, Category, ProductSpecification,
    ProductComponent, ProductDocument
)
from inventory.models import (
    Supplier, Warehouse, StorageLocation,
    RawMaterial, Stock, StockMovement
)
from orders.models import (
    Order, OrderItem, Payment, MaterialRequirement
)
from hr_management.models import (
    Employee, Department, Position, Attendance,
    LeaveRequest, PerformanceReview, Skill,
    Certification, Education, Training,
    TrainingParticipant
)
from production.models import (
    ProductionLine, ProductionOrder, ProductionBatch,
    MaterialConsumption, QualityCheck, MaintenanceLog
)
from analytics.models import (
    AnalyticsEvent, KPI, Alert, Report,
    DataAggregation
)

class VictoriaOpsAdminSite(AdminSite):
    site_title = _('VictoriaOps Admin')
    site_header = _('VictoriaOps Administration')
    index_title = _('VictoriaOps Management')
    site_url = '/'

    def get_app_list(self, request, app_label=None):
        """
        Return a sorted list of all the installed apps that have been
        registered in this site. If app_label is provided, return only the 
        specified app.
        """
        app_dict = self._build_app_dict(request)
        
        if app_label:
            if app_label in app_dict:
                return [app_dict[app_label]]
            return []
            
        app_list = sorted(app_dict.values(), key=lambda x: x['name'].lower())
        return app_list

    def index(self, request, extra_context=None):
        """
        Override the default admin index to use a custom template
        """
        app_list = self.get_app_list(request)
        
        # Group apps by category
        categorized_apps = {
            'Factory Operations': {
                'icon': 'fas fa-industry',
                'apps': ['inventory', 'production'],
            },
            'Human Resources': {
                'icon': 'fas fa-users',
                'apps': ['hr_management'],
            },
            'Sales & Orders': {
                'icon': 'fas fa-shopping-cart',
                'apps': ['orders', 'products'],
            },
            'System Administration': {
                'icon': 'fas fa-cogs',
                'apps': ['admin', 'auth', 'contenttypes', 'sessions'],
            },
            'Analytics & Monitoring': {
                'icon': 'fas fa-chart-line',
                'apps': ['analytics', 'django_celery_beat'],
            },
            'API & Integration': {
                'icon': 'fas fa-plug',
                'apps': ['rest_framework', 'corsheaders', 'django_filters', 'drf_spectacular'],
            },
            'Core': {
                'icon': 'fas fa-cube',
                'apps': ['core'],
            }
        }

        # Get quick stats
        total_products = 0
        total_inventory = 0
        total_employees = 0
        active_orders = 0

        try:
            total_products = Product.objects.count()
        except:
            pass

        try:
            total_inventory = Stock.objects.count()
        except:
            pass

        try:
            total_employees = Employee.objects.count()
        except:
            pass

        try:
            active_orders = Order.objects.filter(status__in=['pending', 'confirmed', 'in_production']).count()
        except:
            pass

        context = {
            **self.each_context(request),
            'title': self.index_title,
            'app_list': app_list,
            'categorized_apps': categorized_apps,
            'quick_stats': {
                'total_products': total_products,
                'total_inventory': total_inventory,
                'total_employees': total_employees,
                'active_orders': active_orders,
            },
            **(extra_context or {}),
        }

        request.current_app = self.name

        return TemplateResponse(request, 'admin/custom_index.html', context)

admin_site = VictoriaOpsAdminSite(name='victoriaops_admin')

# Register built-in models
admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)

# Register Products app models
admin_site.register(Product, ProductAdmin)
admin_site.register(Category, CategoryAdmin)
admin_site.register(ProductSpecification, ProductSpecificationAdmin)
admin_site.register(ProductComponent, ProductComponentAdmin)
admin_site.register(ProductDocument, ProductDocumentAdmin)

# Register Inventory app models
admin_site.register(Supplier, SupplierAdmin)
admin_site.register(Warehouse, WarehouseAdmin)
admin_site.register(StorageLocation, StorageLocationAdmin)
admin_site.register(RawMaterial, RawMaterialAdmin)
admin_site.register(Stock, StockAdmin)
admin_site.register(StockMovement, StockMovementAdmin)

# Register Orders app models
admin_site.register(Order, OrderAdmin)
admin_site.register(OrderItem, OrderItemAdmin)
admin_site.register(Payment, PaymentAdmin)
admin_site.register(MaterialRequirement, MaterialRequirementAdmin)

# Register HR Management models
admin_site.register(Employee, EmployeeAdmin)
admin_site.register(Department, DepartmentAdmin)
admin_site.register(Position, PositionAdmin)
admin_site.register(Attendance, AttendanceAdmin)
admin_site.register(LeaveRequest, LeaveRequestAdmin)
admin_site.register(PerformanceReview, PerformanceReviewAdmin)
admin_site.register(Skill, SkillAdmin)
admin_site.register(Certification, CertificationAdmin)
admin_site.register(Education, EducationAdmin)
admin_site.register(Training, TrainingAdmin)
admin_site.register(TrainingParticipant, TrainingParticipantAdmin)

# Register Production models
admin_site.register(ProductionLine, ProductionLineAdmin)
admin_site.register(ProductionOrder, ProductionOrderAdmin)
admin_site.register(ProductionBatch, ProductionBatchAdmin)
admin_site.register(MaterialConsumption, MaterialConsumptionAdmin)
admin_site.register(QualityCheck, QualityCheckAdmin)
admin_site.register(MaintenanceLog, MaintenanceLogAdmin)

# Register Analytics models
admin_site.register(AnalyticsEvent, AnalyticsEventAdmin)
admin_site.register(KPI, KPIAdmin)
admin_site.register(Alert, AlertAdmin)
admin_site.register(Report, ReportAdmin)
admin_site.register(DataAggregation, DataAggregationAdmin)
