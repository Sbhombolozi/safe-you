"""Admin-only aggregate statistics dashboard."""

from collections.abc import Awaitable, Callable

import flet as ft

from components.surfaces import panel, section_header, status_chip


_LABELS = {
    "under_18": "Under 18",
    "18_24": "18-24",
    "25_34": "25-34",
    "35_44": "35-44",
    "45_54": "45-54",
    "55_plus": "55 and over",
    "prefer_not_to_say": "Prefer not to say",
    "urban": "Urban",
    "rural": "Rural",
    "informal_settlement": "Informal settlement",
}


_SAMPLE_STATS = {
    "total_users": 248,
    "active_now": 6,
    "active_24h": 57,
    "panic_presses_7d": 31,
    "by_province": [
        {"label": "Gauteng", "count": 62, "suppressed": False},
        {"label": "KwaZulu-Natal", "count": 48, "suppressed": False},
        {"label": "Western Cape", "count": 36, "suppressed": False},
        {"label": "Eastern Cape", "count": 30, "suppressed": False},
        {"label": "Limpopo", "count": 22, "suppressed": False},
        {"label": "Mpumalanga", "count": 18, "suppressed": False},
        {"label": "Free State", "count": 12, "suppressed": False},
        {"label": "North West", "count": 12, "suppressed": False},
        {"label": "Northern Cape", "count": 8, "suppressed": False},
    ],
    "by_area_type": [
        {"label": "urban", "count": 118, "suppressed": False},
        {"label": "rural", "count": 74, "suppressed": False},
        {"label": "informal_settlement", "count": 56, "suppressed": False},
    ],
    "by_age_group": [
        {"label": "18_24", "count": 54, "suppressed": False},
        {"label": "25_34", "count": 78, "suppressed": False},
        {"label": "35_44", "count": 52, "suppressed": False},
        {"label": "45_54", "count": 32, "suppressed": False},
        {"label": "55_plus", "count": 16, "suppressed": False},
        {"label": "prefer_not_to_say", "count": 13, "suppressed": False},
        {"label": "under_18", "count": None, "suppressed": True},
    ],
}


_STAT_CARDS = [
    ("Total users", "total_users", None),
    ("Active now", "active_now", "last 5 min"),
    ("Active 24h", "active_24h", None),
    ("Panic presses 7d", "panic_presses_7d", None),
]


_SECTIONS = [
    ("By province", "by_province"),
    ("By area type", "by_area_type"),
    ("By age group", "by_age_group"),
]


def _stat_card(label: str, value: object, detail: str | None) -> ft.Control:
    controls = [
        ft.Text(label, color=ft.Colors.BLUE_GREY_700),
        ft.Text(str(value), size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_800),
    ]
    if detail:
        controls.append(ft.Text(detail, size=12, color=ft.Colors.BLUE_GREY_600))
    return ft.Container(
        width=170,
        padding=14,
        bgcolor=ft.Colors.PURPLE_50,
        border_radius=16,
        content=ft.Column(controls=controls, spacing=4, tight=True),
    )


def _group_section(title: str, key: str, stats: dict | None) -> ft.Control:
    items = (stats or {}).get(key) or []
    counts = []
    for item in items:
        try:
            counts.append(max(0, int(item.get("count") or 0)))
        except (TypeError, ValueError, AttributeError):
            counts.append(0)
    largest = max(counts, default=0)

    rows: list[ft.Control] = []
    if not items:
        rows.append(ft.Text("No data available.", color=ft.Colors.BLUE_GREY_600))
    else:
        for item, count in zip(items, counts):
            label = str(item.get("label", ""))
            friendly_label = _LABELS.get(label, label)
            suppressed = bool(item.get("suppressed"))
            if suppressed:
                bar_width = 12
                bar_height = 4
                bar_color = ft.Colors.GREY_400
                count_label = "<5"
            else:
                bar_width = 0 if largest == 0 else max(4, 220 * count / largest)
                bar_height = 9
                bar_color = ft.Colors.PURPLE_700
                count_label = str(count)
            rows.append(
                ft.Column(
                    controls=[
                        ft.Text(friendly_label, color=ft.Colors.BLUE_GREY_800),
                        ft.Row(
                            controls=[
                                ft.Container(
                                    width=bar_width,
                                    height=bar_height,
                                    bgcolor=bar_color,
                                    border_radius=ft.BorderRadius.all(5),
                                ),
                                ft.Text(count_label, color=ft.Colors.BLUE_GREY_700),
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=3,
                    tight=True,
                )
            )

    return panel(
        ft.Column(
            controls=[
                section_header(ft.Icons.INSIGHTS, title, "Anonymous totals"),
                *rows,
            ],
            spacing=12,
            tight=True,
        )
    )


@ft.component
def admin_view(
    stats: dict | None,
    loading: bool,
    status: str,
    on_refresh: Callable[[], Awaitable[None]],
    use_sample: bool,
    on_toggle_sample: Callable[[bool], None],
) -> ft.Control:
    displayed_stats = _SAMPLE_STATS if use_sample else stats
    stat_controls = []
    for label, key, detail in _STAT_CARDS:
        value = "—" if displayed_stats is None else displayed_stats.get(key, "—")
        stat_controls.append(_stat_card(label, value, detail))

    controls: list[ft.Control] = [
        panel(
            ft.Column(
                controls=[
                    section_header(
                        ft.Icons.INSIGHTS,
                        "Admin dashboard",
                        "Anonymous totals only. Groups under 5 are hidden. No individual data is available here.",
                    ),
                    *(
                        [
                            ft.Container(
                                content=ft.Text(
                                    "SAMPLE DATA - illustrative figures for demonstration, not real users.",
                                    color=ft.Colors.AMBER_900,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                bgcolor=ft.Colors.AMBER_100,
                                border=ft.Border.all(1, ft.Colors.AMBER_300),
                                border_radius=12,
                                padding=12,
                            )
                        ]
                        if use_sample
                        else []
                    ),
                    ft.Switch(
                        label="Show sample data (demo)",
                        value=use_sample,
                        on_change=lambda event: on_toggle_sample(bool(event.control.value)),
                    ),
                    status_chip("ANONYMOUS TOTALS"),
                    ft.Row(
                        controls=[
                            ft.Button(
                                content="Refresh",
                                icon=ft.Icons.REFRESH,
                                bgcolor=ft.Colors.PURPLE_800,
                                color=ft.Colors.WHITE,
                                disabled=loading,
                                on_click=on_refresh,
                            ),
                            *([ft.ProgressRing(color=ft.Colors.PURPLE_700)] if loading else []),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    *([ft.Text(status, color=ft.Colors.DEEP_ORANGE_800)] if status else []),
                    *(
                        [ft.Text("No data yet. Press Refresh.", color=ft.Colors.BLUE_GREY_600)]
                        if displayed_stats is None
                        else []
                    ),
                ],
                spacing=12,
                tight=True,
            )
        ),
        ft.Row(controls=stat_controls, spacing=10, run_spacing=10, wrap=True),
    ]
    if displayed_stats is not None:
        controls.extend(_group_section(title, key, displayed_stats) for title, key in _SECTIONS)

    return ft.Column(controls=controls, spacing=12, tight=True)
