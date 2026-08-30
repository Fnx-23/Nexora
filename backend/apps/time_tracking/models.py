"""Time entry records scoped to a company."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.db.models import TenantedModel


class TimeEntry(TenantedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="time_entries",
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="time_entries",
    )
    task = models.ForeignKey(
        "tasks.Task",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="time_entries",
    )
    date = models.DateField(default=timezone.now)
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    duration = models.DurationField(
        null=True,
        blank=True,
        help_text="Calculated or manually entered duration.",
    )
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-date", "-start_time"]
        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["project"]),
            models.Index(fields=["date"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} - {self.project} - {self.date}"

    def clean(self):
        super().clean()
        if self.end_time and self.start_time and self.end_time < self.start_time:
            raise ValidationError("end_time cannot precede start_time.")
        if self.task and self.project and self.task.project_id != self.project_id:
            raise ValidationError("task must belong to the same project.")
        if self.duration and self.duration.total_seconds() < 0:
            raise ValidationError("duration cannot be negative.")

    def save(self, *args, **kwargs):
        self.full_clean()
        self._recalculate_duration()
        super().save(*args, **kwargs)

    def _recalculate_duration(self):
        """Always derive duration from the current start/end times.

        Duration is recomputed on every save (create and update) so edits to
        start_time or end_time are reflected in the stored duration, keeping
        the duration column, summary totals, project breakdown and weekly
        chart consistent.
        """
        if self.start_time and self.end_time:
            from datetime import datetime

            dt_start = datetime.combine(self.date, self.start_time)
            dt_end = datetime.combine(self.date, self.end_time)
            self.duration = dt_end - dt_start
        else:
            # Running entry (no end time) has no duration.
            self.duration = None
