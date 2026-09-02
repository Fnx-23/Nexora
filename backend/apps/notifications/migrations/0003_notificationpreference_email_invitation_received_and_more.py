
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0002_notificationpreference_notification_category_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationpreference',
            name='email_invitation_received',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='notificationpreference',
            name='email_project_assigned',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='notificationpreference',
            name='email_project_deadline',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='notificationpreference',
            name='email_role_changed',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='notificationpreference',
            name='email_task_assigned',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='notificationpreference',
            name='email_task_comment',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='notificationpreference',
            name='email_task_due_soon',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='notificationpreference',
            name='email_task_overdue',
            field=models.BooleanField(default=True),
        ),
    ]
