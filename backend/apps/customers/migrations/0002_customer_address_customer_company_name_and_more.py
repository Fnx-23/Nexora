
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='address',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='customer',
            name='company_name',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.AddField(
            model_name='customer',
            name='status',
            field=models.CharField(choices=[('ACTIVE', 'Active'), ('INACTIVE', 'Inactive'), ('ARCHIVED', 'Archived')], db_index=True, default='ACTIVE', max_length=20),
        ),
        migrations.AlterField(
            model_name='customer',
            name='name',
            field=models.CharField(max_length=120, verbose_name='contact name'),
        ),
    ]
