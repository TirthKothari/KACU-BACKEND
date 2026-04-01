from django.conf import settings
from api.helpers import send_email_html_brevo
import logging


logger = logging.getLogger(getattr(settings, 'LOGGER', __name__))


ROLE_TEMPLATE_MAP = {
    "ADMIN": "invite-admin.html",
    "AGENT": "invite-agent.html",
    "PARTNER": "invite-partner.html",
}


ROLE_SUBJECT_MAP = {
    "ADMIN": "Admin",
    "AGENT": "Agent",
    "PARTNER": "Partner",
}


def send_invitation_email(email, recipient_name, inviter_name, business_name, invite_link, expires_at, role):
    role_key = (role or "").upper().strip()
    template_name = ROLE_TEMPLATE_MAP.get(role_key, "invite-user.html")
    role_label = ROLE_SUBJECT_MAP.get(role_key, "Team")

    context = {
        "params": {
            "RecipientName": recipient_name,
            "InviterName": inviter_name,
            "BusinessName": business_name,
            "Link": invite_link,
            "ExpiresAt": expires_at,
            "Role": role_label,
        }
    }
    subject = f"{inviter_name} invited you as {role_label} to join {business_name}"
    return send_email_html_brevo(
        email,
        recipient_name,
        template_name,
        context,
        subject,
    )
