
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='action',
            field=models.CharField(choices=[('customer.created', 'Customer created'), ('customer.updated', 'Customer updated'), ('customer.archived', 'Customer archived'), ('project.created', 'Project created'), ('project.updated', 'Project updated'), ('project.status_changed', 'Project status changed'), ('task.created', 'Task created'), ('task.assigned', 'Task assigned'), ('task.status_changed', 'Task status changed'), ('team.role_changed', 'Team role changed'), ('password.changed', 'Password changed'), ('password.reset', 'Password reset'), ('email.verified', 'Email verified'), ('session.revoked', 'Session revoked'), ('sessions.revoked_others', 'All other sessions revoked'), ('profile.updated', 'Profile updated'), ('invitation.sent', 'Invitation sent'), ('invitation.accepted', 'Invitation accepted'), ('invitation.revoked', 'Invitation revoked'), ('team.member_deactivated', 'Member deactivated'), ('team.member_reactivated', 'Member reactivated'), ('team.member_removed', 'Member removed')], editable=False, max_length=40),
        ),
        migrations.AlterField(
            model_name='activity',
            name='entity_type',
            field=models.CharField(choices=[('customer', 'Customer'), ('project', 'Project'), ('task', 'Task'), ('membership', 'Membership'), ('invitation', 'Invitation')], editable=False, max_length=40),
        ),
    ]
