
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0002_customer_address_customer_company_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='name',
            field=models.CharField(db_index=True, max_length=120, verbose_name='contact name'),
        ),
    ]
