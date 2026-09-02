
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0002_teaminvitation'),
        ('notifications', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationPreference',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('task_assigned', models.BooleanField(default=True)),
                ('task_due_soon', models.BooleanField(default=True)),
                ('task_overdue', models.BooleanField(default=True)),
                ('task_comment', models.BooleanField(default=True)),
                ('project_assigned', models.BooleanField(default=True)),
                ('project_deadline', models.BooleanField(default=True)),
                ('invitation_received', models.BooleanField(default=True)),
                ('role_changed', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
        migrations.AddField(
            model_name='notification',
            name='category',
            field=models.CharField(blank=True, choices=[('task_assigned', 'Task assignments'), ('task_due_soon', 'Task due soon'), ('task_overdue', 'Task overdue'), ('task_comment', 'Task comments'), ('project_assigned', 'Project assignments'), ('project_deadline', 'Project deadlines'), ('invitation_received', 'Invitations'), ('role_changed', 'Role changes')], db_index=True, default='', max_length=40),
        ),
        migrations.AddField(
            model_name='notification',
            name='dedup_key',
            field=models.CharField(blank=True, db_index=True, default='', max_length=200),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['company', 'recipient', 'category', 'dedup_key'], name='notificatio_company_f57b2c_idx'),
        ),
        migrations.AddField(
            model_name='notificationpreference',
            name='company',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='companies.company'),
        ),
        migrations.AddField(
            model_name='notificationpreference',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_preferences', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddIndex(
            model_name='notificationpreference',
            index=models.Index(fields=['company', 'user'], name='notificatio_company_123f2b_idx'),
        ),
        migrations.AddConstraint(
            model_name='notificationpreference',
            constraint=models.UniqueConstraint(fields=('company', 'user'), name='uniq_notification_preference_per_company_user'),
        ),
    ]
