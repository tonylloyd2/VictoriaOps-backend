from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Department, Employee, LeaveRequest, Attendance,
    PerformanceReview, Training, TrainingParticipant,
    Skill, Certification, Education, Position,
    EmployeeSkill, EmployeeCertification, EmployeeEducation
)
from datetime import datetime, date

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'level_required')
    list_filter = ('category', 'level_required')
    search_fields = ('name', 'description', 'category')

@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'issuing_organization', 'validity_period')
    list_filter = ('issuing_organization',)
    search_fields = ('name', 'issuing_organization', 'description')

@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('institution', 'degree', 'field_of_study', 'start_date', 'end_date')
    list_filter = ('degree', 'institution')
    search_fields = ('institution', 'degree', 'field_of_study')
    date_hierarchy = 'start_date'

class EmployeeSkillInline(admin.TabularInline):
    model = EmployeeSkill
    extra = 1
    autocomplete_fields = ['skill']

class EmployeeCertificationInline(admin.TabularInline):
    model = EmployeeCertification
    extra = 1
    autocomplete_fields = ['certification']

class EmployeeEducationInline(admin.TabularInline):
    model = EmployeeEducation
    extra = 1
    autocomplete_fields = ['education']

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'manager', 'employee_count')
    list_filter = ('created_at',)
    search_fields = ('name', 'code', 'description')
    date_hierarchy = 'created_at'

    def employee_count(self, obj):
        return obj.employee_set.count()
    employee_count.short_description = 'Number of Employees'

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'get_full_name', 'department', 'position', 'employment_type', 'employment_status')
    list_filter = ('department', 'employment_type', 'employment_status', 'hire_date')
    search_fields = ('user__first_name', 'user__last_name', 'employee_id', 'position')
    date_hierarchy = 'hire_date'
    inlines = [EmployeeSkillInline, EmployeeCertificationInline, EmployeeEducationInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (('user', 'employee_id'), ('department', 'position'))
        }),
        ('Employment Details', {
            'fields': (
                ('employment_type', 'employment_status'),
                ('hire_date', 'end_date'),
                'salary'
            )
        }),
        ('Personal Information', {
            'fields': (
                'date_of_birth',
                ('national_id', 'phone_number'),
                ('emergency_contact', 'emergency_phone')
            )
        }),
    )
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Name'

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'status', 'approved_by')
    list_filter = ('leave_type', 'status', 'start_date')
    search_fields = ('employee__user__first_name', 'employee__user__last_name', 'reason')
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Request Details', {
            'fields': ('employee', 'leave_type', ('start_date', 'end_date'), 'reason')
        }),
        ('Status', {
            'fields': ('status', 'approved_by', 'approved_at')
        }),
    )
    readonly_fields = ('approved_at',)

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'time_in', 'time_out', 'status', 'duration')
    list_filter = ('date', 'status')
    search_fields = ('employee__user__first_name', 'employee__user__last_name')
    date_hierarchy = 'date'
    
    def duration(self, obj):
        if obj.time_in and obj.time_out:
            time_in = obj.time_in
            time_out = obj.time_out
            duration = datetime.combine(date.min, time_out) - datetime.combine(date.min, time_in)
            hours = duration.seconds / 3600
            return f"{hours:.2f} hours"
        return "-"
    duration.short_description = 'Duration'

@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    list_display = ('employee', 'reviewer', 'review_period', 'overall_rating', 'status_indicator')
    list_filter = ('review_period', 'overall_rating', 'acknowledgement')
    search_fields = ('employee__user__first_name', 'employee__user__last_name', 'reviewer__user__first_name', 'reviewer__user__last_name')
    date_hierarchy = 'review_date'
    
    fieldsets = (
        ('Review Information', {
            'fields': ('employee', 'reviewer', 'review_period', 'review_date')
        }),
        ('Performance Ratings', {
            'fields': (
                'overall_rating',
                ('technical_skills', 'communication'),
                ('teamwork', 'initiative'),
                'punctuality'
            )
        }),
        ('Feedback', {
            'fields': ('achievements', 'areas_for_improvement', 'goals', 'comments')
        }),
        ('Acknowledgement', {
            'fields': ('acknowledgement', 'acknowledged_at')
        }),
    )
    readonly_fields = ('acknowledged_at',)
    
    def status_indicator(self, obj):
        if obj.acknowledgement:
            color = 'green'
            status = 'Acknowledged'
        else:
            color = 'orange'
            status = 'Pending'
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            status
        )
    status_indicator.short_description = 'Status'

@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ('title', 'training_type', 'trainer', 'start_date', 'end_date', 'status', 'participant_count')
    list_filter = ('training_type', 'status', 'start_date')
    search_fields = ('title', 'description', 'trainer')
    date_hierarchy = 'start_date'
    filter_horizontal = ('prerequisites',)
    
    fieldsets = (
        ('Training Information', {
            'fields': ('title', 'description', 'training_type', 'trainer')
        }),
        ('Schedule', {
            'fields': (('start_date', 'end_date'), 'status')
        }),
        ('Requirements', {
            'fields': ('prerequisites', 'max_participants', 'cost_per_participant')
        }),
        ('Location', {
            'fields': ('location',)
        }),
    )
    
    def participant_count(self, obj):
        count = obj.participants.count()
        return f"{count}/{obj.max_participants}"
    participant_count.short_description = 'Participants'

@admin.register(TrainingParticipant)
class TrainingParticipantAdmin(admin.ModelAdmin):
    list_display = ('employee', 'training', 'status', 'enrollment_date', 'completion_date', 'score', 'attendance')
    list_filter = ('status', 'enrollment_date', 'completion_date')
    search_fields = ('employee__user__first_name', 'employee__user__last_name', 'training__title')
    date_hierarchy = 'enrollment_date'
    
    fieldsets = (
        ('Participant Information', {
            'fields': ('employee', 'training', 'status')
        }),
        ('Progress', {
            'fields': (('enrollment_date', 'completion_date'), ('score', 'attendance'))
        }),
        ('Feedback', {
            'fields': ('feedback',)
        }),
    )
    readonly_fields = ('enrollment_date',)

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'level', 'is_active')
    list_filter = ('department', 'level', 'is_active')
    search_fields = ('title', 'description')
    ordering = ('department', 'level', 'title')
