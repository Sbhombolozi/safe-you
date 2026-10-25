"""Optional profile details, last-seen tracking and admin statistics."""

from datetime import datetime, timezone

import httpx2 as httpx

from services.supabase_auth import SUPABASE_ANON_KEY, SUPABASE_URL


class ProfileApiError(Exception):
    """A safe, user-displayable profile API failure."""


PROFILES_URL = f"{SUPABASE_URL}/rest/v1/profiles"
RPC_URL = f"{SUPABASE_URL}/rest/v1/rpc"

AGE_GROUPS = [
    ("under_18", "Under 18"),
    ("18_24", "18-24"),
    ("25_34", "25-34"),
    ("35_44", "35-44"),
    ("45_54", "45-54"),
    ("55_plus", "55 and over"),
    ("prefer_not_to_say", "Prefer not to say"),
]
AREA_TYPES = [
    ("urban", "Urban"),
    ("rural", "Rural"),
    ("informal_settlement", "Informal settlement"),
    ("prefer_not_to_say", "Prefer not to say"),
]
PROVINCES = [
    "Eastern Cape",
    "Free State",
    "Gauteng",
    "KwaZulu-Natal",
    "Limpopo",
    "Mpumalanga",
    "Northern Cape",
    "North West",
    "Western Cape",
]


def _headers(access_token: str, prefer: str | None = None) -> dict[str, str]:
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def _message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    if isinstance(payload, dict):
        text = payload.get("message") or payload.get("details") or payload.get("hint")
        if text:
            return str(text)
    return f"Supabase request failed (HTTP {response.status_code})."


async def _send(method: str, url: str, access_token: str, *, params=None, body=None, prefer=None):
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.request(
                method,
                url,
                headers=_headers(access_token, prefer),
                params=params,
                json=body,
            )
    except httpx.HTTPError as error:
        raise ProfileApiError("Could not reach Supabase. Check your connection and try again.") from error
    if response.status_code < 200 or response.status_code >= 300:
        raise ProfileApiError(_message(response))
    if not response.content:
        return None
    try:
        return response.json()
    except ValueError as error:
        raise ProfileApiError("Supabase returned an unreadable response.") from error


async def _update_own_profile(access_token: str, user_id: str, fields: dict) -> None:
    result = await _send(
        "PATCH",
        PROFILES_URL,
        access_token,
        params={"id": f"eq.{user_id}", "select": "id"},
        body=fields,
        prefer="return=representation",
    )
    if isinstance(result, list) and result:
        return
    await _send(
        "POST",
        PROFILES_URL,
        access_token,
        body={"id": user_id, **fields},
        prefer="return=minimal",
    )


async def save_profile_details(
    access_token: str,
    user_id: str,
    age_group: str | None,
    area_type: str | None,
    province: str | None,
) -> None:
    await _update_own_profile(
        access_token,
        user_id,
        {"age_group": age_group, "area_type": area_type, "province": province},
    )


async def touch_last_seen(access_token: str, user_id: str) -> None:
    await _update_own_profile(
        access_token,
        user_id,
        {"last_seen_at": datetime.now(timezone.utc).isoformat()},
    )


async def fetch_is_admin(access_token: str) -> bool:
    result = await _send("POST", f"{RPC_URL}/is_admin", access_token, body={})
    return result is True


async def fetch_admin_stats(access_token: str) -> dict:
    result = await _send("POST", f"{RPC_URL}/admin_stats", access_token, body={})
    if not isinstance(result, dict):
        raise ProfileApiError("Supabase returned unexpected admin statistics.")
    return result
