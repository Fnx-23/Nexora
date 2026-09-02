
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=120)),
                ('slug', models.SlugField(max_length=60, unique=True)),
                ('description', models.TextField(blank=True, default='')),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('role', models.CharField(choices=[('ADMIN', 'Admin'), ('MANAGER', 'Manager'), ('EMPLOYEE', 'Employee')], default='EMPLOYEE', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='companies.company')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['created_at'],
                'indexes': [models.Index(fields=['user'], name='companies_m_user_id_b8199c_idx')],
                'constraints': [models.UniqueConstraint(fields=('company', 'user'), name='uniq_membership_per_company')],
            },
        ),
    ]
