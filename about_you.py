"""Optional profile details screen shown after sign-in."""

from collections.abc import Awaitable, Callable

import flet as ft

from components.surfaces import panel, section_header
from services.profile_api import AGE_GROUPS, AREA_TYPES, PROVINCES


@ft.component
def about_you_view(
    on_save: Callable[[str | None, str | None, str | None], Awaitable[None]],
    on_skip: Callable[[], Awaitable[None]],
    busy: bool,
    status: str,
) -> ft.Control:
    age_value, set_age_value = ft.use_state(lambda: None)
    area_value, set_area_value = ft.use_state(lambda: None)
    province_value, set_province_value = ft.use_state(lambda: None)

    age_group = ft.Dropdown(
        label="Age group",
        options=[ft.DropdownOption(key=value, text=label) for value, label in AGE_GROUPS],
        value=age_value,
        on_select=lambda event: set_age_value(event.control.value or None),
    )
    area_type = ft.Dropdown(
        label="Area type",
        options=[ft.DropdownOption(key=value, text=label) for value, label in AREA_TYPES],
        value=area_value,
        on_select=lambda event: set_area_value(event.control.value or None),
    )
    province = ft.Dropdown(
        label="Province",
        options=[ft.DropdownOption(key=value, text=value) for value in PROVINCES],
        value=province_value,
        on_select=lambda event: set_province_value(event.control.value or None),
    )

    async def save() -> None:
        await on_save(
            age_group.value or None,
            area_type.value or None,
            province.value or None,
        )

    async def skip() -> None:
        await on_skip()

    controls: list[ft.Control] = [
        section_header(
            ft.Icons.PERSON_OUTLINE,
            "About you (optional)",
            "Optional profile details",
        ),
        ft.Text(
            "This helps us understand who needs support and where. It is optional, never shown with your name, and only used in anonymous totals. You can skip it.",
            color=ft.Colors.BLUE_GREY_700,
        ),
        age_group,
        area_type,
        province,
        ft.Row(
            controls=[
                ft.Button(
                    content="Save",
                    bgcolor=ft.Colors.PURPLE_800,
                    color=ft.Colors.WHITE,
                    disabled=busy,
                    on_click=save,
                ),
                ft.OutlinedButton(
                    content="Skip",
                    disabled=busy,
                    on_click=skip,
                ),
            ],
            spacing=12,
            wrap=True,
        ),
    ]
    if status:
        controls.append(ft.Text(status, color=ft.Colors.DEEP_ORANGE_800))

    return panel(
        ft.Column(
            controls=controls,
            spacing=14,
            tight=True,
        ),
        padding=24,
    )
