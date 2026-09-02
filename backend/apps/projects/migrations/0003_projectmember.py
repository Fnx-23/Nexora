
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0002_teaminvitation'),
        ('projects', '0002_rename_end_date_project_deadline_project_manager_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectMember',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='companies.company')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='projects.project')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='project_memberships', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['created_at'],
                'indexes': [models.Index(fields=['project'], name='projects_pr_project_3a727c_idx'), models.Index(fields=['user'], name='projects_pr_user_id_7dfae9_idx')],
                'constraints': [models.UniqueConstraint(fields=('project', 'user'), name='uniq_project_member')],
            },
        ),
    ]
