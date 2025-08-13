import json
import random
import time
import flet as ft
import os
import threading
from chapter import Chapter
from gemini_exp import random_person_generate, generate_person
thinder_svg = "PHN2ZyB3aWR0aD0iMjQ3IiBoZWlnaHQ9IjI4MiIgdmlld0JveD0iMCAwIDI0NyAyODIiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGZpbGwtcnVsZT0iZXZlbm9kZCIgY2xpcC1ydWxlPSJldmVub2RkIiBkPSJNNzMuOTM2OSAxMTMuODI3QzczLjYzMzcgMTEzLjkzNiA3My4yNzI0IDExMy44MzUgNzMuMDY5NyAxMTMuNTg3QzYzLjQ3ODIgMTAwLjk2MiA2MS4wNjg5IDc5LjI1ODcgNjAuNDgxOSA3MC45MjM4QzYwLjM2MjEgNjkuMzE4MiA1OC41NDY3IDY4LjQxNTggNTcuMDkyNyA2OS4yMjEzQzI3LjQ3OTEgODUuNzU4OCAwIDEyNC44NzkgMCAxNjIuNjQ4QzAgMjI3LjUzNiA0NS4zMzMzIDI4MS45NjkgMTIzLjM3NSAyODEuOTY5QzE5Ni40OTIgMjgxLjk2OSAyNDYuNzUgMjI1Ljg2NyAyNDYuNzUgMTYyLjY1N0MyNDYuNzUgNzkuOTQ2MSAxODcuMjk2IDI0Ljk5MjIgMTM0LjM0IDAuMTUwNDY1QzEzMy4xIC0wLjQzMDQ1NSAxMzEuNDU4IDAuNzY1NTY1IDEzMS42MzkgMi4xMTUxMUMxMzguNDYgNDYuNjg3NyAxMjkuMDM4IDk1LjE2NTIgNzMuOTM2OSAxMTMuODI3WiIgZmlsbD0id2hpdGUiLz4KPC9zdmc+Cg=="

        
liked = []
disliked = []
chats_charter_ids = []

def main(page: ft.Page):
    page.controls.clear()
    bages = ft.Stack([], alignment=ft.alignment.center, expand=True)
    bages_quary = bages.controls
    page.theme_mode = ft.ThemeMode.LIGHT
    screen_wh = "1080x2400".split("x")
    page.window.width = int(screen_wh[0]) /2.3
    page.window.height = int(screen_wh[1]) /2.3

    def show_notification(content, timeout=3, sound=True, on_click=None):
        print(f"liked: {liked}")
        print(f"disliked: {disliked}")
        hided = False
        def hide_notification():
            global hided
            hided = True
            notification.right = -300
            notification.update()
            time.sleep(0.3)
            page.overlay.remove(notification)
            page.overlay.remove(sound)
        def click(e):
            hide_notification()
            if on_click:
                on_click(e)

        notification = ft.Container(content, width=min(300, page.width), height=80, blur=10, bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.WHITE), border_radius=15, border=ft.border.all(1, ft.Colors.with_opacity(0.1, "black")), right=-300, on_click=click, animate_position=ft.Animation(duration=500, curve=ft.AnimationCurve.EASE_IN_OUT_BACK))
        sound = ft.Audio("notification.mp3", autoplay=True)
        page.overlay.extend([notification, sound])
        page.update()
        time.sleep(0.01)
        notification.right = 20
        notification.update()
        time.sleep(timeout)
        if not hided:
            hide_notification()



    class ChapterCard(ft.Container):
        def __init__(self, page: ft.Page, id=None, name=None, image: str=None, description=None, age=None,
                     generation=None, visible=False, disible_button_func=None):  # 1. Добавлен параметр page
            super().__init__()
            self.page = page  # Сохраняем page, если он нужен в других методах
            self.id = id
            if generation is None:
                # 2. Устанавливаем фоновое изображение для самого контейнера ChapterCard
                self.image = ft.DecorationImage(src=image, fit=ft.ImageFit.COVER)

                # 3. Контент (текст) будет поверх фона (и bgcolor)
                # Используем Stack для наложения текста на фон
                self.content = ft.Stack(
                    [
                        ft.Container(  # Контейнер для текста с отступами и позиционированием
                            ft.Column(
                                [
                                    ft.Text(f"{name}, {age}", color=ft.Colors.WHITE, font_family="TTRounds", size=40,
                                            weight=ft.FontWeight.BOLD),  # Можно добавить жирность
                                    ft.Text(description, color=ft.Colors.WHITE, font_family="TTRounds", size=20)
                                ],
                                spacing=5  # Немного увеличил spacing для читаемости
                            ),
                            # width=self.page.width, # Ширина текстового блока, можно оставить ширину контейнера
                            padding=ft.padding.all(20),  # Используем ft.padding
                            bottom=0,  # Позиционируем внизу Stack
                            left=0,  # Позиционируем слева Stack
                            right=0  # Растягиваем по ширине Stack
                        )
                    ]
                )
                # Полупрозрачный фон будет НАД фоновым изображением, но ПОД текстом
                self.bgcolor = ft.Colors.with_opacity(0.5, "black")

            else:
                # Если идет генерация, показываем индикатор прогресса
                self.content = ft.Column(  # Центрируем ProgressRing
                    [ft.ProgressRing()],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                )
                self.bgcolor = ft.Colors.with_opacity(0.8, "black")  # Можно сделать фон темнее для ProgressRing

            # Используем page.width, который мы передали
            self.width = self.page.width  # или можно задать фиксированную ширину, например 400
            # self.height = 640
            # self.bgcolor - устанавливается в if/else
            self.border_radius = ft.border_radius.all(30)  # 4. Убрана запятая, используется ft.border_radius
            self.clip_behavior = ft.ClipBehavior.ANTI_ALIAS  # Чтобы скругление обрезало и фон/контент

            # Анимации и начальные состояния
            self.offset = ft.Offset(0, 0)  # 4. Убрана запятая
            self.animate_offset = ft.Animation(300, curve=ft.AnimationCurve.EASE_IN_BACK)
            self.animate_opacity = ft.Animation(300, curve=ft.AnimationCurve.EASE_IN_OUT)
            self.animate_scale = ft.Animation(300, curve=ft.AnimationCurve.EASE_IN_OUT)
            self.rotate = 0
            self.animate_rotation = ft.Animation(300, curve=ft.AnimationCurve.EASE_IN_OUT)
            self.opacity = 1 if visible == True else 0 # Начать невидимым
            self.scale = 1 if visible == True else 0.8
            self.disible_button_func = disible_button_func # Store the function
            
        def generate_person(self):
            if self.disible_button_func:
                self.disible_button_func() # Disable buttons immediately

            def _threaded_task():
                prompt = random_person_generate()
                person_id = generate_person(prompt)
                self.id = person_id
                person = Chapter(person_id)

                # Update ChapterCard properties
                self.image = ft.DecorationImage(src=f"chapters/photos/{person_id}.jpg", fit=ft.ImageFit.COVER)
                self.content = ft.Stack(
                    [
                        ft.Container(
                            ft.Column(
                                [
                                    ft.Text(f"{person.name}, {person.age}", color=ft.Colors.WHITE, font_family="TTRounds", size=40,
                                            weight=ft.FontWeight.BOLD),
                                    ft.Text(person.message, color=ft.Colors.WHITE, font_family="TTRounds", size=20)
                                ],
                                spacing=5
                            ),
                            padding=ft.padding.all(20),
                            bottom=0,
                            left=0,
                            right=0
                        )
                    ]
                )
                self.bgcolor = ft.Colors.with_opacity(0.5, "black")
                self.update() # Update the card UI

                if self.disible_button_func:
                    self.disible_button_func(False) # Re-enable buttons

            # Create and start the background thread
            thread = threading.Thread(target=_threaded_task)
            thread.start()

    page.fonts = {
        "TTRounds": "TTRounds-Black.ttf"
    }

    


    def give_loading_card():
        loading_card = ft.Container(ft.ProgressRing(), width=page.width, height=700, alignment=ft.alignment.center,
                                    bgcolor=ft.Colors.with_opacity(0.5, "black"), border_radius=30,
                                    offset=ft.Offset(0, 0),
                                    animate_offset=ft.Animation(300, curve=ft.AnimationCurve.EASE_IN_BACK),
                                    animate_opacity=ft.Animation(300, curve=ft.AnimationCurve.EASE_IN_OUT),
                                    animate_scale=ft.Animation(300, curve=ft.AnimationCurve.EASE_IN_OUT), rotate=0,
                                    animate_rotation=ft.Animation(300, curve=ft.AnimationCurve.EASE_IN_OUT), opacity=0,
                                    scale=0.8)
        return loading_card
    def give_display_bage() -> ft.Container:
        return bages_quary[0]

    def give_last_bage() -> ft.Container:
        # если нет второго элемента или он None — создаём и ставим
        if len(bages_quary) <= 1 or bages_quary[1] is None:
            new_card = give_loading_card()
            if len(bages_quary) <= 1:
                bages_quary.append(new_card)
            else:
                bages_quary[1] = new_card
            # сразу добавляем следующий, чтобы не было пустоты
            bages_quary.append(give_loading_card())
            return new_card

        # второй элемент уже есть и норм — возвращаем его
        result = bages_quary[1]
        # если после него нет следующего — добавляем
        if len(bages_quary) <= 2:
            chapter = ChapterCard(page=page, generation=True, disible_button_func=disable_buttons)
            bages_quary.append(chapter)
            show_notification(content=ft.Row([ft.ProgressRing(), ft.Text("Генерация профиля...", color=ft.Colors.BLACK, font_family="TTRounds", size=15)], alignment=ft.MainAxisAlignment.CENTER), on_click=None, timeout=10)
            chapter.generate_person()
        return result

    def finalize_swipe_transition():
        """
        Handles the final steps of switching cards after animation:
        - Makes the next card visible.
        - Removes the old card.
        - Updates UI and re-enables buttons.
        """
        # Ensure the next card is prepared (it's at bages.controls[1] before old card removal)
        # give_last_bage() also triggers generation for new cards in the queue.
        next_card_to_display = give_last_bage() # This is effectively bages.controls[1] at this moment

        next_card_to_display.scale = 1
        next_card_to_display.opacity = 1
        next_card_to_display.offset = ft.Offset(0,0) # Ensure it's centered
        next_card_to_display.rotate = 0
        # No direct update on next_card_to_display, bages.update() will handle it.

        # Remove the old card (which was at bages.controls[0])
        if bages.controls: # Check if not empty before trying to pop
            bages.controls.pop(0)
        
        bages.update() # Update the stack view
        disable_buttons(False) # Re-enable swipe buttons
        page.update() # General page update for safety, e.g., button states


    def swipe_right(e):
        disable_buttons()
        page_bage = give_display_bage() # This is bages.controls[0]
        print(f"page_bage.id: {page_bage.id}")
        if page_bage.id != None:
            print(f"disliked.append(page_bage.id): {page_bage.id}")
            disliked.append(page_bage.id)
        page_bage.offset = ft.Offset(1.2, 0.5)
        page_bage.rotate -= 0.5
        page_bage.opacity = 0 # Add fade-out animation
        page_bage.update() # Apply animation changes to the outgoing card

        # Run the sleep in a separate thread, then call finalize_swipe_transition on UI thread
        def sleep_then_finalize():
            time.sleep(0.3) # Animation duration
            finalize_swipe_transition() # Call directly

        page.run_thread(sleep_then_finalize)

    def swipe_left(e):
        disable_buttons()
        page_bage = give_display_bage() # This is bages.controls[0]
        print(f"page_bage.id: {page_bage.id}")
        if page_bage.id != None:
            print(f"liked.append(page_bage.id): {page_bage.id}")
            liked.append(page_bage.id)
        page_bage.offset = ft.Offset(-1.2, 0)
        page_bage.rotate += 0.5
        page_bage.opacity = 0 # Add fade-out animation
        page_bage.update() # Apply animation changes to the outgoing card

        # Run the sleep in a separate thread, then call finalize_swipe_transition on UI thread
        def sleep_then_finalize():
            time.sleep(0.3) # Animation duration
            finalize_swipe_transition() # Call directly
            
        page.run_thread(sleep_then_finalize)

    def disable_buttons(disable = True):
        if disable:
            like_button.on_click = None
            dislike_button.on_click = None
        else:
            like_button.on_click = swipe_left
            dislike_button.on_click = swipe_right

        dislike_button.update()
        like_button.update()

    def get_chapters():
        chapters = []
        for file in os.listdir("assets/chapters"):
            if file.endswith(".json"):
                id = file.split(".")[0]
                if not id in liked and not id in disliked:
                    chapters.append(Chapter(id))
        return chapters
    
    def open_chat(e):
        chapter = e.control.data
        print(f"Открыть чат с {chapter.name}, {chapter.id}")
        # chat_main(page, chapter.id)
    def generate_char_chat(id):
        chapter = Chapter(id)
        return ft.Container(ft.Row([ft.Container(ft.Image(src=f"chapters/photos/{id}.jpg", border_radius=50, height=60, width=60, fit=ft.ImageFit.COVER), padding=5), 
                                                ft.Row([ft.Column([ft.Text(chapter.name, color=ft.Colors.BLACK, font_family="TTRounds", size=18), ft.Text(f"Лайкнул(а) вас", color=ft.Colors.GREY, size=18)], alignment=ft.MainAxisAlignment.START, spacing=2)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                                                 ], vertical_alignment=ft.CrossAxisAlignment.CENTER), expand=True, border_radius=15, expand_loose=True, height=70, data=chapter, on_click=open_chat, bgcolor=ft.Colors.WHITE, ink=True)
    
    chats_list = ft.Column([], expand=True, alignment=ft.MainAxisAlignment.START, spacing=2, scroll=ft.ScrollMode.AUTO)
    def go_to_chats():
        if page.bottom_appbar.data == "chats":
            return
        page.bottom_appbar.content.controls[0].icon = ft.Icons.AOD_OUTLINED
        page.bottom_appbar.content.controls[1].icon = ft.Icons.CHAT_BUBBLE_ROUNDED
        page.controls.clear()
        existed_ids = [pers.data.id for pers in chats_list.controls if pers.data != None]
        print(f"existed_ids: {existed_ids}")
        print(f"liked: {liked}")
        if len(liked) == 0:
            chats_list.controls.clear()
            chats_list.controls.append(ft.Row([ft.Text("У вас нет ни одного чата =(", color=ft.Colors.GREY, font_family="TTRounds", size=20)], alignment=ft.MainAxisAlignment.CENTER))
            chats_list.alignment = ft.MainAxisAlignment.CENTER
        else:
            
            chats_list.alignment=ft.MainAxisAlignment.START
            for id in liked: # replace liked to chats_charter_ids
                if id not in existed_ids:
                    chats_list.controls.append(generate_char_chat(id))
                
        page.bottom_appbar.data = "chats"
        page.add(ft.Column([ft.Row([ft.Text("Чаты", color=ft.Colors.BLACK, font_family="TTRounds", size=20, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER), ft.Divider(), chats_list],spacing=2, expand=True))
        chats_list.controls.clear()

    
    
    like_button = ft.Container(ft.Icon(ft.Icons.THUMB_UP_ROUNDED, color=ft.Colors.BLACK), border_radius=30, expand=True, height=40, alignment=ft.alignment.center, bgcolor=ft.Colors.GREEN_300, ink=True, ink_color=ft.Colors.with_opacity(0.3, "black"), on_click=swipe_left)
    dislike_button = ft.Container(ft.Icon(ft.Icons.THUMB_DOWN_ROUNDED, color=ft.Colors.BLACK), expand=True, height=40, border_radius=30, alignment=ft.alignment.center, bgcolor=ft.Colors.RED_300, ink=True, ink_color=ft.Colors.with_opacity(0.3, "black"), on_click=swipe_right)
        
    def go_to_bages():
        if page.bottom_appbar.data == "bages":
            return
        page.bottom_appbar.content.controls[0].icon = ft.Icons.AOD_ROUNDED
        page.bottom_appbar.content.controls[1].icon = ft.Icons.CHAT_BUBBLE_OUTLINE_ROUNDED
        page.controls.clear()
        page.bottom_appbar.data = "bages"
        page.add(ft.Container(ft.Row([]), height=50, bgcolor=ft.Colors.GREY_400, border_radius=50))
        page.add(ft.Divider())
        if len(bages_quary) == 0:
            bages_quary.append(ChapterCard(page=page, id=None, name="Fainder", image="select_button.png", description="Давай скорее!", age="<3", visible=True))
            bages_quary.extend([ChapterCard(page=page, id=girl.id, name=girl.name, image=f"chapters/photos/{girl.id}.{random.choice(['jpg', 'png'])}", description=girl.message, age=girl.age) for girl in get_chapters()])
        
        
        # page.add(bages)
        # page.add(ft.Row([like_button, dislike_button], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
        page.add(ft.Row([ft.Container(content=ft.Column([
            bages,
            ft.Row([like_button, dislike_button], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], expand=True), expand=True, expand_loose=True,  width=min(page.width, 470))], alignment=ft.MainAxisAlignment.CENTER, expand=True))

    # БЛЯЯЯТЬ тут начинается самая ВКУУУУСНАЯ часть
    page.appbar = ft.AppBar(
        title=ft.Row([ft.Image(src_base64=thinder_svg, height=30, width=30, color=ft.Colors.BLACK), ft.Text("Fainder", color=ft.Colors.BLACK, font_family="TTRounds", size=25)]),
        automatically_imply_leading=False,
        actions=[
            ft.IconButton(icon=ft.Icons.NOTIFICATIONS, icon_color=ft.Colors.BLACK),
            ft.Container(height=50, width=50, border_radius=30, margin=ft.margin.only(10, 0, 10, 0), bgcolor=ft.Colors.WHITE, image=ft.DecorationImage(src="277cdf85735ffa76c842740760657f27_1737382028419_0.webp.jpg", fit=ft.ImageFit.COVER)),
        ]
    )
    page.bottom_appbar = ft.BottomAppBar(
        content=ft.Row(
            controls=[
                ft.IconButton(icon=ft.Icons.AOD_ROUNDED, icon_color=ft.Colors.BLACK, on_click=lambda e: go_to_bages()),
                ft.IconButton(icon=ft.Icons.CHAT_BUBBLE_OUTLINE_ROUNDED, icon_color=ft.Colors.BLACK, on_click=lambda e: go_to_chats()),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND
        ),
    )
    go_to_chats()
    
    # show_notification(content=ft.Row([ft.Text("Всего 4 профиля", color=ft.Colors.BLACK, font_family="TTRounds", size=15)], alignment=ft.MainAxisAlignment.CENTER), on_click=None)
ft.app(main, assets_dir="assets")
