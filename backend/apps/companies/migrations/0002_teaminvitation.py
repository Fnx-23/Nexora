
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TeamInvitation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('email', models.EmailField(max_length=254)),
                ('role', models.CharField(choices=[('ADMIN', 'Admin'), ('MANAGER', 'Manager'), ('EMPLOYEE', 'Employee')], default='EMPLOYEE', max_length=20)),
                ('token_hash', models.CharField(editable=False, max_length=128)),
                ('expires_at', models.DateTimeField()),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('ACCEPTED', 'Accepted'), ('EXPIRED', 'Expired'), ('REVOKED', 'Revoked')], db_index=True, default='PENDING', max_length=20)),
                ('accepted_at', models.DateTimeField(blank=True, null=True)),
                ('accepted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to='companies.company')),
                ('invited_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['company', 'status'], name='companies_t_company_2f0629_idx'), models.Index(fields=['email'], name='companies_t_email_299179_idx')],
                'constraints': [models.UniqueConstraint(condition=models.Q(('status', 'PENDING')), fields=('company', 'email'), name='uniq_pending_invitation_per_company_email')],
            },
        ),
    ]
