from django.conf import settings
from api.utils import HttpMethod, HttpUtils
import logging
from django.template import Context, Template
import os
from pathlib import Path

logger = logging.getLogger(getattr(settings, 'LOGGER', __name__))


def render_email_template(template_name, context):
    base_dir = Path(settings.BASE_DIR)
    template_path = base_dir / 'email_templates' / template_name

    if not os.path.exists(template_path):
        error_msg = f"Email template not found: {template_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    try:
        with open(template_path, 'r', encoding='utf-8') as file:
            template_content = file.read()

        template = Template(template_content)
        rendered_content = template.render(Context(context))
        logger.debug("Successfully rendered email template: %s", template_name)
        return rendered_content
    except Exception as exc:
        error_msg = f"Error rendering email template {template_name}: {str(exc)}"
        logger.error(error_msg, exc_info=True)
        raise Exception(error_msg) from exc


def send_email_html_brevo(to_email, to_name, template_name, context, subject, cc_list=None, attachments=None):
    try:
        html_content = render_email_template(template_name, context)
    except Exception as exc:
        error_msg = f"Template rendering failed for {template_name}: {str(exc)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg

    brevo_api_key = getattr(settings, 'BREVO_API_KEY', None)
    if not brevo_api_key:
        error_msg = "BREVO_API_KEY is not configured."
        logger.error(error_msg)
        return False, error_msg

    payload = {
        "sender": {
            "name": getattr(settings, 'BREVO_SENDER_NAME', 'KACU'),
            "email": getattr(settings, 'BREVO_SENDER_EMAIL', 'no-reply@kacu.ca'),
        },
        "to": [{"email": to_email, "name": to_name}],
        "subject": subject,
        "htmlContent": html_content,
    }

    if cc_list:
        payload["cc"] = [{"email": cc_email} for cc_email in cc_list]

    if attachments:
        import base64

        brevo_attachments = []
        for file in attachments:
            try:
                brevo_attachments.append(
                    {
                        "content": base64.b64encode(file["content"]).decode("utf-8"),
                        "name": file["filename"],
                    }
                )
            except Exception as exc:
                logger.error("Attachment processing failed: %s", str(exc), exc_info=True)
        payload["attachment"] = brevo_attachments

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": brevo_api_key,
    }

    url = "https://api.brevo.com/v3/smtp/email"

    try:
        logger.info("Sending invite email through Brevo to %s", to_email)
        response = HttpUtils.make_http_call(
            HttpMethod.POST,
            url,
            headers=headers,
            json=payload,
            skip_ssl_check=True,
        )

        if response.status_code < 200 or response.status_code > 299:
            error_msg = f"Failed to send email via Brevo. Status: {response.status_code}, Response: {response.text}"
            logger.error(error_msg)
            return False, error_msg

        return True, "Email sent successfully"
    except Exception as exc:
        error_msg = f"Failed to send email via Brevo: {str(exc)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg
