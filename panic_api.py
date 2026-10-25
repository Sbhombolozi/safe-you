"""Saves a panic press to the user's Supabase panic_alerts table."""

import httpx2 as httpx

from services.supabase_auth import SUPABASE_ANON_KEY, SUPABASE_URL


class PanicApiError(Exception):
    """A safe, user-displayable Panic API failure."""


PANIC_URL = f"{SUPABASE_URL}/rest/v1/panic_alerts"


def _response_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    if isinstance(payload, dict):
        message = payload.get("message") or payload.get("details") or payload.get("hint")
        if message:
            return str(message)
    return f"Supabase request failed (HTTP {response.status_code})."


async def save_panic_alert(
    access_token: str,
    user_id: str,
    latitude: float | None = None,
    longitude: float | None = None,
) -> str:
    """Record a panic press and return the new alert's id."""
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    body = {
        "user_id": user_id,
        "latitude": latitude,
        "longitude": longitude,
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                PANIC_URL,
                headers=headers,
                params={"select": "id"},
                json=body,
            )
    except httpx.HTTPError as error:
        raise PanicApiError(
            "Could not reach Supabase. Check your connection and try again."
        ) from error

    if response.status_code < 200 or response.status_code >= 300:
        raise PanicApiError(_response_message(response))
    try:
        result = response.json()
    except ValueError as error:
        raise PanicApiError("Supabase returned an unreadable alert response.") from error
    if not isinstance(result, list) or not result:
        raise PanicApiError("Supabase did not confirm that the alert was saved.")
    return str(result[0]["id"])
