
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('companies', '0001_initial'),
        ('customers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=120)),
                ('description', models.TextField(blank=True, default='')),
                ('status', models.CharField(choices=[('PLANNING', 'Planning'), ('ACTIVE', 'Active'), ('ON_HOLD', 'On hold'), ('COMPLETED', 'Completed'), ('ARCHIVED', 'Archived')], default='PLANNING', max_length=20)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='companies.company')),
                ('customer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='projects', to='customers.customer')),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['status'], name='projects_pr_status_f023cb_idx')],
            },
        ),
    ]
