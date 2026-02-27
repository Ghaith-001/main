"""
Notifications EmailJS (API REST) pour formulaires Contact / Idées.
Configuration via variables d'environnement.
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib import request, error


EMAILJS_ENDPOINT = "https://api.emailjs.com/api/v1.0/email/send"


def is_emailjs_enabled() -> bool:
    return os.getenv("ENABLE_EMAILJS", "false").strip().lower() in {"1", "true", "yes", "on"}


def _base_payload(template_id: str, template_params: dict[str, Any]) -> dict[str, Any]:
    service_id = os.getenv("EMAILJS_SERVICE_ID", "").strip()
    public_key = os.getenv("EMAILJS_PUBLIC_KEY", "").strip()
    private_key = os.getenv("EMAILJS_PRIVATE_KEY", "").strip()

    if not service_id or not public_key or not template_id:
        raise ValueError("EmailJS non configuré: EMAILJS_SERVICE_ID / EMAILJS_PUBLIC_KEY / TEMPLATE_ID manquant.")

    payload: dict[str, Any] = {
        "service_id": service_id,
        "template_id": template_id,
        "user_id": public_key,
        "template_params": template_params,
    }
    if private_key:
        payload["accessToken"] = private_key
    return payload


def _send(payload: dict[str, Any]) -> tuple[bool, str]:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        EMAILJS_ENDPOINT,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=15) as resp:
            status = getattr(resp, "status", 200)
            body = resp.read().decode("utf-8", errors="ignore")
            if status in (200, 201):
                return True, body or "ok"
            return False, body or f"HTTP {status}"
    except error.HTTPError as http_err:
        body = http_err.read().decode("utf-8", errors="ignore")
        return False, body or f"HTTPError {http_err.code}"
    except Exception as exc:
        return False, str(exc)


def send_contact_email(name: str, email: str, message: str, date: str) -> tuple[bool, str]:
    template_id = os.getenv("EMAILJS_TEMPLATE_ID_CONTACT", "").strip()
    payload = _base_payload(
        template_id,
        {
            "type": "contact",
            "name": name,
            "email": email,
            "message": message,
            "date": date,
        },
    )
    return _send(payload)


def send_idea_email(name: str, role: str, category: str, content: str, rating: int, date: str) -> tuple[bool, str]:
    template_id = os.getenv("EMAILJS_TEMPLATE_ID_IDEA", "").strip()
    payload = _base_payload(
        template_id,
        {
            "type": "idea",
            "name": name,
            "role": role,
            "category": category,
            "content": content,
            "rating": rating,
            "date": date,
        },
    )
    return _send(payload)
