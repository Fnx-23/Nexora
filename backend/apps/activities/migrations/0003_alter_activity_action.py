
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0002_alter_activity_action_alter_activity_entity_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='action',
            field=models.CharField(choices=[('customer.created', 'Customer created'), ('customer.updated', 'Customer updated'), ('customer.archived', 'Customer archived'), ('project.created', 'Project created'), ('project.updated', 'Project updated'), ('project.status_changed', 'Project status changed'), ('project.member_added', 'Member added to project'), ('project.member_removed', 'Member removed from project'), ('task.created', 'Task created'), ('task.assigned', 'Task assigned'), ('task.status_changed', 'Task status changed'), ('task.priority_changed', 'Task priority changed'), ('task.due_date_changed', 'Task due date changed'), ('task.comment_added', 'Comment added to task'), ('task.comment_deleted', 'Comment removed from task'), ('task.attachment_added', 'Attachment added to task'), ('team.role_changed', 'Team role changed'), ('password.changed', 'Password changed'), ('password.reset', 'Password reset'), ('email.verified', 'Email verified'), ('session.revoked', 'Session revoked'), ('sessions.revoked_others', 'All other sessions revoked'), ('profile.updated', 'Profile updated'), ('invitation.sent', 'Invitation sent'), ('invitation.accepted', 'Invitation accepted'), ('invitation.revoked', 'Invitation revoked'), ('team.member_deactivated', 'Member deactivated'), ('team.member_reactivated', 'Member reactivated'), ('team.member_removed', 'Member removed')], editable=False, max_length=40),
        ),
    ]
