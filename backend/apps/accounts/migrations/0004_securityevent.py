
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_add_refresh_token_to_sessiondevice'),
    ]

    operations = [
        migrations.CreateModel(
            name='SecurityEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('event_type', models.CharField(choices=[('login', 'Login'), ('login_failed', 'Failed login'), ('password_changed', 'Password changed'), ('password_reset', 'Password reset'), ('email_verified', 'Email verified'), ('profile_updated', 'Profile updated'), ('session_revoked', 'Session revoked'), ('sessions_revoked_others', 'All other sessions revoked')], db_index=True, max_length=40)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True, default='')),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Non-sensitive contextual detail (e.g. session id).')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='security_events', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['user', '-created_at'], name='acc_sec_evt_user_idx')],
            },
        ),
    ]
