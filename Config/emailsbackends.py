import resend
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings

class ResendEmailBackend(BaseEmailBackend):
    """
    Email backend using Resend API
    """
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'RESEND_API_KEY', None)
        if self.api_key:
            resend.api_key = self.api_key

    def send_messages(self, email_messages):
        """
        Send one or more EmailMessage objects and return the number of email
        messages sent.
        """
        if not email_messages or not self.api_key:
            return 0

        msg_count = 0
        for message in email_messages:
            sent = self._send(message)
            if sent:
                msg_count += 1
        return msg_count

    def _send(self, email_message):
        """Send a single email message"""
        if not email_message.recipients():
            return False

        try:
            # Prepare the email data for Resend
            email_data = {
                "from": email_message.from_email or settings.DEFAULT_FROM_EMAIL,
                "to": email_message.recipients(),
                "subject": email_message.subject,
            }

            # Handle HTML vs plain text content
            if hasattr(email_message, 'alternatives') and email_message.alternatives:
                # If there are alternatives, use the HTML version
                for content, content_type in email_message.alternatives:
                    if content_type == 'text/html':
                        email_data["html"] = content
                        break
                else:
                    # Fallback to plain text
                    email_data["text"] = email_message.body
            else:
                email_data["text"] = email_message.body

            # Send the email via Resend API
            response = resend.Emails.send(email_data)

            return True

        except Exception as e:
            if not self.fail_silently:
                raise
            return False