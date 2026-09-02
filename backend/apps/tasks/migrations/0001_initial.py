
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('companies', '0001_initial'),
        ('projects', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, default='')),
                ('status', models.CharField(choices=[('TODO', 'To do'), ('IN_PROGRESS', 'In progress'), ('DONE', 'Done'), ('CANCELLED', 'Cancelled')], default='TODO', max_length=20)),
                ('priority', models.CharField(choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('URGENT', 'Urgent')], default='MEDIUM', max_length=20)),
                ('due_date', models.DateField(blank=True, null=True)),
                ('assignee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_tasks', to=settings.AUTH_USER_MODEL)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='companies.company')),
                ('project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tasks', to='projects.project')),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['status'], name='tasks_task_status_4a0a95_idx'), models.Index(fields=['assignee'], name='tasks_task_assigne_a1ddb3_idx')],
            },
        ),
    ]
