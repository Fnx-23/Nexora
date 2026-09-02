
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('companies', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=120)),
                ('email', models.EmailField(blank=True, default='', max_length=254)),
                ('phone', models.CharField(blank=True, default='', max_length=40)),
                ('notes', models.TextField(blank=True, default='')),
                ('is_active', models.BooleanField(default=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='companies.company')),
            ],
            options={
                'ordering': ['name'],
                'indexes': [models.Index(fields=['is_active'], name='customers_c_is_acti_91d305_idx')],
            },
        ),
    ]
