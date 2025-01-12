# Generated by Django 4.2.17 on 2025-01-12 08:38

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("hr_management", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Position",
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
                ("title", models.CharField(max_length=100)),
                ("description", models.TextField()),
                (
                    "level",
                    models.IntegerField(
                        help_text="Position level in organization hierarchy (1-10)",
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(10),
                        ],
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("min_salary", models.DecimalField(decimal_places=2, max_digits=10)),
                ("max_salary", models.DecimalField(decimal_places=2, max_digits=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "department",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="hr_management.department",
                    ),
                ),
            ],
            options={
                "ordering": ["department", "level", "title"],
            },
        ),
        migrations.AlterField(
            model_name="employee",
            name="position",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="hr_management.position",
            ),
        ),
    ]
