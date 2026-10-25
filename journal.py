"""Supabase-backed incident journal screen."""

from collections.abc import Awaitable, Callable

import flet as ft

from components.surfaces import panel, section_header, status_chip
from models import EvidenceType, Incident, JournalEntry


@ft.component
def journal_view(
    incidents: list[Incident],
    entries: list[JournalEntry],
    active_incident_id: str | None,
    file_picker: ft.FilePicker,
    on_select_incident: Callable[[str], None],
    on_create_incident: Callable[[], Awaitable[None]],
    on_add_text: Callable[[str, str], Awaitable[bool]],
    on_upload_media: Callable[[str, EvidenceType, bytes, str], Awaitable[bool]],
    on_retry: Callable[[], Awaitable[None]],
    *,
    status: str,
    loading: bool,
    load_failed: bool,
    busy: bool,
) -> ft.Control:
    note_text, set_note_text = ft.use_state("")
    local_status, set_local_status = ft.use_state("")

    active_incident = next(
        (incident for incident in incidents if incident.id == active_incident_id), None
    )
    is_open = active_incident is not None and active_incident.status == "open"
    incident_options = [
        ft.DropdownOption(
            key=incident.id,
            text=f"Incident · {incident.created_at.strftime('%Y-%m-%d')} · {incident.entry_count} entries",
        )
        for incident in incidents
    ]

    async def create_incident() -> None:
        set_local_status("")
        await on_create_incident()

    async def add_note() -> None:
        if active_incident_id is None:
            set_local_status("Create or select an open incident before saving a note.")
            return
        saved = await on_add_text(active_incident_id, note_text)
        if saved:
            set_note_text("")
            set_local_status("")

    async def pick_and_upload(entry_type: EvidenceType) -> None:
        if active_incident_id is None:
            set_local_status("Create or select an open incident before adding evidence.")
            return
        set_local_status("")
        picker_type = {
            "photo": ft.FilePickerFileType.IMAGE,
            "audio": ft.FilePickerFileType.AUDIO,
            "video": ft.FilePickerFileType.VIDEO,
        }[entry_type]
        try:
            picked_files = await file_picker.pick_files(
                dialog_title=f"Choose {entry_type} evidence",
                file_type=picker_type,
                allow_multiple=False,
                with_data=True,
            )
        except Exception:
            set_local_status("Could not open the file picker. Please try again.")
            return
        if not picked_files:
            return
        picked_file = picked_files[0]
        if picked_file.bytes is None:
            set_local_status("The selected file could not be read into temporary upload memory.")
            return
        set_local_status("")
        await on_upload_media(
            active_incident_id,
            entry_type,
            picked_file.bytes,
            picked_file.name,
        )

    async def pick_photo() -> None:
        await pick_and_upload("photo")

    async def pick_audio() -> None:
        await pick_and_upload("audio")

    async def pick_video() -> None:
        await pick_and_upload("video")

    async def retry_journal() -> None:
        await on_retry()

    visible_entries = [
        entry for entry in entries if entry.incident_id == active_incident_id
    ]
    rows: list[ft.Control] = []
    if loading:
        rows.append(
            panel(
                ft.Row(
                    controls=[
                        ft.ProgressRing(color=ft.Colors.PURPLE_700),
                        ft.Text("Loading incidents and evidence…", color=ft.Colors.BLUE_GREY_700),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=16,
            )
        )
    elif load_failed:
        rows.append(
            ft.Button(
                content=ft.Row(
                    controls=[ft.Icon(ft.Icons.REFRESH), ft.Text("Retry loading journal")],
                    tight=True,
                    spacing=8,
                ),
                on_click=retry_journal,
            )
        )
    elif active_incident is None:
        rows.append(
            panel(
                ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.FOLDER_OPEN, size=30, color=ft.Colors.PURPLE_700),
                        ft.Text("Start an incident to add a note or evidence."),
                    ],
                    spacing=8,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    tight=True,
                ),
                padding=18,
            )
        )
    elif not visible_entries:
        rows.append(
            panel(
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.LOCK_OUTLINE, color=ft.Colors.PURPLE_800),
                        ft.Text("Entries for this incident will appear here after they are saved."),
                    ],
                    spacing=10,
                ),
                padding=16,
            )
        )
    else:
        for entry in visible_entries:
            icon = {
                "text": ft.Icons.NOTES,
                "photo": ft.Icons.IMAGE,
                "audio": ft.Icons.MIC,
                "video": ft.Icons.VIDEOCAM,
            }[entry.entry_type]
            detail_controls: list[ft.Control] = [
                ft.Row(
                    controls=[
                        ft.Text(entry.entry_type.title(), weight=ft.FontWeight.BOLD, expand=True),
                        status_chip(entry.created_at.strftime("%Y-%m-%d · %H:%M UTC")),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text(
                    f"SHA-256  {entry.content_hash_sha256}",
                    size=12,
                    color=ft.Colors.BLUE_GREY_600,
                    selectable=True,
                ),
            ]
            if entry.entry_type == "text":
                detail_controls.insert(
                    1,
                    ft.Text(
                        entry.text_content or "No text content was returned.",
                        color=ft.Colors.BLUE_GREY_800,
                        selectable=True,
                    ),
                )
            detail_controls.append(
                ft.Text(
                    "Linked to the previous entry" if entry.previous_entry_hash else "First entry in this account",
                    size=12,
                    color=ft.Colors.PURPLE_800,
                )
            )
            rows.append(
                panel(
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Icon(icon, color=ft.Colors.PURPLE_800),
                                width=42,
                                height=42,
                                alignment=ft.Alignment.CENTER,
                                bgcolor=ft.Colors.PURPLE_50,
                                border_radius=14,
                            ),
                            ft.Column(
                                controls=detail_controls,
                                spacing=7,
                                tight=True,
                                expand=True,
                            ),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    padding=14,
                )
            )

    message = status or local_status
    is_warning = bool(message) and not message.lower().startswith(("saved", "incident created"))
    status_slot = ft.Container(
        content=(
            ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.WARNING_AMBER if is_warning else ft.Icons.CHECK_CIRCLE_OUTLINE,
                        color=ft.Colors.DEEP_ORANGE_800 if is_warning else ft.Colors.PURPLE_800,
                    ),
                    ft.Text(message, color=ft.Colors.BLUE_GREY_800, expand=True),
                ],
                spacing=10,
            )
            if message
            else None
        ),
        padding=12 if message else 0,
        bgcolor=ft.Colors.AMBER_50 if is_warning else ft.Colors.PURPLE_50,
        border_radius=14,
    )

    active_content = active_incident is not None and is_open and not busy and not loading
    if incidents:
        incident_controls: list[ft.Control] = [
            ft.Dropdown(
                label="Choose an incident",
                hint_text="Select an open incident",
                value=active_incident_id,
                options=incident_options,
                disabled=busy or loading,
                on_select=lambda event: on_select_incident(event.control.value or ""),
            ),
            ft.Button(
                content=ft.Row(
                    controls=[ft.Icon(ft.Icons.ADD), ft.Text("New Incident")],
                    tight=True,
                    spacing=8,
                ),
                disabled=busy or loading,
                on_click=create_incident,
            ),
        ]
    else:
        incident_controls = [
            ft.Button(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE),
                        ft.Text("Start a New Incident", size=17, weight=ft.FontWeight.BOLD),
                    ],
                    tight=True,
                    spacing=10,
                ),
                bgcolor=ft.Colors.PURPLE_800,
                color=ft.Colors.WHITE,
                expand=True,
                disabled=busy or loading,
                on_click=create_incident,
            )
        ]

    composer = panel(
        ft.Column(
            controls=[
                ft.Text("Add to this incident", size=18, weight=ft.FontWeight.BOLD),
                ft.TextField(
                    label="Write a note",
                    hint_text="Add only what feels useful right now.",
                    value=note_text,
                    multiline=True,
                    min_lines=3,
                    max_lines=6,
                    disabled=not active_content,
                    filled=True,
                    fill_color=ft.Colors.BLUE_GREY_50,
                    border_radius=14,
                    border_color=ft.Colors.BLUE_GREY_100,
                    content_padding=14,
                    on_change=lambda event: set_note_text(event.control.value or ""),
                ),
                ft.Button(
                    content=ft.Row(
                        controls=[ft.Icon(ft.Icons.CLOUD_UPLOAD_OUTLINED), ft.Text("Save note securely")],
                        tight=True,
                        spacing=8,
                    ),
                    bgcolor=ft.Colors.PURPLE_800,
                    color=ft.Colors.WHITE,
                    disabled=not active_content or not note_text.strip(),
                    on_click=add_note,
                ),
                ft.Divider(color=ft.Colors.BLUE_GREY_100),
                ft.Text("Upload a file already on this device", weight=ft.FontWeight.W_600),
                ft.Row(
                    controls=[
                        ft.Button(
                            content=ft.Row(controls=[ft.Icon(ft.Icons.IMAGE), ft.Text("Photo")], tight=True, spacing=6),
                            disabled=not active_content,
                            on_click=pick_photo,
                        ),
                        ft.Button(
                            content=ft.Row(controls=[ft.Icon(ft.Icons.MIC), ft.Text("Audio")], tight=True, spacing=6),
                            disabled=not active_content,
                            on_click=pick_audio,
                        ),
                        ft.Button(
                            content=ft.Row(controls=[ft.Icon(ft.Icons.VIDEOCAM), ft.Text("Video")], tight=True, spacing=6),
                            disabled=not active_content,
                            on_click=pick_video,
                        ),
                    ],
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                ),
                ft.Text(
                    "Selected files are read into temporary memory, hashed, and uploaded directly to the private evidence bucket.",
                    size=12,
                    color=ft.Colors.BLUE_GREY_600,
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
                            ft.Icons.NOTES,
                            "Evidence journal",
                            "Keep incident notes and files together, one step at a time.",
                        ),
                        ft.Divider(color=ft.Colors.BLUE_GREY_100),
                        ft.Row(
                            controls=[
                                ft.Text(f"{len(incidents)} incidents", color=ft.Colors.BLUE_GREY_700),
                                status_chip("PRIVATE UPLOADS"),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        *incident_controls,
                    ],
                    spacing=12,
                    tight=True,
                )
            ),
            status_slot,
            composer,
            *rows,
        ],
        spacing=12,
        tight=True,
    )
