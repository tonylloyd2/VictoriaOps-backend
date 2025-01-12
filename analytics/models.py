from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings

class AnalyticsEvent(models.Model):
    """Model for tracking analytics events"""
    EVENT_TYPES = (
        ('production', 'Production'),
        ('quality', 'Quality'),
        ('maintenance', 'Maintenance'),
        ('safety', 'Safety'),
        ('inventory', 'Inventory'),
    )

    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    event_name = models.CharField(max_length=100)
    timestamp = models.DateTimeField(default=timezone.now)
    value = models.FloatField()
    unit = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    # Replace JSON field with structured data
    source_machine = models.CharField(max_length=100)
    source_department = models.CharField(max_length=100)
    source_operator = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.event_type} - {self.event_name} ({self.timestamp})"

class EventMetadata(models.Model):
    """Model for storing additional event metadata"""
    event = models.ForeignKey(AnalyticsEvent, on_delete=models.CASCADE, related_name='metadata')
    key = models.CharField(max_length=100)
    value = models.CharField(max_length=255)
    
    class Meta:
        unique_together = ['event', 'key']

class KPI(models.Model):
    """Model for tracking Key Performance Indicators"""
    CATEGORIES = (
        ('efficiency', 'Efficiency'),
        ('quality', 'Quality'),
        ('productivity', 'Productivity'),
        ('safety', 'Safety'),
        ('cost', 'Cost'),
    )

    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORIES)
    unit = models.CharField(max_length=50)
    target_value = models.FloatField()
    current_value = models.FloatField()
    
    # Alert thresholds
    warning_threshold = models.FloatField(help_text="Threshold for warning alerts")
    critical_threshold = models.FloatField(help_text="Threshold for critical alerts")
    
    # Trend settings
    trend_period_days = models.IntegerField(default=30, help_text="Number of days to analyze for trends")
    update_frequency = models.CharField(
        max_length=50,
        choices=[
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        default='daily'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.category})"

class KPIHistory(models.Model):
    """Model for tracking historical KPI values"""
    kpi = models.ForeignKey(KPI, on_delete=models.CASCADE, related_name='history')
    value = models.FloatField()
    timestamp = models.DateTimeField(default=timezone.now)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "KPI histories"

    def __str__(self):
        return f"{self.kpi.name} - {self.value} ({self.timestamp})"

class Alert(models.Model):
    """Model for managing KPI alerts"""
    SEVERITY_LEVELS = (
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    )

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
    )

    kpi = models.ForeignKey(KPI, on_delete=models.CASCADE, related_name='alerts')
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    threshold_value = models.FloatField()
    current_value = models.FloatField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    acknowledged_by = models.CharField(max_length=100, blank=True)
    resolution_note = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.severity} Alert: {self.title}"

class Report(models.Model):
    """Model for generating and storing reports"""
    REPORT_TYPES = (
        ('kpi_summary', 'KPI Summary'),
        ('event_analysis', 'Event Analysis'),
        ('trend_analysis', 'Trend Analysis'),
        ('alert_summary', 'Alert Summary'),
    )

    FORMAT_CHOICES = (
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    )

    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    description = models.TextField(blank=True)
    
    # Report parameters
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    report_format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='pdf')
    
    # Report filters
    included_kpis = models.ManyToManyField(KPI, blank=True, related_name='reports')
    event_types = models.CharField(max_length=255, blank=True, help_text="Comma-separated list of event types")
    departments = models.CharField(max_length=255, blank=True, help_text="Comma-separated list of departments")
    
    created_at = models.DateTimeField(auto_now_add=True)
    generated_at = models.DateTimeField(null=True, blank=True)
    generated_by = models.CharField(max_length=100)
    
    # Store the report file
    file = models.FileField(upload_to='reports/', null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.report_type})"

class DataAggregation(models.Model):
    """Model for storing pre-calculated aggregations"""
    AGGREGATION_TYPES = (
        ('sum', 'Sum'),
        ('average', 'Average'),
        ('min', 'Minimum'),
        ('max', 'Maximum'),
        ('count', 'Count'),
    )

    TIME_PERIODS = (
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    aggregation_type = models.CharField(max_length=50, choices=AGGREGATION_TYPES)
    time_period = models.CharField(max_length=50, choices=TIME_PERIODS)
    
    # Source data configuration
    source_kpi = models.ForeignKey(KPI, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=50, choices=AnalyticsEvent.EVENT_TYPES, blank=True)
    department = models.CharField(max_length=100, blank=True)
    
    # Aggregation results
    value = models.FloatField(null=True, blank=True)
    count = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    # Time range
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    class Meta:
        unique_together = ['name', 'aggregation_type', 'time_period']
        indexes = [
            models.Index(fields=['aggregation_type', 'time_period']),
        ]

    def __str__(self):
        return f"{self.name} ({self.aggregation_type} - {self.time_period})"

class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='managed_departments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class ProductionMetrics(models.Model):
    date = models.DateField()
    production_line = models.CharField(max_length=100)
    output_quantity = models.IntegerField(validators=[MinValueValidator(0)])
    defect_rate = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Defect rate in percentage"
    )
    efficiency = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Production line efficiency in percentage"
    )
    downtime = models.DurationField(help_text="Total downtime duration")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.production_line} - {self.date}"

    class Meta:
        ordering = ['-date']
        verbose_name = "Production Metric"
        verbose_name_plural = "Production Metrics"

class InventoryMetrics(models.Model):
    date = models.DateField()
    warehouse = models.CharField(max_length=100)
    stock_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    turnover_rate = models.FloatField(
        validators=[MinValueValidator(0)],
        help_text="Inventory turnover rate"
    )
    stockout_incidents = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of stockout incidents"
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.warehouse} - {self.date}"

    class Meta:
        ordering = ['-date']
        verbose_name = "Inventory Metric"
        verbose_name_plural = "Inventory Metrics"

class AnalyticsEventNew(models.Model):
    EVENT_TYPES = [
        ('system', 'System Event'),
        ('user', 'User Event'),
        ('business', 'Business Event'),
    ]
    
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    name = models.CharField(max_length=100)
    description = models.TextField()
    data = models.JSONField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='analytics_events_new'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} - {self.name}"

    class Meta:
        ordering = ['-timestamp']

class ReportNew(models.Model):
    REPORT_TYPES = [
        ('daily', 'Daily Report'),
        ('weekly', 'Weekly Report'),
        ('monthly', 'Monthly Report'),
        ('custom', 'Custom Report'),
    ]
    
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField(blank=True)
    parameters = models.JSONField(default=dict)
    data = models.JSONField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_reports_new'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.report_type}"

    class Meta:
        ordering = ['-created_at']

class AlertNew(models.Model):
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    is_active = models.BooleanField(default=True)
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.severity} - {self.title}"

    class Meta:
        ordering = ['-created_at']

class DataAggregationNew(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    aggregation_type = models.CharField(max_length=50)
    data = models.JSONField()
    parameters = models.JSONField(default=dict)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.aggregation_type}"

    class Meta:
        ordering = ['-last_updated']
