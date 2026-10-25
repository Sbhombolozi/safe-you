"""Authenticated Supabase API for incidents and private journal evidence."""

from datetime import datetime, timezone
import hashlib
import mimetypes
from uuid import uuid4
from urllib.parse import quote

import httpx2 as httpx

from models import EvidenceType, Incident, JournalEntry
from services.supabase_auth import SUPABASE_ANON_KEY, SUPABASE_URL


REST_URL = f"{SUPABASE_URL}/rest/v1"
STORAGE_URL = f"{SUPABASE_URL}/storage/v1"
BUCKET = "evidence"


class JournalApiError(Exception):
    """A safe, user-displayable Journal API failure."""


def _headers(access_token: str) -> dict[str, str]:
    return {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }


def _error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    if isinstance(payload, dict):
        message = (
            payload.get("message")
            or payload.get("msg")
            or payload.get("error_description")
            or payload.get("error")
            or payload.get("details")
        )
        if message:
            return str(message)
    return f"Supabase request failed (HTTP {response.status_code})."


def _decode_time(value: object) -> datetime:
    if not isinstance(value, str):
        raise JournalApiError("Supabase returned a record without a valid timestamp.")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise JournalApiError("Supabase returned an invalid timestamp.") from error
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)


def _decode_incident(row: object, expected_user_id: str) -> Incident:
    if not isinstance(row, dict) or str(row.get("user_id")) != expected_user_id:
        raise JournalApiError("Supabase returned an invalid incident record.")
    try:
        return Incident(
            id=str(row["id"]),
            created_at=_decode_time(row["created_at"]),
            status=str(row["status"]),
            entry_count=int(row["entry_count"]),
            last_updated=_decode_time(row["last_updated"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise JournalApiError("Supabase returned an incomplete incident record.") from error


def _decode_entry(row: object, expected_user_id: str, text: str | None = None) -> JournalEntry:
    if not isinstance(row, dict) or str(row.get("user_id")) != expected_user_id:
        raise JournalApiError("Supabase returned an invalid evidence record.")
    try:
        entry_type = str(row["entry_type"])
        if entry_type not in {"audio", "text", "photo", "video"}:
            raise ValueError("unsupported entry type")
        previous_hash = row.get("previous_entry_hash")
        storage_path_value = row.get("storage_path")
        row_text = row.get("text_content")
        if text is None and isinstance(row_text, str):
            text = row_text
        return JournalEntry(
            id=str(row["id"]),
            incident_id=str(row["incident_id"]),
            user_id=expected_user_id,
            entry_type=entry_type,  # type: ignore[arg-type]
            storage_path=str(storage_path_value) if storage_path_value else None,
            content_hash_sha256=str(row["content_hash_sha256"]),
            previous_entry_hash=str(previous_hash) if previous_hash else None,
            created_at=_decode_time(row["created_at"]),
            text_content=text,
        )
    except (KeyError, TypeError, ValueError) as error:
        raise JournalApiError("Supabase returned an incomplete evidence record.") from error


async def _rest_request(
    method: str,
    table: str,
    access_token: str,
    *,
    params: dict[str, str] | None = None,
    body: dict[str, object] | None = None,
) -> object:
    headers = _headers(access_token)
    headers["Prefer"] = "return=representation"
    if body is not None:
        headers["Content-Type"] = "application/json"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method,
                f"{REST_URL}/{table}",
                headers=headers,
                params=params,
                json=body,
            )
    except httpx.HTTPError as error:
        raise JournalApiError(
            "Could not reach Supabase. Check your connection and try again."
        ) from error
    if response.status_code < 200 or response.status_code >= 300:
        raise JournalApiError(_error_message(response))
    if not response.content:
        return None
    try:
        return response.json()
    except ValueError as error:
        raise JournalApiError("Supabase returned an unreadable Journal response.") from error


def _object_url(path: str) -> str:
    encoded_path = quote(path, safe="/")
    return f"{STORAGE_URL}/object/{BUCKET}/{encoded_path}"


async def _upload_object(access_token: str, path: str, content: bytes, content_type: str) -> None:
    headers = _headers(access_token)
    headers.update({"Content-Type": content_type, "x-upsert": "false"})
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                _object_url(path), headers=headers, content=content
            )
    except httpx.HTTPError as error:
        raise JournalApiError(
            "The evidence file could not reach secure storage. Check your connection and try again."
        ) from error
    if response.status_code < 200 or response.status_code >= 300:
        raise JournalApiError(f"Evidence upload failed: {_error_message(response)}")


async def _download_text(access_token: str, path: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(_object_url(path), headers=_headers(access_token))
    except httpx.HTTPError as error:
        raise JournalApiError("A saved text note could not be loaded from secure storage.") from error
    if response.status_code < 200 or response.status_code >= 300:
        raise JournalApiError(f"A saved text note could not be loaded: {_error_message(response)}")
    try:
        return response.content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise JournalApiError("A saved text note could not be decoded.") from error


async def _remove_object(access_token: str, path: str) -> None:
    """Best-effort cleanup if object upload succeeded but its row did not."""
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.delete(
                f"{STORAGE_URL}/object/{BUCKET}",
                headers={**_headers(access_token), "Content-Type": "application/json"},
                json={"prefixes": [path]},
            )
        if response.status_code >= 300:
            return
    except httpx.HTTPError:
        return


async def fetch_journal(
    access_token: str, user_id: str
) -> tuple[list[Incident], list[JournalEntry]]:
    incident_rows = await _rest_request(
        "GET",
        "incidents",
        access_token,
        params={
            "select": "id,user_id,created_at,status,entry_count,last_updated",
            "user_id": f"eq.{user_id}",
            "order": "last_updated.desc",
        },
    )
    entry_rows = await _rest_request(
        "GET",
        "evidence_entries",
        access_token,
        params={
            "select": "id,incident_id,user_id,entry_type,storage_path,text_content,content_hash_sha256,previous_entry_hash,created_at",
            "user_id": f"eq.{user_id}",
            "order": "created_at.desc,id.desc",
        },
    )
    if not isinstance(incident_rows, list) or not isinstance(entry_rows, list):
        raise JournalApiError("Supabase returned an unexpected Journal response.")
    incidents = [_decode_incident(row, user_id) for row in incident_rows]
    entries: list[JournalEntry] = []
    for row in entry_rows:
        if not isinstance(row, dict):
            raise JournalApiError("Supabase returned a malformed evidence record.")
        text = None
        if row.get("entry_type") == "text":
            stored_text = row.get("text_content")
            if isinstance(stored_text, str):
                text = stored_text
            elif row.get("storage_path"):
                # Compatibility for text evidence created before text_content existed.
                text = await _download_text(access_token, str(row["storage_path"]))
        entries.append(_decode_entry(row, user_id, text))
    return incidents, entries


async def create_incident(access_token: str, user_id: str) -> Incident:
    result = await _rest_request(
        "POST",
        "incidents",
        access_token,
        params={"select": "id,user_id,created_at,status,entry_count,last_updated"},
        body={"id": str(uuid4()), "user_id": user_id, "status": "open"},
    )
    if not isinstance(result, list) or not result:
        raise JournalApiError("Supabase did not confirm the new incident was saved.")
    return _decode_incident(result[0], user_id)


async def save_entry(
    access_token: str,
    user_id: str,
    incident_id: str,
    entry_type: EvidenceType,
    content: bytes,
    *,
    text_content: str | None = None,
    filename: str | None = None,
) -> JournalEntry:
    if entry_type not in {"audio", "text", "photo", "video"}:
        raise JournalApiError("Choose a supported evidence type.")

    entry_id = str(uuid4())
    if entry_type == "text":
        if text_content is None:
            try:
                text_content = content.decode("utf-8")
            except UnicodeDecodeError as error:
                raise JournalApiError("The note text could not be decoded.") from error
        if not text_content.strip():
            raise JournalApiError("This note is empty. Add some text and try again.")
        content = text_content.encode("utf-8")
        storage_path = None
    else:
        if not content:
            raise JournalApiError("This evidence file is empty. Choose another file.")
        storage_path = f"{user_id}/{incident_id}/{entry_id}"
        text_content = None

    content_hash = hashlib.sha256(content).hexdigest()
    latest = await _rest_request(
        "GET",
        "evidence_entries",
        access_token,
        params={
            "select": "content_hash_sha256",
            "user_id": f"eq.{user_id}",
            "order": "created_at.desc,id.desc",
            "limit": "1",
        },
    )
    if not isinstance(latest, list):
        raise JournalApiError("Could not verify the most recent journal entry.")
    previous_hash = None
    if latest:
        if not isinstance(latest[0], dict) or not latest[0].get("content_hash_sha256"):
            raise JournalApiError("The most recent journal entry has no valid content hash.")
        previous_hash = str(latest[0]["content_hash_sha256"])

    if storage_path is not None:
        content_type = mimetypes.guess_type(filename or "")[0] or "application/octet-stream"
        await _upload_object(access_token, storage_path, content, content_type)

    try:
        result = await _rest_request(
            "POST",
            "evidence_entries",
            access_token,
            params={
                "select": "id,incident_id,user_id,entry_type,storage_path,text_content,content_hash_sha256,previous_entry_hash,created_at"
            },
            body={
                "id": entry_id,
                "incident_id": incident_id,
                "user_id": user_id,
                "entry_type": entry_type,
                "storage_path": storage_path,
                "text_content": text_content,
                "content_hash_sha256": content_hash,
                "previous_entry_hash": previous_hash,
            },
        )
        if not isinstance(result, list) or not result:
            raise JournalApiError("Supabase did not confirm this entry was saved.")
        return _decode_entry(result[0], user_id, text_content)
    except Exception as error:
        if storage_path is not None:
            await _remove_object(access_token, storage_path)
        if isinstance(error, JournalApiError):
            raise
        raise JournalApiError(
            "This entry could not be saved to Supabase. Please retry."
        ) from error
