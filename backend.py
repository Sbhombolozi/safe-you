"""Supabase integration boundary (intentionally unconfigured in this starter)."""

from datetime import datetime
from typing import Protocol

from models import EvidenceEntry


class EvidenceBackend(Protocol):
    async def get_server_timestamp(self) -> datetime: ...

    async def upload_encrypted_media(self, encrypted_bytes: bytes, object_key: str) -> str: ...

    async def save_entry_metadata(self, entry: EvidenceEntry, chain_hash: str) -> None: ...


class SupabaseGateway:
    """Placeholder for an authenticated, user-scoped Supabase client.

    Configure a trusted backend before implementing these methods. Never ship
    a Supabase service-role key in a Flet client; storage policies and server
    functions must enforce access, encryption, and chain ordering.
    """

    async def get_server_timestamp(self) -> datetime:
        raise NotImplementedError("Connect an authenticated backend for server time")

    async def upload_encrypted_media(self, encrypted_bytes: bytes, object_key: str) -> str:
        raise NotImplementedError("Configure encrypted cloud storage before uploading")

    async def save_entry_metadata(self, entry: EvidenceEntry, chain_hash: str) -> None:
        raise NotImplementedError("Configure authenticated metadata storage first")
