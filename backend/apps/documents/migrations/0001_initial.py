
import apps.documents.models
import django.core.validators
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
            name='Document',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('file', models.FileField(max_length=500, upload_to=apps.documents.models.document_upload_path, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['csv', 'doc', 'docx', 'gif', 'jpeg', 'jpg', 'pdf', 'png', 'ppt', 'pptx', 'txt', 'webp', 'xls', 'xlsx', 'zip'])])),
                ('original_filename', models.CharField(max_length=255)),
                ('mime_type', models.CharField(blank=True, default='', max_length=127)),
                ('size', models.PositiveBigIntegerField(help_text='File size in bytes.')),
                ('entity_kind', models.CharField(choices=[('COMPANY', 'Company'), ('PROJECT', 'Project'), ('CUSTOMER', 'Customer')], default='COMPANY', max_length=20)),
                ('entity_id', models.UUIDField(blank=True, help_text='PK of linked project or customer.', null=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='companies.company')),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['company', 'entity_kind', 'entity_id'], name='documents_d_company_6103ca_idx'), models.Index(fields=['company', '-created_at'], name='documents_d_company_45ca0d_idx')],
            },
        ),
    ]
