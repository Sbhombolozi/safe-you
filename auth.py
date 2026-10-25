"""Email/password sign-up and login screen."""

from collections.abc import Callable

import flet as ft

from components.surfaces import panel
from services.supabase_auth import AuthError, AuthSession, sign_in, sign_up


@ft.component
def auth_view(on_authenticated: Callable[[AuthSession], None]) -> ft.Control:
    email, set_email = ft.use_state("")
    password, set_password = ft.use_state("")
    status, set_status = ft.use_state("")
    busy, set_busy = ft.use_state(False)

    async def login() -> None:
        set_busy(True)
        set_status("")
        try:
            session = await sign_in(email, password)
            on_authenticated(session)
        except AuthError as error:
            set_status(f"Error: {error}")
        except Exception:
            set_status("Error: Login could not be completed. Please try again.")
        finally:
            set_busy(False)

    async def signup() -> None:
        set_busy(True)
        set_status("")
        try:
            session = await sign_up(email, password)
            if session:
                on_authenticated(session)
            else:
                set_status("Account created. Check your email to confirm, then log in.")
        except AuthError as error:
            set_status(f"Error: {error}")
        except Exception:
            set_status("Error: Sign up could not be completed. Please try again.")
        finally:
            set_busy(False)

    status_slot = ft.Container(
        content=(
            ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.INFO_OUTLINE,
                        color=ft.Colors.DEEP_ORANGE_800
                        if status.startswith("Error:")
                        else ft.Colors.PURPLE_800,
                    ),
                    ft.Text(status, color=ft.Colors.BLUE_GREY_800, expand=True),
                ],
                spacing=10,
            )
            if status
            else None
        ),
        padding=12 if status else 0,
        bgcolor=(
            ft.Colors.AMBER_50
            if status.startswith("Error:")
            else ft.Colors.PURPLE_50
        ),
        border_radius=14,
    )

    return ft.Column(
        controls=[
            panel(
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Icon(
                                        ft.Icons.PRIVACY_TIP,
                                        color=ft.Colors.PURPLE_800,
                                        size=28,
                                    ),
                                    width=56,
                                    height=56,
                                    alignment=ft.Alignment.CENTER,
                                    bgcolor=ft.Colors.PURPLE_50,
                                    border_radius=18,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            "Safe YOU",
                                            size=26,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        ft.Text(
                                            "Your voice. Your evidence. Your safety.",
                                            color=ft.Colors.BLUE_GREY_600,
                                        ),
                                    ],
                                    spacing=3,
                                    tight=True,
                                ),
                            ],
                            spacing=14,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Divider(color=ft.Colors.BLUE_GREY_100),
                        ft.Text("Welcome", size=22, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "Sign in to continue, or create an account to get started.",
                            color=ft.Colors.BLUE_GREY_700,
                        ),
                        ft.TextField(
                            label="Email address",
                            value=email,
                            keyboard_type=ft.KeyboardType.EMAIL,
                            autocorrect=False,
                            enable_suggestions=False,
                            prefix_icon=ft.Icons.EMAIL_OUTLINED,
                            filled=True,
                            fill_color=ft.Colors.BLUE_GREY_50,
                            border_radius=14,
                            border_color=ft.Colors.BLUE_GREY_100,
                            content_padding=15,
                            on_change=lambda event: set_email(event.control.value or ""),
                        ),
                        ft.TextField(
                            label="Password",
                            value=password,
                            password=True,
                            can_reveal_password=True,
                            prefix_icon=ft.Icons.LOCK_OUTLINE,
                            filled=True,
                            fill_color=ft.Colors.BLUE_GREY_50,
                            border_radius=14,
                            border_color=ft.Colors.BLUE_GREY_100,
                            content_padding=15,
                            on_change=lambda event: set_password(event.control.value or ""),
                        ),
                        ft.Row(
                            controls=[
                                ft.Button(
                                    content="Log in",
                                    bgcolor=ft.Colors.PURPLE_800,
                                    color=ft.Colors.WHITE,
                                    disabled=busy,
                                    on_click=login,
                                ),
                                ft.OutlinedButton(
                                    content="Sign Up",
                                    disabled=busy,
                                    on_click=signup,
                                ),
                            ],
                            spacing=12,
                            wrap=True,
                        ),
                        status_slot,
                    ],
                    spacing=14,
                    tight=True,
                ),
                padding=24,
            ),
            ft.Column(
                controls=[
                    ft.Text(
                        "Your privacy",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_GREY_700,
                    ),
                    ft.Text(
                        "Safe YOU collects only what you choose to save: your account email, your journal entries and media, your trusted contacts, and your location at the moment you press the panic button. This information is stored in your private account and is not shared or sold. We only use it to provide the service to you. You can remove your trusted contacts at any time. If you choose to share your age group, type of area and province, they are used only in anonymous totals, and groups smaller than five people are never shown.",
                        size=12,
                        color=ft.Colors.BLUE_GREY_600,
                    ),
                ],
                spacing=4,
                tight=True,
            ),
            ft.Text(
                "A quiet, simple space for support and organization.",
                color=ft.Colors.BLUE_GREY_600,
                text_align=ft.TextAlign.CENTER,
            ),
        ],
        spacing=14,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
