
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('time_tracking', '0001_initial'),
    ]

    operations = [
        migrations.RenameIndex(
            model_name='timeentry',
            new_name='time_tracki_user_id_60c1d3_idx',
            old_name='time_tracki_user_id_date__idx',
        ),
        migrations.RenameIndex(
            model_name='timeentry',
            new_name='time_tracki_project_241d11_idx',
            old_name='time_tracki_project_idx',
        ),
        migrations.RenameIndex(
            model_name='timeentry',
            new_name='time_tracki_date_91a36d_idx',
            old_name='time_tracki_date_idx',
        ),
    ]
