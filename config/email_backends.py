"""HTTPS email backends for hosts that block outbound SMTP (e.g. DigitalOcean)."""

from __future__ import annotations

import logging
from email.utils import parseaddr

import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)


class ResendEmailBackend(BaseEmailBackend):
    """Send mail through Resend's HTTPS API (port 443) — no SMTP required."""

    api_url = "https://api.resend.com/emails"

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        api_key = getattr(settings, "RESEND_API_KEY", "") or ""
        if not api_key:
            raise RuntimeError("RESEND_API_KEY is not configured.")

        sent = 0
        for message in email_messages:
            try:
                self._send_one(message, api_key)
                sent += 1
            except Exception:
                logger.exception("Resend failed for subject=%r to=%s", message.subject, message.to)
                if not self.fail_silently:
                    raise
        return sent

    def _send_one(self, message, api_key):
        from_email = message.from_email or settings.DEFAULT_FROM_EMAIL
        payload = {
            "from": from_email,
            "to": list(message.to or []),
            "subject": message.subject or "",
        }
        if message.cc:
            payload["cc"] = list(message.cc)
        if message.bcc:
            payload["bcc"] = list(message.bcc)
        if message.reply_to:
            # Resend accepts a single reply_to string.
            payload["reply_to"] = message.reply_to[0]

        html_body, text_body = self._extract_bodies(message)
        if html_body:
            payload["html"] = html_body
        if text_body:
            payload["text"] = text_body
        if not html_body and not text_body:
            payload["text"] = message.body or ""

        # Helpfulness for deliverability logs.
        name, addr = parseaddr(from_email)
        if addr:
            payload.setdefault("tags", [{"name": "app", "value": "safastyle"}])

        resp = requests.post(
            self.api_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=getattr(settings, "EMAIL_TIMEOUT", 20),
        )
        if resp.status_code >= 400:
            raise RuntimeError(
                f"Resend API error {resp.status_code}: {resp.text[:500]}"
            )

    @staticmethod
    def _extract_bodies(message):
        html_body = None
        text_body = None
        if message.content_subtype == "html":
            html_body = message.body
        else:
            text_body = message.body
        for alt, mimetype in getattr(message, "alternatives", []) or []:
            if mimetype == "text/html":
                html_body = alt
            elif mimetype == "text/plain" and not text_body:
                text_body = alt
        return html_body, text_body
