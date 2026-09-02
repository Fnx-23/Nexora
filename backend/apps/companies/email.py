"""Email delivery for team invitations.

Sending is best-effort and must never fail the invitation request. Any failure
to render or dispatch is logged and swallowed, so a broken mail path degrades
to a silently-sent invitation rather than a failed create.
"""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger("apps.companies")


def send_invitation_email(
    *,
    email: str,
    company,
    role: str,
    token: str,
    invited_by=None,
) -> bool:
    """Render and dispatch an invitation email.

    The accept URL is built from ``SITE_URL`` so it works under every deployed
    environment without hard-coding hosts. Returns ``True`` on success,
    ``False`` on any transient failure after logging.
    """
    inviter_name = ""
    if invited_by is not None:
        inviter_name = invited_by.get_full_name() or invited_by.email

    role_label = role.replace("_", " ").title()

    invite_url = f"{settings.SITE_URL}/invite?token={token}"

    subject = f"You're invited to join {company.name} on Nexora"
    body = (
        f"Hello,\n\n"
        f"{inviter_name or 'A team member'} has invited you to join "
        f"{company.name} on Nexora as {role_label}.\n\n"
        f"Accept your invitation here:\n{invite_url}\n\n"
        f"This invitation expires in 7 days.\n\n"
        f"Thanks,\nThe Nexora team"
    )
    html_body = body.replace("\n", "<br>")

    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=f"<p>{html_body}</p>",
        )
        return True
    except Exception:
        logger.exception("Failed to send invitation email to %s", email)
        return False
