# Generated by Django 4.2.17 on 2025-01-11 16:19

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Certification",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("issuing_organization", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                (
                    "validity_period",
                    models.IntegerField(
                        blank=True, help_text="Validity period in months", null=True
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Department",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("code", models.CharField(max_length=10, unique=True)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="Education",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("institution", models.CharField(max_length=100)),
                ("degree", models.CharField(max_length=100)),
                ("field_of_study", models.CharField(max_length=100)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField(blank=True, null=True)),
                ("grade", models.CharField(blank=True, max_length=20)),
                ("description", models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="Employee",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("employee_id", models.CharField(max_length=20, unique=True)),
                ("position", models.CharField(max_length=100)),
                (
                    "employment_type",
                    models.CharField(
                        choices=[
                            ("full_time", "Full Time"),
                            ("part_time", "Part Time"),
                            ("contract", "Contract"),
                            ("intern", "Intern"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "employment_status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("on_leave", "On Leave"),
                            ("terminated", "Terminated"),
                            ("suspended", "Suspended"),
                        ],
                        default="active",
                        max_length=20,
                    ),
                ),
                ("date_of_birth", models.DateField()),
                ("national_id", models.CharField(max_length=20, unique=True)),
                ("phone_number", models.CharField(max_length=20)),
                ("emergency_contact", models.CharField(max_length=100)),
                ("emergency_phone", models.CharField(max_length=20)),
                ("hire_date", models.DateField()),
                ("end_date", models.DateField(blank=True, null=True)),
                ("salary", models.DecimalField(decimal_places=2, max_digits=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="Skill",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("category", models.CharField(max_length=50)),
                (
                    "level_required",
                    models.IntegerField(
                        help_text="Skill level from 1 to 5",
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(5),
                        ],
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Training",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField()),
                (
                    "training_type",
                    models.CharField(
                        choices=[
                            ("technical", "Technical"),
                            ("soft_skills", "Soft Skills"),
                            ("compliance", "Compliance"),
                            ("safety", "Safety"),
                            ("leadership", "Leadership"),
                        ],
                        max_length=20,
                    ),
                ),
                ("trainer", models.CharField(max_length=100)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("planned", "Planned"),
                            ("in_progress", "In Progress"),
                            ("completed", "Completed"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="planned",
                        max_length=20,
                    ),
                ),
                ("location", models.CharField(max_length=100)),
                ("max_participants", models.IntegerField()),
                (
                    "cost_per_participant",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="TrainingParticipant",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("enrolled", "Enrolled"),
                            ("in_progress", "In Progress"),
                            ("completed", "Completed"),
                            ("dropped", "Dropped"),
                        ],
                        default="enrolled",
                        max_length=20,
                    ),
                ),
                ("enrollment_date", models.DateField(auto_now_add=True)),
                ("completion_date", models.DateField(blank=True, null=True)),
                ("score", models.FloatField(blank=True, null=True)),
                ("feedback", models.TextField(blank=True)),
                (
                    "attendance",
                    models.IntegerField(
                        default=0,
                        help_text="Attendance percentage",
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ],
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "employee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="hr_management.employee",
                    ),
                ),
                (
                    "training",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="hr_management.training",
                    ),
                ),
            ],
            options={
                "unique_together": {("employee", "training")},
            },
        ),
        migrations.AddField(
            model_name="training",
            name="participants",
            field=models.ManyToManyField(
                related_name="trainings",
                through="hr_management.TrainingParticipant",
                to="hr_management.employee",
            ),
        ),
        migrations.AddField(
            model_name="training",
            name="prerequisites",
            field=models.ManyToManyField(blank=True, to="hr_management.skill"),
        ),
        migrations.CreateModel(
            name="PerformanceReview",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("review_period", models.CharField(max_length=50)),
                ("review_date", models.DateField()),
                (
                    "overall_rating",
                    models.IntegerField(
                        choices=[
                            (1, "Poor"),
                            (2, "Below Average"),
                            (3, "Average"),
                            (4, "Above Average"),
                            (5, "Excellent"),
                        ],
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(5),
                        ],
                    ),
                ),
                (
                    "technical_skills",
                    models.IntegerField(
                        choices=[
                            (1, "Poor"),
                            (2, "Below Average"),
                            (3, "Average"),
                            (4, "Above Average"),
                            (5, "Excellent"),
                        ],
                        default=3,
                    ),
                ),
                (
                    "communication",
                    models.IntegerField(
                        choices=[
                            (1, "Poor"),
                            (2, "Below Average"),
                            (3, "Average"),
                            (4, "Above Average"),
                            (5, "Excellent"),
                        ],
                        default=3,
                    ),
                ),
                (
                    "teamwork",
                    models.IntegerField(
                        choices=[
                            (1, "Poor"),
                            (2, "Below Average"),
                            (3, "Average"),
                            (4, "Above Average"),
                            (5, "Excellent"),
                        ],
                        default=3,
                    ),
                ),
                (
                    "initiative",
                    models.IntegerField(
                        choices=[
                            (1, "Poor"),
                            (2, "Below Average"),
                            (3, "Average"),
                            (4, "Above Average"),
                            (5, "Excellent"),
                        ],
                        default=3,
                    ),
                ),
                (
                    "punctuality",
                    models.IntegerField(
                        choices=[
                            (1, "Poor"),
                            (2, "Below Average"),
                            (3, "Average"),
                            (4, "Above Average"),
                            (5, "Excellent"),
                        ],
                        default=3,
                    ),
                ),
                ("achievements", models.TextField()),
                ("areas_for_improvement", models.TextField()),
                ("goals", models.TextField()),
                ("comments", models.TextField()),
                ("acknowledgement", models.BooleanField(default=False)),
                ("acknowledged_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "employee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="performance_reviews",
                        to="hr_management.employee",
                    ),
                ),
                (
                    "reviewer",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reviewed_performances",
                        to="hr_management.employee",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="LeaveRequest",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "leave_type",
                    models.CharField(
                        choices=[
                            ("annual", "Annual Leave"),
                            ("sick", "Sick Leave"),
                            ("maternity", "Maternity Leave"),
                            ("paternity", "Paternity Leave"),
                            ("unpaid", "Unpaid Leave"),
                            ("other", "Other"),
                        ],
                        max_length=20,
                    ),
                ),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("reason", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "approved_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="approved_leaves",
                        to="hr_management.employee",
                    ),
                ),
                (
                    "employee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="leave_requests",
                        to="hr_management.employee",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="EmployeeSkill",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "proficiency_level",
                    models.IntegerField(
                        help_text="Current proficiency level from 1 to 5",
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(5),
                        ],
                    ),
                ),
                (
                    "years_of_experience",
                    models.DecimalField(
                        decimal_places=1,
                        help_text="Years of experience with this skill",
                        max_digits=4,
                    ),
                ),
                (
                    "last_used",
                    models.DateField(help_text="When was this skill last used"),
                ),
                (
                    "employee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="hr_management.employee",
                    ),
                ),
                (
                    "skill",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="hr_management.skill",
                    ),
                ),
            ],
            options={
                "unique_together": {("employee", "skill")},
            },
        ),
        migrations.CreateModel(
            name="EmployeeEducation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("is_verified", models.BooleanField(default=False)),
                ("verification_date", models.DateField(blank=True, null=True)),
                ("verification_notes", models.TextField(blank=True)),
                (
                    "education",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="hr_management.education",
                    ),
                ),
                (
                    "employee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="hr_management.employee",
                    ),
                ),
            ],
            options={
                "unique_together": {("employee", "education")},
            },
        ),
        migrations.CreateModel(
            name="EmployeeCertification",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date_obtained", models.DateField()),
                ("expiry_date", models.DateField(blank=True, null=True)),
                ("certificate_number", models.CharField(blank=True, max_length=100)),
                (
                    "certification",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="hr_management.certification",
                    ),
                ),
                (
                    "employee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="hr_management.employee",
                    ),
                ),
            ],
            options={
                "unique_together": {("employee", "certification", "date_obtained")},
            },
        ),
        migrations.AddField(
            model_name="employee",
            name="certifications",
            field=models.ManyToManyField(
                through="hr_management.EmployeeCertification",
                to="hr_management.certification",
            ),
        ),
        migrations.AddField(
            model_name="employee",
            name="department",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="hr_management.department",
            ),
        ),
        migrations.AddField(
            model_name="employee",
            name="education",
            field=models.ManyToManyField(
                through="hr_management.EmployeeEducation", to="hr_management.education"
            ),
        ),
        migrations.AddField(
            model_name="employee",
            name="skills",
            field=models.ManyToManyField(
                through="hr_management.EmployeeSkill", to="hr_management.skill"
            ),
        ),
        migrations.AddField(
            model_name="employee",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name="department",
            name="manager",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="managed_department",
                to="hr_management.employee",
            ),
        ),
        migrations.CreateModel(
            name="Attendance",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date", models.DateField()),
                ("time_in", models.TimeField()),
                ("time_out", models.TimeField(blank=True, null=True)),
                ("status", models.CharField(default="present", max_length=20)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "employee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attendance",
                        to="hr_management.employee",
                    ),
                ),
            ],
            options={
                "unique_together": {("employee", "date")},
            },
        ),
    ]
