
import django.core.validators
import django.db.models.deletion
import re
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0002_teaminvitation'),
        ('tasks', '0002_task_created_by_alter_task_status_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskLabel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=50)),
                ('color', models.CharField(default='#3b82f6', help_text='Hex color for the label chip, e.g. #3b82f6.', max_length=7, validators=[django.core.validators.RegexValidator(regex=re.compile('^#[0-9a-fA-F]{6}$'))])),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='companies.company')),
            ],
            options={
                'verbose_name': 'task label',
                'verbose_name_plural': 'task labels',
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='task',
            name='labels',
            field=models.ManyToManyField(blank=True, related_name='tasks', to='tasks.tasklabel'),
        ),
        migrations.CreateModel(
            name='TaskSubtask',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=200)),
                ('completed', models.BooleanField(default=False)),
                ('position', models.PositiveIntegerField(default=0)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='companies.company')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subtasks', to='tasks.task')),
            ],
            options={
                'verbose_name': 'task subtask',
                'verbose_name_plural': 'task subtasks',
                'ordering': ['position', 'id'],
            },
        ),
        migrations.CreateModel(
            name='TaskChecklistItem',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('text', models.CharField(max_length=255)),
                ('completed', models.BooleanField(default=False)),
                ('position', models.PositiveIntegerField(default=0)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='companies.company')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checklist_items', to='tasks.task')),
            ],
            options={
                'verbose_name': 'task checklist item',
                'verbose_name_plural': 'task checklist items',
                'ordering': ['position', 'id'],
                'indexes': [models.Index(fields=['task', 'position'], name='tasks_taskc_task_id_0eaca5_idx')],
            },
        ),
        migrations.CreateModel(
            name='TaskComment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('body', models.TextField()),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='task_comments', to=settings.AUTH_USER_MODEL)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='companies.company')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='tasks.task')),
            ],
            options={
                'verbose_name': 'task comment',
                'verbose_name_plural': 'task comments',
                'ordering': ['created_at'],
                'indexes': [models.Index(fields=['task', 'created_at'], name='tasks_taskc_task_id_3f97e8_idx')],
            },
        ),
        migrations.AddConstraint(
            model_name='tasklabel',
            constraint=models.UniqueConstraint(fields=('company', 'name'), name='unique_task_label_name_per_company'),
        ),
    ]
