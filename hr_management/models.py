from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

User = get_user_model()

class Department(models.Model):
    """Model for managing company departments"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    manager = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_department'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Skill(models.Model):
    """Model for employee skills"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50)
    level_required = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Skill level from 1 to 5"
    )

    def __str__(self):
        return self.name

class Certification(models.Model):
    """Model for employee certifications"""
    name = models.CharField(max_length=100)
    issuing_organization = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    validity_period = models.IntegerField(
        help_text="Validity period in months",
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.name} - {self.issuing_organization}"

class Education(models.Model):
    """Model for employee education records"""
    institution = models.CharField(max_length=100)
    degree = models.CharField(max_length=100)
    field_of_study = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    grade = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.degree} in {self.field_of_study} from {self.institution}"

class Position(models.Model):
    """Model for job positions in the company"""
    title = models.CharField(max_length=100)
    department = models.ForeignKey('Department', on_delete=models.CASCADE)
    description = models.TextField()
    level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Position level in organization hierarchy (1-10)"
    )
    is_active = models.BooleanField(default=True)
    min_salary = models.DecimalField(max_digits=10, decimal_places=2)
    max_salary = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.department.name})"

    class Meta:
        ordering = ['department', 'level', 'title']

class Employee(models.Model):
    """Model for managing employee information"""
    EMPLOYMENT_STATUS = (
        ('active', 'Active'),
        ('on_leave', 'On Leave'),
        ('terminated', 'Terminated'),
        ('suspended', 'Suspended'),
    )
    EMPLOYMENT_TYPE = (
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('intern', 'Intern'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE)
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS, default='active')
    
    # Personal Information
    date_of_birth = models.DateField()
    national_id = models.CharField(max_length=20, unique=True)
    phone_number = models.CharField(max_length=20)
    emergency_contact = models.CharField(max_length=100)
    emergency_phone = models.CharField(max_length=20)
    
    # Employment Details
    hire_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Skills, Certifications, and Education
    skills = models.ManyToManyField(Skill, through='EmployeeSkill')
    certifications = models.ManyToManyField(Certification, through='EmployeeCertification')
    education = models.ManyToManyField(Education, through='EmployeeEducation')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"

class EmployeeSkill(models.Model):
    """Model for tracking employee skills"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    proficiency_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Current proficiency level from 1 to 5"
    )
    years_of_experience = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        help_text="Years of experience with this skill"
    )
    last_used = models.DateField(help_text="When was this skill last used")
    
    class Meta:
        unique_together = ['employee', 'skill']

    def __str__(self):
        return f"{self.employee} - {self.skill} (Level {self.proficiency_level})"

class EmployeeCertification(models.Model):
    """Model for tracking employee certifications"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE)
    date_obtained = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    certificate_number = models.CharField(max_length=100, blank=True)
    
    class Meta:
        unique_together = ['employee', 'certification', 'date_obtained']

    def __str__(self):
        return f"{self.employee} - {self.certification}"

class EmployeeEducation(models.Model):
    """Model for tracking employee education"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    education = models.ForeignKey(Education, on_delete=models.CASCADE)
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['employee', 'education']

    def __str__(self):
        return f"{self.employee} - {self.education}"

class LeaveRequest(models.Model):
    """Model for managing employee leave requests"""
    LEAVE_TYPES = (
        ('annual', 'Annual Leave'),
        ('sick', 'Sick Leave'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
        ('unpaid', 'Unpaid Leave'),
        ('other', 'Other'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    approved_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leaves'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.status})"

class Attendance(models.Model):
    """Model for tracking employee attendance"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField()
    time_in = models.TimeField()
    time_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='present')
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'date']

    def __str__(self):
        return f"{self.employee} - {self.date}"

class PerformanceReview(models.Model):
    """Model for managing employee performance reviews"""
    RATING_CHOICES = (
        (1, 'Poor'),
        (2, 'Below Average'),
        (3, 'Average'),
        (4, 'Above Average'),
        (5, 'Excellent'),
    )

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='performance_reviews')
    reviewer = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reviewed_performances'
    )
    review_period = models.CharField(max_length=50)  # e.g., "Q1 2024"
    review_date = models.DateField()
    
    # Performance Metrics
    overall_rating = models.IntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Specific performance areas
    technical_skills = models.IntegerField(choices=RATING_CHOICES, default=3)
    communication = models.IntegerField(choices=RATING_CHOICES, default=3)
    teamwork = models.IntegerField(choices=RATING_CHOICES, default=3)
    initiative = models.IntegerField(choices=RATING_CHOICES, default=3)
    punctuality = models.IntegerField(choices=RATING_CHOICES, default=3)
    
    achievements = models.TextField()
    areas_for_improvement = models.TextField()
    goals = models.TextField()
    
    comments = models.TextField()
    acknowledgement = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee} - {self.review_period}"

class Training(models.Model):
    """Model for managing employee training programs"""
    STATUS_CHOICES = (
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    TRAINING_TYPE = (
        ('technical', 'Technical'),
        ('soft_skills', 'Soft Skills'),
        ('compliance', 'Compliance'),
        ('safety', 'Safety'),
        ('leadership', 'Leadership'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    training_type = models.CharField(max_length=20, choices=TRAINING_TYPE)
    trainer = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    
    participants = models.ManyToManyField(
        Employee,
        through='TrainingParticipant',
        related_name='trainings'
    )
    
    prerequisites = models.ManyToManyField(Skill, blank=True)
    location = models.CharField(max_length=100)
    max_participants = models.IntegerField()
    cost_per_participant = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class TrainingParticipant(models.Model):
    """Model for tracking employee participation in training programs"""
    STATUS_CHOICES = (
        ('enrolled', 'Enrolled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
    )

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    training = models.ForeignKey(Training, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled')
    enrollment_date = models.DateField(auto_now_add=True)
    completion_date = models.DateField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    
    attendance = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Attendance percentage"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'training']

    def __str__(self):
        return f"{self.employee} - {self.training}"
