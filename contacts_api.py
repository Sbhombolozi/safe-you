"""Authenticated CRUD for the user's Supabase contacts rows."""

import httpx2 as httpx

from models import EmergencyContact
from services.supabase_auth import SUPABASE_ANON_KEY, SUPABASE_URL


class ContactsApiError(Exception):
    """A safe, user-displayable Contacts API failure."""


CONTACTS_URL = f"{SUPABASE_URL}/rest/v1/contacts"


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


async def _request(
    method: str,
    access_token: str,
    *,
    params: dict[str, str] | None = None,
    body: dict[str, object] | None = None,
) -> object:
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Prefer": "return=representation",
    }
    if body is not None:
        headers["Content-Type"] = "application/json"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.request(
                method,
                CONTACTS_URL,
                headers=headers,
                params=params,
                json=body,
            )
    except httpx.HTTPError as error:
        raise ContactsApiError(
            "Could not reach Supabase. Check your connection and try again."
        ) from error

    if response.status_code < 200 or response.status_code >= 300:
        raise ContactsApiError(_response_message(response))
    if not response.content:
        return None
    try:
        return response.json()
    except ValueError as error:
        raise ContactsApiError("Supabase returned an unreadable contacts response.") from error


def _decode_contact(row: object, expected_user_id: str) -> EmergencyContact:
    if not isinstance(row, dict):
        raise ContactsApiError("Supabase returned a malformed contact record.")
    try:
        user_id = str(row["user_id"])
        method = str(row["alert_method"])
        if user_id != expected_user_id:
            raise ContactsApiError("Supabase returned a contact for another user.")
        if method not in {"sms", "push", "both"}:
            raise ValueError("unsupported alert method")
        return EmergencyContact(
            id=str(row["id"]),
            name=str(row["name"]),
            phone=str(row["phone"]),
            alert_method=method,
            priority_order=int(row["priority_order"]),
        )
    except ContactsApiError:
        raise
    except (KeyError, TypeError, ValueError) as error:
        raise ContactsApiError("Supabase returned an invalid contact record.") from error


async def fetch_contacts(access_token: str, user_id: str) -> list[EmergencyContact]:
    result = await _request(
        "GET",
        access_token,
        params={
            "select": "id,user_id,name,phone,alert_method,priority_order",
            "user_id": f"eq.{user_id}",
            "order": "priority_order.asc",
        },
    )
    if not isinstance(result, list):
        raise ContactsApiError("Supabase returned an unexpected contacts list.")
    return [_decode_contact(row, user_id) for row in result]


async def save_contact(
    access_token: str, user_id: str, contact: EmergencyContact
) -> EmergencyContact:
    result = await _request(
        "POST",
        access_token,
        params={"select": "id,user_id,name,phone,alert_method,priority_order"},
        body={
            "id": contact.id,
            "user_id": user_id,
            "name": contact.name,
            "phone": contact.phone,
            "alert_method": contact.alert_method,
            "priority_order": contact.priority_order,
        },
    )
    if not isinstance(result, list) or not result:
        raise ContactsApiError("Supabase did not confirm that the contact was saved.")
    return _decode_contact(result[0], user_id)


async def delete_contact(access_token: str, user_id: str, contact_id: str) -> None:
    result = await _request(
        "DELETE",
        access_token,
        params={
            "id": f"eq.{contact_id}",
            "user_id": f"eq.{user_id}",
            "select": "id",
        },
    )
    if not isinstance(result, list) or not result:
        raise ContactsApiError("Contact was not found or could not be deleted.")
