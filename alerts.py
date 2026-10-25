"""Emergency-alert integration boundary; this starter does not send messages."""

from models import EmergencyContact

MAX_EMERGENCY_CONTACTS = 7


def validate_contacts(contacts: list[EmergencyContact]) -> None:
    if len(contacts) > MAX_EMERGENCY_CONTACTS:
        raise ValueError("A maximum of seven emergency contacts is supported")
    priorities = [contact.priority_order for contact in contacts]
    if len(priorities) != len(set(priorities)):
        raise ValueError("Each emergency contact needs a unique priority order")
    for contact in contacts:
        if contact.alert_method not in {"sms", "push", "both"}:
            raise ValueError(f"Unsupported alert method for {contact.name}")
        if not contact.name.strip() or not contact.phone.strip():
            raise ValueError("Each contact needs a name and phone number")


async def send_emergency_alerts(
    contacts: list[EmergencyContact], *, summary: str, location_url: str | None
) -> None:
    """Fail closed until a tested, backend-mediated provider is configured."""
    validate_contacts(contacts)
    raise NotImplementedError(
        "No SMS or push provider is configured; no alert has been sent"
    )
