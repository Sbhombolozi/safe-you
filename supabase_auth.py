"""Supabase email/password Auth using Flet-preview-compatible async HTTP."""

from dataclasses import dataclass
from urllib.parse import quote

import httpx2 as httpx


# Supabase anon keys are public client identifiers, not privileged secrets.
SUPABASE_URL = "https://tyjbxpumbcqbdpprkjie.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR5amJ4cHVtYmNxYmRwcHJramllIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTA4MDIzMDEsImV4cCI6MjEwNjM3ODMwMX0.A9Rf7DQIIoqJhAwFnnlykaK-tmaWpVWvVZHC90JgALM"


@dataclass(frozen=True, slots=True)
class SupabaseAuthConfig:
    url: str
    anon_key: str


@dataclass(frozen=True, slots=True)
class AuthSession:
    access_token: str
    user_id: str


class AuthError(Exception):
    """A safe, user-displayable authentication failure."""


class SupabaseAuthClient:
    """Small async client for Supabase's email/password Auth endpoints."""

    def __init__(self, config: SupabaseAuthConfig) -> None:
        self.config = config
        if not config.url.startswith("https://") or not config.anon_key:
            raise ValueError("A valid HTTPS Supabase URL and anon key are required")

    async def _post(self, path: str, payload: dict[str, str]) -> dict[str, object]:
        headers = {
            "apikey": self.config.anon_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    f"{self.config.url}/auth/v1/{path}",
                    headers=headers,
                    json=payload,
                )
        except httpx.HTTPError as error:
            raise AuthError(
                "Could not reach Supabase. Check your connection and try again."
            ) from error

        if response.status_code < 200 or response.status_code >= 300:
            raise AuthError(self._message(response))
        try:
            result = response.json()
        except ValueError as error:
            raise AuthError(
                "Supabase returned an unreadable response. Please try again."
            ) from error
        if not isinstance(result, dict):
            raise AuthError("Supabase returned an unexpected response. Please try again.")
        return result

    @staticmethod
    def _message(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        if isinstance(payload, dict):
            message = (
                payload.get("msg")
                or payload.get("message")
                or payload.get("error_description")
                or payload.get("error")
            )
            if message:
                return str(message)
        return f"Supabase authentication failed (HTTP {response.status_code})."

    @staticmethod
    def _session(result: dict[str, object]) -> AuthSession:
        token = result.get("access_token")
        user = result.get("user")
        user_id = user.get("id") if isinstance(user, dict) else None
        if not token or not user_id:
            raise AuthError("Supabase did not return a complete signed-in session.")
        return AuthSession(access_token=str(token), user_id=str(user_id))

    async def sign_up(self, email: str, password: str) -> AuthSession | None:
        result = await self._post(
            "signup", {"email": email.strip(), "password": password}
        )
        if not result.get("access_token"):
            return None
        return self._session(result)

    async def sign_in(self, email: str, password: str) -> AuthSession:
        result = await self._post(
            f"token?grant_type={quote('password')}",
            {"email": email.strip(), "password": password},
        )
        return self._session(result)


# The client validates and holds the project configuration as the app starts.
supabase_auth = SupabaseAuthClient(
    SupabaseAuthConfig(url=SUPABASE_URL, anon_key=SUPABASE_ANON_KEY)
)


async def sign_up(email: str, password: str) -> AuthSession | None:
    return await supabase_auth.sign_up(email, password)


async def sign_in(email: str, password: str) -> AuthSession:
    return await supabase_auth.sign_in(email, password)
