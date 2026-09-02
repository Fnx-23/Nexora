
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_email_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='PasswordResetToken',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('token_hash', models.CharField(editable=False, max_length=64)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('expires_at', models.DateTimeField(editable=False)),
                ('used', models.BooleanField(default=False, editable=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='password_reset_tokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [models.Index(fields=['user', 'used', 'expires_at'], name='acc_pwdreset_token_idx')],
            },
        ),
        migrations.CreateModel(
            name='SessionDevice',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('token_id', models.UUIDField(editable=False)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_activity', models.DateTimeField(auto_now=True)),
                ('is_current', models.BooleanField(default=False, editable=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='session_devices', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-last_activity'],
                'indexes': [models.Index(fields=['user', 'is_current'], name='acc_sessdev_current_idx'), models.Index(fields=['user', 'created_at'], name='acc_sessdev_created_idx')],
            },
        ),
    ]
