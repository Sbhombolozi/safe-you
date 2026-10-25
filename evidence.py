"""Evidence metadata helpers. No files are written or uploaded by this module."""

import hashlib
import json
from datetime import datetime, timezone
from uuid import uuid4

from models import EvidenceEntry, EvidenceType


def sha256_hex(content: bytes) -> str:
    """Hash transient content bytes; callers must not persist plaintext locally."""
    return hashlib.sha256(content).hexdigest()


def build_entry_metadata(
    *,
    incident_id: str,
    evidence_type: EvidenceType,
    content: bytes,
    server_timestamp_utc: datetime,
    previous_entry_hash: str | None,
    encrypted_content_url: str,
    device_metadata: dict[str, object] | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> tuple[EvidenceEntry, str]:
    """Build an entry and its chain digest using a backend-confirmed timestamp.

    `content` should be passed only transiently after encryption/upload has been
    handled by a trusted adapter. This helper does not verify server time or
    upload content itself.
    """
    if server_timestamp_utc.tzinfo is None:
        raise ValueError("A timezone-aware backend timestamp is required")
    timestamp = server_timestamp_utc.astimezone(timezone.utc)
    content_hash = sha256_hex(content)
    entry = EvidenceEntry(
        id=str(uuid4()),
        incident_id=incident_id,
        type=evidence_type,
        timestamp_utc=timestamp,
        encrypted_content_url=encrypted_content_url,
        content_hash_sha256=content_hash,
        previous_entry_hash=previous_entry_hash,
        device_metadata=device_metadata or {},
        latitude=latitude,
        longitude=longitude,
        sync_status="uploaded",
    )
    chain_payload = {
        "id": entry.id,
        "incident_id": entry.incident_id,
        "type": entry.type,
        "timestamp_utc": entry.timestamp_utc.isoformat(),
        "content_hash_sha256": entry.content_hash_sha256,
        "previous_entry_hash": entry.previous_entry_hash,
    }
    encoded = json.dumps(chain_payload, sort_keys=True, separators=(",", ":")).encode()
    return entry, sha256_hex(encoded)
