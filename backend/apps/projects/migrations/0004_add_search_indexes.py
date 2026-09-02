
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0003_projectmember'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='name',
            field=models.CharField(db_index=True, max_length=120),
        ),
    ]
