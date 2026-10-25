import logging

import flet as ft

from views.app_shell import render_shell

LOG_LEVEL = logging.INFO
logging.basicConfig(format="%(levelname)s %(name)s: %(message)s")
logging.getLogger("app").setLevel(LOG_LEVEL)


def main(page: ft.Page) -> None:
    file_picker = ft.FilePicker()
    page.title = "Safe YOU"
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.PURPLE_700)
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.Colors.PINK_50
    page.padding = 0
    page.render(render_shell, page, file_picker)


ft.run(main)
