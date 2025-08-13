import flet as ft
from flet.core.textfield import TextField

thinder_svg = "PHN2ZyB3aWR0aD0iMjQ3IiBoZWlnaHQ9IjI4MiIgdmlld0JveD0iMCAwIDI0NyAyODIiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGZpbGwtcnVsZT0iZXZlbm9kZCIgY2xpcC1ydWxlPSJldmVub2RkIiBkPSJNNzMuOTM2OSAxMTMuODI3QzczLjYzMzcgMTEzLjkzNiA3My4yNzI0IDExMy44MzUgNzMuMDY5NyAxMTMuNTg3QzYzLjQ3ODIgMTAwLjk2MiA2MS4wNjg5IDc5LjI1ODcgNjAuNDgxOSA3MC45MjM4QzYwLjM2MjEgNjkuMzE4MiA1OC41NDY3IDY4LjQxNTggNTcuMDkyNyA2OS4yMjEzQzI3LjQ3OTEgODUuNzU4OCAwIDEyNC44NzkgMCAxNjIuNjQ4QzAgMjI3LjUzNiA0NS4zMzMzIDI4MS45NjkgMTIzLjM3NSAyODEuOTY5QzE5Ni40OTIgMjgxLjk2OSAyNDYuNzUgMjI1Ljg2NyAyNDYuNzUgMTYyLjY1N0MyNDYuNzUgNzkuOTQ2MSAxODcuMjk2IDI0Ljk5MjIgMTM0LjM0IDAuMTUwNDY1QzEzMy4xIC0wLjQzMDQ1NSAxMzEuNDU4IDAuNzY1NTY1IDEzMS42MzkgMi4xMTUxMUMxMzguNDYgNDYuNjg3NyAxMjkuMDM4IDk1LjE2NTIgNzMuOTM2OSAxMTMuODI3WiIgZmlsbD0id2hpdGUiLz4KPC9zdmc+Cg=="

def main(page: ft.Page):
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    page.fonts = {
        "TTRounds": "https://cloud.sovagroup.one/users/279076957//TTRounds-Black.ttf"
    }
    def start_anketa_page(e):
        bg.gradient.colors[0] = "#E04782"
        bg.gradient.colors[1] = "#FF8742"
        bg.content.content = start_page_2
        bg.content.update()
        bg.update()

    def open_photo(e: ft.FilePickerResultEvent):
        # проверяем результат
        if e.files is None:
            return
        image = e.files[0].path
        pick_photo.content = ft.Image(src=image, border_radius=100, fit=ft.ImageFit.COVER, width=min(page.width, 320), height=min(page.width-60, 320))
        pick_photo.border = None
        pick_photo.update()

    def select_date(e):
        ...
    start_page_1 = ft.Column([
        ft.Container(expand=True),
        ft.Row([ft.Column([ft.Image(src_base64=thinder_svg, height=100, width=100), ft.Text("Fainder", color="white", font_family="TTRounds", size=60)], horizontal_alignment=ft.CrossAxisAlignment.CENTER)], alignment=ft.MainAxisAlignment.CENTER),
        ft.Container(expand=True),
        ft.Container(ft.Text("Заполнить анкету", font_family="TTRounds", size=15), on_click=start_anketa_page, ink=True, ink_color=ft.colors.with_opacity(0.2, "black"), height=50, width=page.width, bgcolor="white", alignment=ft.alignment.center, margin=ft.margin.only(10, 0, 10, 30), border_radius=10)
    ], alignment=ft.MainAxisAlignment.CENTER)
    file_picker = ft.FilePicker(on_result=open_photo)
    page.overlay.append(file_picker)
    pick_photo = ft.Container(ink = True, ink_color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK), on_click=lambda e: file_picker.pick_files(file_type=ft.FilePickerFileType.IMAGE, allow_multiple=False, dialog_title="Выберете фото профиля"), content=ft.Icon(ft.Icons.CAMERA_ALT_ROUNDED, color="white", size=80), width=min(page.width, 320), height=min(page.width-60, 320), bgcolor=ft.Colors.with_opacity(0.2, "black"), margin=30, border_radius=page.width, border=ft.border.all(4, ft.Colors.WHITE), alignment=ft.alignment.center)
    start_page_2 = ft.Column([
        ft.Row([ft.Column([ft.Container(ft.Image(src_base64=thinder_svg, height=50, width=50), margin=40)],
                          horizontal_alignment=ft.CrossAxisAlignment.CENTER)], alignment=ft.MainAxisAlignment.CENTER),
        pick_photo,
        ft.Container(TextField(border=ft.InputBorder.NONE, hint_text="Ваше имя", text_size=20, color="white", cursor_color="white", hint_style=ft.TextStyle(font_family="TTRounds", size=20, color="white")), bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.WHITE), border_radius=10, border=ft.border.all(1, "white"), padding=ft.padding.only(10)),
        ft.Container(TextField(border=ft.InputBorder.NONE, hint_text="Ваша Фамилия", text_size=20, color="white", cursor_color="white", hint_style=ft.TextStyle(font_family="TTRounds", size=20, color="white")), bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.WHITE), border_radius=10, border=ft.border.all(1, "white"), padding=ft.padding.only(10)),
        ft.DropdownM2(
            options=[ft.dropdownm2.Option("Женщина"),
            ft.dropdownm2.Option("Мужчина")],
            label="Ваш пол",
            label_style=ft.TextStyle(font_family="TTRounds", size=20, color="white"),
            align_label_with_hint=True,
            hint_style=ft.TextStyle(font_family="TTRounds", size=20, color="white"),
            border_radius=10,
            border=ft.InputBorder.OUTLINE,
            border_color="white",
            border_width=1,
        ),
        ft.Row([ft.Text("Дата рождения: ", font_family="TTRounds", size=15, color="white"), ft.Container(ft.Text("Выбрать дату", font_family="TTRounds", size=15, color="black"), padding=ft.padding.only(20, 10, 20, 10), border_radius=10, bgcolor=ft.Colors.WHITE, ink=True, ink_color=ft.Colors.with_opacity(0.2, "black"), on_click=select_date)], alignment=ft.MainAxisAlignment.START),
    ], alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    bg = ft.Container(padding=10, content=ft.AnimatedSwitcher(content=start_page_1, transition=ft.AnimatedSwitcherTransition.FADE, duration=100, reverse_duration=100), expand=True, expand_loose=True, gradient=ft.LinearGradient(colors=["#FF8742", "#E04782"], rotation=180), animate=ft.Animation(1000, ft.AnimationCurve.EASE_IN_OUT))
    page.add(bg)

    page.update()


ft.app(target=main, assets_dir="assets")