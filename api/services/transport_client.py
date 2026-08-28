"""Authenticated client for transport-owned operations."""

from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import HTTPException

from utils.tls import get_ca_bundle_path


def send_portal_message(payload: dict[str, Any], *, actor_user_id: str | None) -> dict:
    base_url = (os.environ.get("BRAIN_TRANSPORT_URL") or "").strip().rstrip("/")
    token = (os.environ.get("AI_BRAIN_WEBHOOK_TOKEN") or "").strip()
    if not base_url or not token:
        raise HTTPException(503, "Transport service is not configured.")
    headers = {"X-Webhook-Token": token}
    if actor_user_id:
        headers["X-Brain-Actor-Id"] = actor_user_id
    try:
        with httpx.Client(timeout=45, verify=get_ca_bundle_path()) as client:
            response = client.post(
                base_url + "/internal/v1/transport/messages/send",
                json=payload,
                headers=headers,
            )
    except httpx.HTTPError as exc:
        raise HTTPException(502, "Transport service is unavailable.") from exc
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail")
        except (ValueError, AttributeError):
            detail = None
        raise HTTPException(response.status_code, detail or "Transport rejected the message.")
    try:
        result = response.json()
    except ValueError as exc:
        raise HTTPException(502, "Transport returned an invalid response.") from exc
    if not isinstance(result, dict):
        raise HTTPException(502, "Transport returned an invalid response.")
    return result
