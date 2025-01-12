from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

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
