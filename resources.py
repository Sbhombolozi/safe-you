from collections.abc import Callable

import flet as ft

from components.surfaces import panel, section_header, status_chip
from models import SupportResource


def resources_view(
    resources: list[SupportResource],
    query: str,
    region: str,
    accessible_only: bool,
    on_query: Callable[[str], None],
    on_region: Callable[[str], None],
    on_accessibility_toggle: Callable[[], None],
) -> ft.Control:
    resource_cards: list[ft.Control] = []
    if not resources:
        resource_cards.append(
            panel(
                ft.Text(
                    "No matching services yet. Try a broader search or region.",
                    color=ft.Colors.BLUE_GREY_700,
                )
            )
        )
    for resource in resources:
        resource_cards.append(
            panel(
                ft.Column(
                    controls=[
                        ft.Text(resource.name, size=18, weight=ft.FontWeight.BOLD),
                        status_chip(resource.category),
                        ft.Text(
                            f"{resource.region} · {resource.country}",
                            color=ft.Colors.BLUE_GREY_600,
                            size=13,
                        ),
                        ft.Text(resource.description, color=ft.Colors.BLUE_GREY_800),
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.ACCESSIBILITY, color=ft.Colors.PURPLE_800, size=20),
                                ft.Text(
                                    resource.accessibility_notes,
                                    color=ft.Colors.BLUE_GREY_700,
                                    expand=True,
                                ),
                            ],
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                    ],
                    spacing=10,
                    tight=True,
                ),
                padding=18,
            )
        )

    def toggle_accessibility() -> None:
        on_accessibility_toggle()

    return ft.Column(
        controls=[
            panel(
                section_header(
                    ft.Icons.LIBRARY_BOOKS,
                    "Support directory",
                    "Explore support options by place and need.",
                )
            ),
            panel(
                ft.Column(
                    controls=[
                        ft.TextField(
                            label="Search services",
                            value=query,
                            prefix_icon=ft.Icons.SEARCH,
                            filled=True,
                            fill_color=ft.Colors.BLUE_GREY_50,
                            border_radius=14,
                            border_color=ft.Colors.BLUE_GREY_100,
                            content_padding=14,
                            on_change=lambda event: on_query(event.control.value or ""),
                        ),
                        ft.TextField(
                            label="Region or country",
                            value=region,
                            prefix_icon=ft.Icons.PLACE,
                            filled=True,
                            fill_color=ft.Colors.BLUE_GREY_50,
                            border_radius=14,
                            border_color=ft.Colors.BLUE_GREY_100,
                            content_padding=14,
                            on_change=lambda event: on_region(event.control.value or ""),
                        ),
                        ft.Button(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.ACCESSIBILITY),
                                    ft.Text(
                                        "Accessible listings: " + ("on" if accessible_only else "off")
                                    ),
                                ],
                                tight=True,
                                spacing=8,
                            ),
                            bgcolor=ft.Colors.PURPLE_50,
                            color=ft.Colors.PURPLE_800,
                            on_click=toggle_accessibility,
                        ),
                        ft.Text(
                            "Plain-language details and accessibility notes are included where available.",
                            color=ft.Colors.BLUE_GREY_600,
                            size=13,
                        ),
                    ],
                    spacing=12,
                    tight=True,
                )
            ),
            *resource_cards,
            panel(
                ft.Text(
                    "Directory listings are starter pointers; verify local services and emergency numbers in your area.",
                    size=13,
                    color=ft.Colors.BLUE_GREY_600,
                ),
                padding=14,
            ),
        ],
        spacing=12,
        tight=True,
    )
