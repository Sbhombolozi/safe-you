"""Supabase-backed trusted contacts screen."""

from collections.abc import Awaitable, Callable

import flet as ft

from components.surfaces import panel, section_header, status_chip
from models import EmergencyContact


@ft.component
def contacts_view(
    contacts: list[EmergencyContact],
    on_add: Callable[[str, str, str], Awaitable[bool]],
    on_remove: Callable[[str], Awaitable[None]],
    on_retry: Callable[[], Awaitable[None]],
    *,
    status: str,
    loading: bool,
    load_failed: bool,
    busy: bool,
    can_edit: bool,
) -> ft.Control:
    name, set_name = ft.use_state("")
    phone, set_phone = ft.use_state("")
    method, set_method = ft.use_state("sms")

    async def retry_contacts() -> None:
        await on_retry()

    contact_rows: list[ft.Control] = []
    if loading:
        contact_rows.append(
            panel(
                ft.Row(
                    controls=[
                        ft.ProgressRing(color=ft.Colors.PURPLE_700),
                        ft.Text("Loading your contacts…", color=ft.Colors.BLUE_GREY_700),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=16,
            )
        )
    elif load_failed:
        contact_rows.append(
            ft.Button(
                content=ft.Row(
                    controls=[ft.Icon(ft.Icons.REFRESH), ft.Text("Retry loading contacts")],
                    tight=True,
                    spacing=8,
                ),
                on_click=retry_contacts,
            )
        )
    elif not contacts:
        contact_rows.append(
            panel(
                ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.CONTACTS, size=30, color=ft.Colors.PURPLE_700),
                        ft.Text("Your trusted contacts will appear here.", color=ft.Colors.BLUE_GREY_700),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                    tight=True,
                ),
                padding=18,
            )
        )
    else:
        def make_remove_handler(contact_id: str):
            async def handler() -> None:
                await on_remove(contact_id)

            return handler

        for contact in contacts:
            contact_rows.append(
                panel(
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Icon(ft.Icons.CALL, color=ft.Colors.PURPLE_800),
                                width=42,
                                height=42,
                                alignment=ft.Alignment.CENTER,
                                bgcolor=ft.Colors.PURPLE_50,
                                border_radius=14,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(contact.name, weight=ft.FontWeight.BOLD),
                                    ft.Text(
                                        f"{contact.phone} · {contact.alert_method}",
                                        color=ft.Colors.BLUE_GREY_600,
                                        size=13,
                                    ),
                                    status_chip(f"PRIORITY {contact.priority_order}"),
                                ],
                                spacing=5,
                                tight=True,
                                expand=True,
                            ),
                            ft.Button(
                                content=ft.Icon(ft.Icons.DELETE_OUTLINE),
                                tooltip=f"Remove {contact.name}",
                                disabled=busy or not can_edit,
                                on_click=make_remove_handler(contact.id),
                            ),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=14,
                )
            )

    status_warning = bool(status) and not status.lower().startswith(
        ("contact saved", "contact removed")
    )
    status_slot = ft.Container(
        content=(
            ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.WARNING_AMBER if status_warning else ft.Icons.CHECK_CIRCLE_OUTLINE,
                        color=ft.Colors.DEEP_ORANGE_800 if status_warning else ft.Colors.PURPLE_800,
                    ),
                    ft.Text(status, color=ft.Colors.BLUE_GREY_800, expand=True),
                ],
                spacing=10,
            )
            if status
            else None
        ),
        padding=12 if status else 0,
        bgcolor=ft.Colors.AMBER_50 if status_warning else ft.Colors.PURPLE_50,
        border_radius=14,
    )

    async def add_contact() -> None:
        saved = await on_add(name, phone, method)
        if saved:
            set_name("")
            set_phone("")

    form = panel(
        ft.Column(
            controls=[
                ft.Text("Add a trusted person", size=18, weight=ft.FontWeight.BOLD),
                ft.TextField(
                    label="Name",
                    value=name,
                    disabled=busy or not can_edit,
                    prefix_icon=ft.Icons.PERSON_OUTLINE,
                    filled=True,
                    fill_color=ft.Colors.BLUE_GREY_50,
                    border_radius=14,
                    border_color=ft.Colors.BLUE_GREY_100,
                    content_padding=14,
                    on_change=lambda event: set_name(event.control.value or ""),
                ),
                ft.TextField(
                    label="Phone number",
                    value=phone,
                    disabled=busy or not can_edit,
                    keyboard_type=ft.KeyboardType.PHONE,
                    prefix_icon=ft.Icons.PHONE,
                    filled=True,
                    fill_color=ft.Colors.BLUE_GREY_50,
                    border_radius=14,
                    border_color=ft.Colors.BLUE_GREY_100,
                    content_padding=14,
                    on_change=lambda event: set_phone(event.control.value or ""),
                ),
                ft.TextField(
                    label="Alert method (sms / push / both)",
                    value=method,
                    disabled=busy or not can_edit,
                    prefix_icon=ft.Icons.NOTIFICATIONS_OUTLINED,
                    filled=True,
                    fill_color=ft.Colors.BLUE_GREY_50,
                    border_radius=14,
                    border_color=ft.Colors.BLUE_GREY_100,
                    content_padding=14,
                    on_change=lambda event: set_method(event.control.value or ""),
                ),
                ft.Button(
                    content=ft.Row(
                        controls=[ft.Icon(ft.Icons.PERSON_ADD), ft.Text("Add contact")],
                        tight=True,
                        spacing=8,
                    ),
                    bgcolor=ft.Colors.PURPLE_800,
                    color=ft.Colors.WHITE,
                    disabled=busy or not can_edit,
                    on_click=add_contact,
                ),
            ],
            spacing=12,
            tight=True,
        )
    )

    return ft.Column(
        controls=[
            panel(
                ft.Column(
                    controls=[
                        section_header(
                            ft.Icons.CONTACTS,
                            "Trusted contacts",
                            "People you may want to reach in an emergency.",
                        ),
                        ft.Row(
                            controls=[status_chip(f"{len(contacts)} / 7")],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                    ],
                    spacing=10,
                    tight=True,
                )
            ),
            status_slot,
            *contact_rows,
            ft.Text(
                "Only add people who know you are listing them as a trusted contact. Their name and number are personal information too.",
                size=12,
                color=ft.Colors.BLUE_GREY_600,
            ),
            form,
        ],
        spacing=12,
        tight=True,
    )
