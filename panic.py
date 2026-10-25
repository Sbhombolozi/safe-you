from collections.abc import Callable

import flet as ft

from components.surfaces import panel, section_header, status_chip
from services.platform import PlatformCapabilities


def panic_view(
    capabilities: PlatformCapabilities,
    on_panic: Callable[[], None],
) -> ft.Control:
    platform_note = "Recording works while this app is open. Background recording is planned for Android."
    return ft.Column(
        controls=[
            panel(
                ft.Column(
                    controls=[
                        section_header(
                            ft.Icons.EMERGENCY,
                            "Panic button",
                            "A quick way to check the emergency action.",
                        ),
                        status_chip("ONE-TAP WHATSAPP ALERT", warning=True),
                        ft.Text(
                            "Pressing the button saves a private record of the time and your location, then opens WhatsApp with a ready-written message to your first trusted contact. Tap send to alert them. Fully automatic sending is planned for a later version.",
                            color=ft.Colors.BLUE_GREY_700,
                        ),
                        ft.Row(
                            controls=[
                                ft.Button(
                                    content=ft.Column(
                                        controls=[
                                            ft.Icon(ft.Icons.EMERGENCY, color=ft.Colors.WHITE, size=30),
                                            ft.Text(
                                                "SEND PANIC ALERT",
                                                color=ft.Colors.WHITE,
                                                size=15,
                                                weight=ft.FontWeight.BOLD,
                                                text_align=ft.TextAlign.CENTER,
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        spacing=10,
                                        tight=True,
                                    ),
                                    width=180,
                                    height=180,
                                    style=ft.ButtonStyle(
                                        shape=ft.CircleBorder(),
                                        bgcolor=ft.Colors.RED_700,
                                        color=ft.Colors.WHITE,
                                        padding=0,
                                    ),
                                    on_click=on_panic,
                                )
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=18,
                    tight=True,
                ),
                padding=22,
            ),
            panel(
                ft.Column(
                    controls=[
                        ft.Text("Important", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "This app does not replace emergency services. If you are in immediate danger, call 10111 (SAPS).",
                            color=ft.Colors.BLUE_GREY_700,
                        ),
                        ft.Divider(color=ft.Colors.BLUE_GREY_100),
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.PURPLE_800),
                                ft.Text(platform_note, color=ft.Colors.BLUE_GREY_700, expand=True),
                            ],
                            spacing=10,
                        ),
                    ],
                    spacing=12,
                    tight=True,
                ),
                padding=18,
            ),
        ],
        spacing=14,
        tight=True,
    )
