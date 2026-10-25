import asyncio
import re
from dataclasses import replace
from urllib.parse import quote

import flet as ft
import flet_geolocator as fgl

from components.surfaces import panel, status_chip
from models import EvidenceType, Incident, JournalEntry
from models.demo_data import SUPPORT_RESOURCES
from services.contacts import create_contact
from services.contacts_api import (
    ContactsApiError,
    delete_contact as delete_contact_request,
    fetch_contacts,
    save_contact,
)
from services.platform import detect_platform
from services.panic_api import PanicApiError, save_panic_alert
from services.profile_api import (
    ProfileApiError,
    fetch_admin_stats,
    fetch_is_admin,
    save_profile_details,
    touch_last_seen,
)
from services.journal_api import JournalApiError, create_incident as create_journal_incident_request, fetch_journal, save_entry
from services.resources import search_resources
from services.supabase_auth import AuthSession
from views.auth import auth_view
from views.about_you import about_you_view
from views.admin import admin_view
from views.contacts import contacts_view
from views.journal import journal_view
from views.panic import panic_view
from views.resources import resources_view


@ft.component
def render_shell(page: ft.Page, file_picker: ft.FilePicker) -> ft.Control:
    session, set_session = ft.use_state(lambda: None)
    about_done, set_about_done = ft.use_state(False)
    about_busy, set_about_busy = ft.use_state(False)
    about_status, set_about_status = ft.use_state("")
    is_admin, set_is_admin = ft.use_state(False)
    admin_stats, set_admin_stats = ft.use_state(lambda: None)
    admin_loading, set_admin_loading = ft.use_state(False)
    admin_status, set_admin_status = ft.use_state("")
    use_sample, set_use_sample = ft.use_state(False)
    selected_index, set_selected_index = ft.use_state(1)
    contacts, set_contacts = ft.use_state(lambda: [])
    contacts_status, set_contacts_status = ft.use_state("")
    contacts_loading, set_contacts_loading = ft.use_state(False)
    contacts_load_failed, set_contacts_load_failed = ft.use_state(False)
    contacts_loaded, set_contacts_loaded = ft.use_state(False)
    contacts_busy, set_contacts_busy = ft.use_state(False)
    notice, set_notice = ft.use_state("")
    query, set_query = ft.use_state("")
    region, set_region = ft.use_state("")
    accessible_only, set_accessible_only = ft.use_state(False)
    incidents, set_incidents = ft.use_state(lambda: [])
    journal_entries, set_journal_entries = ft.use_state(lambda: [])
    active_incident_id, set_active_incident_id = ft.use_state(lambda: None)
    journal_status, set_journal_status = ft.use_state("")
    journal_loading, set_journal_loading = ft.use_state(False)
    journal_load_failed, set_journal_load_failed = ft.use_state(False)
    journal_busy, set_journal_busy = ft.use_state(False)

    def check_admin_effect() -> None:
        if not about_done or session is None:
            return

        async def check_access() -> None:
            try:
                set_is_admin(await fetch_is_admin(session.access_token))
            except Exception:
                set_is_admin(False)

        asyncio.create_task(check_access())

    ft.use_effect(check_admin_effect, dependencies=[about_done])

    if session is None:
        return auth_view(set_session)

    if not about_done:
        async def save_about(
            age_group: str | None,
            area_type: str | None,
            province: str | None,
        ) -> None:
            set_about_busy(True)
            set_about_status("")
            try:
                await save_profile_details(
                    session.access_token,
                    session.user_id,
                    age_group,
                    area_type,
                    province,
                )
                await touch_last_seen(session.access_token, session.user_id)
                set_about_done(True)
            except ProfileApiError:
                set_about_status("Could not save your details. You can skip this step.")
            except Exception:
                set_about_status("Could not save your details. You can skip this step.")
            finally:
                set_about_busy(False)

        async def skip_about() -> None:
            try:
                await touch_last_seen(session.access_token, session.user_id)
            except Exception:
                pass
            set_about_done(True)

        return about_you_view(
            save_about,
            skip_about,
            about_busy,
            about_status,
        )

    capabilities = detect_platform(page.platform)

    async def load_contacts() -> None:
        set_contacts_loading(True)
        set_contacts_load_failed(False)
        set_contacts_loaded(False)
        set_contacts_status("")
        try:
            saved_contacts = await fetch_contacts(
                session.access_token,
                session.user_id,
            )
            set_contacts(saved_contacts)
            set_contacts_loaded(True)
        except ContactsApiError as error:
            set_contacts_load_failed(True)
            set_contacts_status(f"Could not load contacts: {error}")
        except Exception:
            set_contacts_load_failed(True)
            set_contacts_status("Could not load contacts. Please try again.")
        finally:
            set_contacts_loading(False)

    async def add_contact(name: str, phone: str, method: str) -> bool:
        if len(contacts) >= 7:
            set_contacts_status("Maximum of 7 contacts reached. Remove one before adding another.")
            return False

        set_contacts_busy(True)
        set_contacts_status("")
        try:
            candidate = create_contact(contacts, name, phone, method)
            saved = await save_contact(session.access_token, session.user_id, candidate)
            set_contacts(
                lambda current: sorted(
                    [*current, saved], key=lambda item: item.priority_order
                )
            )
            set_contacts_status("Contact saved to your account.")
            return True
        except ValueError as error:
            set_contacts_status(str(error))
        except ContactsApiError as error:
            set_contacts_status(f"Could not save contact: {error}")
        except Exception:
            set_contacts_status("Could not save contact. Please try again.")
        finally:
            set_contacts_busy(False)
        return False

    async def remove_contact(contact_id: str) -> None:
        set_contacts_busy(True)
        set_contacts_status("")
        try:
            await delete_contact_request(
                session.access_token,
                session.user_id,
                contact_id,
            )
            set_contacts(
                lambda current: [contact for contact in current if contact.id != contact_id]
            )
            set_contacts_status("Contact removed from your account.")
        except ContactsApiError as error:
            set_contacts_status(f"Could not delete contact: {error}")
        except Exception:
            set_contacts_status("Could not delete contact. Please try again.")
        finally:
            set_contacts_busy(False)

    async def load_journal() -> None:
        set_journal_loading(True)
        set_journal_load_failed(False)
        set_journal_status("")
        try:
            saved_incidents, saved_entries = await fetch_journal(
                session.access_token,
                session.user_id,
            )
            set_incidents(saved_incidents)
            set_journal_entries(saved_entries)
            selected = next(
                (item for item in saved_incidents if item.id == active_incident_id and item.status == "open"),
                None,
            )
            if selected is None:
                selected = next((item for item in saved_incidents if item.status == "open"), None)
            set_active_incident_id(selected.id if selected else None)
        except JournalApiError as error:
            set_journal_load_failed(True)
            set_journal_status(f"Could not load journal: {error}")
        except Exception:
            set_journal_load_failed(True)
            set_journal_status("Could not load your journal. Please try again.")
        finally:
            set_journal_loading(False)

    async def create_incident() -> None:
        set_journal_busy(True)
        set_journal_status("")
        try:
            incident = await create_journal_incident_request(
                session.access_token,
                session.user_id,
            )
            set_incidents(lambda current: [incident, *current])
            set_active_incident_id(incident.id)
            set_journal_status("Incident created and ready for an entry.")
        except JournalApiError as error:
            set_journal_status(f"Could not create incident: {error}")
        except Exception:
            set_journal_status("Could not create the incident. Please try again.")
        finally:
            set_journal_busy(False)

    async def save_journal_entry(
        incident_id: str,
        entry_type: EvidenceType,
        content: bytes,
        *,
        text_content: str | None = None,
        filename: str | None = None,
    ) -> bool:
        if journal_busy:
            set_journal_status("Another journal save is in progress. Please wait a moment and try again.")
            return False
        incident = next((item for item in incidents if item.id == incident_id), None)
        if incident is None or incident.status != "open":
            set_journal_status("Choose an open incident before adding evidence.")
            return False
        set_journal_busy(True)
        set_journal_status("")
        try:
            saved = await save_entry(
                session.access_token,
                session.user_id,
                incident_id,
                entry_type,
                content,
                text_content=text_content,
                filename=filename,
            )
            set_journal_entries(lambda current: [saved, *current])
            set_incidents(
                lambda current: [
                    replace(item, entry_count=item.entry_count + 1, last_updated=saved.created_at)
                    if item.id == incident_id
                    else item
                    for item in current
                ]
            )
            set_journal_status("Saved securely to your private evidence storage.")
            return True
        except JournalApiError as error:
            set_journal_status(f"Could not save this entry: {error}")
        except Exception:
            set_journal_status("Could not save this entry. Please check your connection and try again.")
        finally:
            set_journal_busy(False)
        return False

    async def add_text_entry(incident_id: str, text: str) -> bool:
        note = text.strip()
        if not note:
            set_journal_status("Write a note before saving it.")
            return False
        return await save_journal_entry(
            incident_id,
            "text",
            note.encode("utf-8"),
            text_content=note,
        )

    async def upload_journal_media(
        incident_id: str,
        entry_type: EvidenceType,
        content: bytes,
        filename: str,
    ) -> bool:
        return await save_journal_entry(
            incident_id,
            entry_type,
            content,
            filename=filename,
        )

    def select_incident(incident_id: str) -> None:
        set_active_incident_id(incident_id or None)
        set_journal_status("")

    async def panic_action() -> None:
        latitude = None
        longitude = None
        try:
            geolocator = fgl.Geolocator()
            position = await asyncio.wait_for(
                geolocator.get_current_position(),
                timeout=5.0,
            )
            latitude = position.latitude
            longitude = position.longitude
            if latitude is None or longitude is None:
                latitude = None
                longitude = None
        except Exception:
            # Location is optional; always continue with the panic press.
            latitude = None
            longitude = None

        try:
            await save_panic_alert(
                session.access_token,
                session.user_id,
                latitude,
                longitude,
            )
        except PanicApiError as error:
            set_notice(f"Could not record the panic press: {error}")
            return
        except Exception:
            set_notice("Could not record the panic press. Please try again.")
            return

        emergency_contacts = contacts
        if not emergency_contacts or not contacts_loaded:
            try:
                emergency_contacts = await fetch_contacts(
                    session.access_token,
                    session.user_id,
                )
                set_contacts(emergency_contacts)
                set_contacts_loaded(True)
            except Exception:
                set_notice("Panic press recorded, but your emergency contacts could not be loaded.")
                return

        if not emergency_contacts:
            set_notice(
                "Panic press recorded, but you have no emergency contacts yet. Add one in the Contacts tab."
            )
            return

        contact = min(emergency_contacts, key=lambda item: item.priority_order)
        phone_number = re.sub(r"[^0-9]", "", contact.phone)
        if phone_number.startswith("0"):
            phone_number = "27" + phone_number[1:]

        message = "EMERGENCY: I need help. This is an alert from Safe YOU."
        if latitude is not None and longitude is not None:
            message += f" My location: https://maps.google.com/?q={latitude},{longitude}"
        whatsapp_url = f"https://wa.me/{phone_number}?text={quote(message, safe='')}"

        try:
            if not phone_number:
                raise ValueError("The contact has no valid phone number.")
            await ft.UrlLauncher().launch_url(whatsapp_url)
        except Exception:
            set_notice("Panic press recorded, but WhatsApp could not be opened.")
            return

        set_notice(
            f"Panic press recorded. WhatsApp opened for {contact.name}. Tap send to alert them. Automatic sending is not connected yet."
        )

    async def load_admin() -> None:
        set_admin_loading(True)
        set_admin_status("")
        try:
            set_admin_stats(await fetch_admin_stats(session.access_token))
        except Exception:
            set_admin_status("Could not load the dashboard.")
        finally:
            set_admin_loading(False)

    screens = [
        journal_view(
            incidents,
            journal_entries,
            active_incident_id,
            file_picker,
            select_incident,
            create_incident,
            add_text_entry,
            upload_journal_media,
            load_journal,
            status=journal_status,
            loading=journal_loading,
            load_failed=journal_load_failed,
            busy=journal_busy,
        ),
        panic_view(capabilities, panic_action),
        contacts_view(
            contacts,
            add_contact,
            remove_contact,
            load_contacts,
            status=contacts_status,
            loading=contacts_loading,
            load_failed=contacts_load_failed,
            busy=contacts_busy,
            can_edit=contacts_loaded and not contacts_loading,
        ),
        resources_view(
            search_resources(
                SUPPORT_RESOURCES,
                query=query,
                region=region,
                accessible_only=accessible_only,
            ),
            query,
            region,
            accessible_only,
            set_query,
            set_region,
            lambda: set_accessible_only(not accessible_only),
        ),
    ]
    if is_admin:
        screens.append(
            admin_view(
                admin_stats,
                admin_loading,
                admin_status,
                load_admin,
                use_sample,
                set_use_sample,
            )
        )

    destinations = [
        ft.NavigationBarDestination(icon=ft.Icons.NOTES, label="Journal"),
        ft.NavigationBarDestination(icon=ft.Icons.EMERGENCY, label="Panic"),
        ft.NavigationBarDestination(icon=ft.Icons.CONTACTS, label="Contacts"),
        ft.NavigationBarDestination(icon=ft.Icons.LIBRARY_BOOKS, label="Resources"),
    ]
    if is_admin:
        destinations.append(
            ft.NavigationBarDestination(icon=ft.Icons.INSIGHTS, label="Admin")
        )

    async def change_tab(event) -> None:
        index = event.control.selected_index
        set_selected_index(index)
        set_notice("")
        try:
            await touch_last_seen(session.access_token, session.user_id)
        except Exception:
            pass
        if index == 0:
            await load_journal()
        elif index == 2:
            await load_contacts()
        elif index == 4 and is_admin:
            await load_admin()

    platform_label = (
        "Android prototype"
        if capabilities.is_android
        else "Web preview"
        if capabilities.foreground_capture_only
        else capabilities.platform.title()
    )
    header = panel(
        ft.Row(
            controls=[
                ft.Container(
                    content=ft.Icon(ft.Icons.PRIVACY_TIP, size=26, color=ft.Colors.PURPLE_800),
                    width=52,
                    height=52,
                    alignment=ft.Alignment.CENTER,
                    bgcolor=ft.Colors.PURPLE_50,
                    border_radius=18,
                ),
                ft.Column(
                    controls=[
                        ft.Text("Safe YOU", size=22, weight=ft.FontWeight.BOLD),
                        ft.Text("Your voice. Your evidence. Your safety.", color=ft.Colors.BLUE_GREY_600),
                        status_chip(platform_label, warning=capabilities.is_android),
                    ],
                    spacing=5,
                    tight=True,
                    expand=True,
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=14,
        ),
        padding=14,
    )
    notice_banner = ft.Container(
        content=(
            ft.Row(
                controls=[
                    ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.DEEP_ORANGE_800),
                    ft.Text(notice, color=ft.Colors.BLUE_GREY_900, expand=True),
                ],
                spacing=10,
            )
            if notice
            else None
        ),
        padding=12 if notice else 0,
        bgcolor=ft.Colors.AMBER_50 if notice else ft.Colors.TRANSPARENT,
        border_radius=14,
    )

    return ft.Container(
        expand=True,
        padding=18,
        content=ft.Column(
            controls=[
                header,
                notice_banner,
                ft.ListView(
                    controls=[screens[selected_index]],
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,
                    spacing=12,
                ),
                ft.NavigationBar(
                    destinations=destinations,
                    selected_index=selected_index,
                    on_change=change_tab,
                    bgcolor=ft.Colors.WHITE,
                    indicator_color=ft.Colors.PURPLE_100,
                ),
            ],
            expand=True,
            spacing=12,
        ),
    )
