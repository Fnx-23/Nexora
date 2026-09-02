
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_user_is_email_verified_passwordresettoken_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sessiondevice',
            name='refresh_token',
            field=models.TextField(blank=True, default='', editable=False),
        ),
    ]
