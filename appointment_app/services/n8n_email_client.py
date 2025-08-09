import os
import re
import json
import logging
from typing import Dict, Any
import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class EmailClient:
    """
    Sends email by POSTing to a webhook URL defined in the SEND_EMAIL_WEBHOOK env var.
    Optional env vars:
      - FROM_EMAIL
      - FROM_NAME
    """

    def __init__(self, timeout: float = 10.0):
        load_dotenv()  # loads .env into process env if not already loaded
        self.webhook_url = os.getenv("SEND_EMAIL_WEBHOOK", "").strip()
        self.from_email = os.getenv("FROM_EMAIL", "").strip() or None
        self.from_name = os.getenv("FROM_NAME", "").strip() or None
        self.timeout = timeout

        if not self.webhook_url:
            raise ValueError("SEND_EMAIL_WEBHOOK is not set in the environment.")

        # very light URL sanity check (won't block localhost)
        if not re.match(r"^https?://", self.webhook_url):
            raise ValueError("SEND_EMAIL_WEBHOOK must start with http:// or https://")

    def send_email(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """
        Send an email via the configured webhook.

        Params:
          - to: recipient email
          - subject: email subject
          - body: HTML or plain-text body

        Returns:
          { "success": bool, "status_code": int, "data": <parsed json or text>, "error": str|None }
        """
        if not to or not subject or body is None:
            return {
                "success": False,
                "status_code": 0,
                "data": None,
                "error": "Missing required parameters: to, subject, body.",
            }

        # Heuristic: treat as HTML if it looks like it
        is_html = bool(re.search(r"<[a-zA-Z][\s\S]*>", body))

        payload = {
            "to": to,
            "subject": subject,
            "body": body,
            "is_html": is_html,
            "from_email": self.from_email or "",
            "from_name": self.from_name or "",
        }

        headers = {
            "Content-Type": "application/json",
            # Optional: idempotency key per message
            "X-Idempotency-Key": f"email:{to}:{hash(subject+body)}",
        }

        try:
            resp = requests.post(
                self.webhook_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=self.timeout,
            )
        except requests.exceptions.Timeout:
            logger.exception("Email webhook timed out")
            return {
                "success": False,
                "status_code": 0,
                "data": None,
                "error": "Request to email webhook timed out.",
            }
        except requests.RequestException as e:
            logger.exception("Email webhook request error")
            return {
                "success": False,
                "status_code": 0,
                "data": None,
                "error": f"Request error: {e}",
            }

        # Handle non-2xx
        if not (200 <= resp.status_code < 300):
            msg = resp.text.strip()
            return {
                "success": False,
                "status_code": resp.status_code,
                "data": msg if msg else None,
                "error": f"Webhook returned HTTP {resp.status_code}",
            }

        # Try to parse JSON; fall back to raw text
        try:
            data = resp.json()
        except ValueError:
            data = resp.text

        return {
            "success": True,
            "status_code": resp.status_code,
            "data": data,
            "error": None,
        }
