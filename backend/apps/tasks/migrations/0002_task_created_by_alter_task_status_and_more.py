
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0001_initial'),
        ('projects', '0002_rename_end_date_project_deadline_project_manager_and_more'),
        ('tasks', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tasks', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='task',
            name='status',
            field=models.CharField(choices=[('TODO', 'To do'), ('IN_PROGRESS', 'In progress'), ('IN_REVIEW', 'In review'), ('DONE', 'Done'), ('CANCELLED', 'Cancelled')], default='TODO', max_length=20),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['created_by'], name='tasks_task_created_d80085_idx'),
        ),
    ]
