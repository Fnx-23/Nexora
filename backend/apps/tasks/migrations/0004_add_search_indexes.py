
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0003_tasklabel_task_labels_tasksubtask_taskchecklistitem_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='title',
            field=models.CharField(db_index=True, max_length=200),
        ),
    ]
