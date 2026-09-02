
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("companies", "0001_initial"),
        ("projects", "0001_initial"),
        ("tasks", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TimeEntry",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, db_index=True),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "date",
                    models.DateField(default=django.utils.timezone.now),
                ),
                ("start_time", models.TimeField()),
                ("end_time", models.TimeField(blank=True, null=True)),
                (
                    "duration",
                    models.DurationField(
                        blank=True,
                        help_text="Calculated or manually entered duration.",
                        null=True,
                    ),
                ),
                ("description", models.TextField(blank=True, default="")),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="companies.company",
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="time_entries",
                        to="projects.project",
                    ),
                ),
                (
                    "task",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="time_entries",
                        to="tasks.task",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="time_entries",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-date", "-start_time"],
                "indexes": [
                    models.Index(
                        fields=["user", "date"],
                        name="time_tracki_user_id_date__idx",
                    ),
                    models.Index(
                        fields=["project"],
                        name="time_tracki_project_idx",
                    ),
                    models.Index(
                        fields=["date"],
                        name="time_tracki_date_idx",
                    ),
                ],
            },
        ),
    ]
