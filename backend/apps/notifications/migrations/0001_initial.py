
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('companies', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('verb', models.CharField(max_length=255)),
                ('entity_type', models.CharField(blank=True, default='', max_length=40)),
                ('entity_id', models.UUIDField(blank=True, null=True)),
                ('entity_name', models.CharField(blank=True, default='', max_length=200)),
                ('link', models.CharField(blank=True, default='', max_length=500)),
                ('is_read', models.BooleanField(db_index=True, default=False)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='companies.company')),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['recipient', 'is_read', '-created_at'], name='notificatio_recipie_684eac_idx'), models.Index(fields=['company', 'recipient'], name='notificatio_company_73f089_idx')],
            },
        ),
    ]
