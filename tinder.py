import flet as ft

thinder_svg = "PHN2ZyB3aWR0aD0iMjQ3IiBoZWlnaHQ9IjI4MiIgdmlld0JveD0iMCAwIDI0NyAyODIiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGZpbGwtcnVsZT0iZXZlbm9kZCIgY2xpcC1ydWxlPSJldmVub2RkIiBkPSJNNzMuOTM2OSAxMTMuODI3QzczLjYzMzcgMTEzLjkzNiA3My4yNzI0IDExMy44MzUgNzMuMDY5NyAxMTMuNTg3QzYzLjQ3ODIgMTAwLjk2MiA2MS4wNjg5IDc5LjI1ODcgNjAuNDgxOSA3MC45MjM4QzYwLjM2MjEgNjkuMzE4MiA1OC41NDY3IDY4LjQxNTggNTcuMDkyNyA2OS4yMjEzQzI3LjQ3OTEgODUuNzU4OCAwIDEyNC44NzkgMCAxNjIuNjQ4QzAgMjI3LjUzNiA0NS4zMzMzIDI4MS45NjkgMTIzLjM3NSAyODEuOTY5QzE5Ni40OTIgMjgxLjk2OSAyNDYuNzUgMjI1Ljg2NyAyNDYuNzUgMTYyLjY1N0MyNDYuNzUgNzkuOTQ2MSAxODcuMjk2IDI0Ljk5MjIgMTM0LjM0IDAuMTUwNDY1QzEzMy4xIC0wLjQzMDQ1NSAxMzEuNDU4IDAuNzY1NTY1IDEzMS42MzkgMi4xMTUxMUMxMzguNDYgNDYuNjg3NyAxMjkuMDM4IDk1LjE2NTIgNzMuOTM2OSAxMTMuODI3WiIgZmlsbD0id2hpdGUiLz4KPC9zdmc+Cg=="


def main(page: ft.Page):
    page.horizontal_alignment = page.vertical_alignment = "center"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.floating_action_button = ft.FloatingActionButton(icon=ft.Icons.ADD)
    page.floating_action_button_location = ft.FloatingActionButtonLocation.CENTER_DOCKED
    page.fonts = {
        "TTRounds": "https://cloud.sovagroup.one/users/279076957//TTRounds-Black.ttf"
    }

    page.appbar = ft.AppBar(
        title=ft.Row([ft.Image(src_base64=thinder_svg, height=30, width=30, color=ft.Colors.BLACK), ft.Text("Fainder", color=ft.Colors.BLACK, font_family="TTRounds", size=25)]),
        automatically_imply_leading=False,
        actions=[
            ft.IconButton(icon=ft.Icons.NOTIFICATIONS, icon_color=ft.Colors.BLACK),
            ft.Container(height=30, width=30, border_radius=30, margin=ft.margin.only(0, 0, 0, 10), bgcolor=ft.Colors.WHITE, content=ft.Image(src_base64=ass, height=30, width=30, color=ft.Colors.BLACK)),
        ]
    )
    page.bottom_appbar = ft.BottomAppBar(
        bgcolor=ft.Colors.BLUE,
        shape=ft.NotchShape.CIRCULAR,
        content=ft.Row(
            controls=[
                ft.IconButton(icon=ft.Icons.MENU, icon_color=ft.Colors.WHITE),
                ft.Container(expand=True),
                ft.IconButton(icon=ft.Icons.SEARCH, icon_color=ft.Colors.WHITE),
                ft.IconButton(icon=ft.Icons.FAVORITE, icon_color=ft.Colors.WHITE),
            ]
        ),
    )

    page.add(ft.Text("Body!"))


ft.app(main, assets_dir="assets")
