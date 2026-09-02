
import apps.companies.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0002_teaminvitation'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='locale',
            field=models.CharField(choices=[('en', 'English'), ('fr', 'Français'), ('es', 'Español'), ('ar', 'العربية'), ('de', 'Deutsch')], default='en', help_text='Curated interface language for the workspace.', max_length=8),
        ),
        migrations.AddField(
            model_name='company',
            name='logo',
            field=models.ImageField(blank=True, help_text='Optional workspace logo (JPEG/PNG/WebP).', null=True, upload_to=apps.companies.models.company_logo_upload_path),
        ),
        migrations.AddField(
            model_name='company',
            name='timezone',
            field=models.CharField(default='UTC', help_text='IANA time zone for the workspace (e.g. America/New_York).', max_length=64),
        ),
    ]
