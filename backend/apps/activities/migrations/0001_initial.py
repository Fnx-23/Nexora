
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('companies', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('action', models.CharField(choices=[('customer.created', 'Customer created'), ('customer.updated', 'Customer updated'), ('customer.archived', 'Customer archived'), ('project.created', 'Project created'), ('project.updated', 'Project updated'), ('project.status_changed', 'Project status changed'), ('task.created', 'Task created'), ('task.assigned', 'Task assigned'), ('task.status_changed', 'Task status changed'), ('team.role_changed', 'Team role changed')], editable=False, max_length=40)),
                ('entity_type', models.CharField(choices=[('customer', 'Customer'), ('project', 'Project'), ('task', 'Task'), ('membership', 'Membership')], editable=False, max_length=40)),
                ('entity_id', models.UUIDField(blank=True, editable=False, help_text='Primary key of the affected object (retained even if it is later deleted).', null=True)),
                ('metadata', models.JSONField(blank=True, default=dict, editable=False, help_text='Non-sensitive contextual detail. Sanitized before storage.')),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('actor', models.ForeignKey(blank=True, editable=False, help_text='User who caused the event; NULL for system actions.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('company', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='companies.company')),
            ],
            options={
                'verbose_name': 'activity',
                'verbose_name_plural': 'activities',
                'ordering': ['-timestamp'],
                'indexes': [models.Index(fields=['company', '-timestamp'], name='activities__company_44ffcf_idx'), models.Index(fields=['company', 'entity_type', 'entity_id'], name='activities__company_3560cd_idx'), models.Index(fields=['company', 'action'], name='activities__company_c5cf43_idx'), models.Index(fields=['company', 'actor'], name='activities__company_390f36_idx')],
            },
        ),
    ]
