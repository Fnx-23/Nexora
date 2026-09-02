
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='entity_kind',
            field=models.CharField(choices=[('COMPANY', 'Company'), ('PROJECT', 'Project'), ('CUSTOMER', 'Customer'), ('TASK', 'Task')], default='COMPANY', max_length=20),
        ),
    ]
