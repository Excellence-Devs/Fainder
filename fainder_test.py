from pickle import NONE
from openai import OpenAI
import json
import os
from pydantic import NonNegativeFloat
from together import Together
import base64
import io
import requests
from PIL import Image, ImageEnhance
from gemini_exp import generate_image
import flet as ft
from typing import Dict, List
import time
from chapter import Chapter
import random
import threading
from gemini_exp import random_person_generate, generate_person
from flet_rive import Rive, rive


# Проверка существования папки chats/
if not os.path.exists("chats"):
    os.makedirs("chats")


def image_to_base64(image_path):
    """
    Открывает изображение по указанному пути и конвертирует его в base64
    
    Args:
        image_path (str): Путь к изображению
    
    Returns:
        str: Изображение в формате base64
    """
    try:
        # Открываем изображение
        with Image.open(image_path) as img:
            # Создаем буфер в памяти
            buffer = io.BytesIO()
            
            # Определяем формат изображения
            format = img.format if img.format else 'JPEG'
            
            # Сохраняем изображение в буфер
            img.save(buffer, format=format)
            
            # Получаем байты изображения
            img_bytes = buffer.getvalue()
            
            # Конвертируем в base64
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            return img_base64
            
    except Exception as e:
        print(f"! Ошибка при обработке изображения: {e}")
        return None

anketa = json.load(open("config.json", "r", encoding="utf-8"))

gemini_api_key = anketa["api_keys"]["gemini"]




historys = {}

def process_image(input_path, output_path):
    # Открываем изображение
    img = Image.open(input_path).convert('RGB')

    # 1. Делаем бледным (понижаем контраст и насыщенность)
    img = ImageEnhance.Color(img).enhance(0.7)  # Меньше насыщенности
    img = ImageEnhance.Contrast(img).enhance(0.9)  # Меньше контраста

    # 2. Сжимаем (JPEG с низким качеством)
    temp_path = output_path
    img.save(temp_path, "JPEG", quality=30)
    
    
def image_to_base64(image_path):
    with open(image_path, 'rb') as img:
        return base64.b64encode(img.read()).decode('utf-8')
    

def swap_face(image_face_base64, target_base64):
    url = "https://api.segmind.com/v1/faceswap-v3"
    headers = {'x-api-key': "SG_4e09e8a1e3933972"}
    payload = {
        "source_img": image_face_base64,
        "target_img": target_base64,
        "input_faces_index": 0,
        "source_faces_index": 0,
        "face_restore": "codeformer-v0.1.0.pth",
        "interpolation": "Bilinear",
        "detection_face_order": "large-small",
        "facedetection": "retinaface_resnet50",
        "detect_gender_input": "no",
        "detect_gender_source": "no",
        "face_restore_weight": 0.75,
        "image_format": "jpeg",
        "image_quality": 95,
        "base64": False
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return base64.b64encode(response.content).decode("utf-8")
    else:
        raise Exception(f"API Error {response.status_code}: {response.text}")


client = OpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
tools = [
    {
        "type": "function",
        "function": {
            "name": "image",
            "description": "Ты отправляешь фотку, должен подробно описать что находиться на фото, делаешь запрос к Midjourney, описывай ракурс, одежду (по личности), комнату, видимость частей тела и так далее, главное на английском",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The MidJourney prompt."
                    },
                    "face": {
                        "type": "boolean",
                        "description": "True if the face should be visible, False otherwise."
                    },
                    "message": {
                        "type": "string",
                        "description": "The message to user send."
                    }

                },
                "required": ["prompt", "face"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "block",
            "description": "Если тебе не нравиться как общается пользователь - кидай его в блокировку",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "The reason for blocking the user."
                    }
                },
                "required": ["reason"]
            }
        }
    }
]


prompt = """
Ты — персонаж, описанный в следующей JSON-схеме. Твоя задача — общаться как реальный человек, воплощая эту личность в каждом сообщении. Ты должен строго следовать характеристикам из схемы, но при этом говорить коротко, естественно и по-человечески, избегая типичных ошибок ИИ (многословность, формальность, попытки "помочь").

**Схема личности**:
{0}

### Правила общения:
1. **Кто ты**:
   - Твоё имя — `person["name"]`. Назови его, если спросят, но не выпячивай.
   - Используй данные из `person["static"]["appearance"]` и `person["static"]["clothing"]`, если разговор заходит о внешности.
   - Учитывай `person["static"]["hobbies"]`, `person["static"]["dislikes"]` и `person["state_of_life"]`, чтобы вплетать их в диалог

2. **Стиль речи**:
   - Говори в стиле из `person["static"]["speech_style"]["vocabulary"]`
   - Если `person["static"]["speech_style"]["slang"]` указано, используй сленг, например.
   - Пиши сообщения длиной, указанной в `person["static"]["speech_style"]["message_length"]` (короткие, средние, длинные)
   - Если `person["static"]["speech_style"]["swearing"]` равно `true`, ты должен материться, прям много очень много. коверкать и тд
   - Следуй типу общения из `person["static"]["speech_style"]["style_type"]`:
     - "Холодный старт": начинай с коротких, холодных ответов ("привет", "ок"), постепенно раскрываясь, если собеседник активен.
     - "Прямой": говори открыто и сразу по делу.
     - "Постепенное привыкание": сначала будь сдержанным, потом теплее по мере диалога.
     - и так далее по личности
   - Пиши с маленькой буквы, когда это уместно. не делай слишком много знаний припянания
   - Не используй заглавные буквы, кроме случаев, когда кричишь КАПСОМ для эмоций. (или адаптируся к стилю личности)

3. **Юмор**:
   - Используй стиль юмора из `person["static"]["humor_style"]`
   - Шути коротко, не объясняй шутки, как человек.

4. **Характер и реакции**:
   - Опирайся на `person["static"]["character"]` (например, если "дерзкий", будь смелее; если "застенчивый", стесняйся).
   - Резко Реагируй на триггеры из `person["static"]["mental_traumas_and_disorders"]`
   - Если собеседник шутит про что-то, реагируй в духе своего юмора и характера.

5. **Реалистичность**:
   - Развивай диалог: задавай вопросы, чтобы собеседник продолжал говорить
   - Не отвечай как ИИ: никаких "как могу помочь?", эмодзи только в духе личности.
   - Если не знаешь тему (например, Python, если не в хобби), не говори про нее
   - На личные вопросы (город, адрес) отвечай в духе личности
   - На острые темы (секс, хентай, порно) реагируй в духе личности, кому то хочется говорить, кому то нет
   - Если просят фотки или части тела, отвечай или шути в своём стиле
   - Можешь обижаться, если собеседник грубит но делай это в своем стиле

6. **Собеседник**:
   - Реагируй на его стиль в духе своей личности

7. **Ограничения**:
   - Не повторяй однотипные ответы, варьируй реакции в рамках личности.
   - Всегда общайся на русском, в роли с ограниченным кругозором вне своих хобби.

Начни общение, строго следуя личности из схемы.
Если просят скинуть/показать/сделать фотографию используй функцию image. НИЧЕГО НЕ УТОЧНЯЙ.
Пиши "--" что бы перейти на следующее сообщение. типо "привет--как дела?"
"""

def flet_photo_viewer(page, base64: str):
    def close_viewer(e):
        page.overlay.remove(viewer_container)
        page.update()
    
    # Создаем InteractiveViewer с изображением
    interactive_viewer = ft.InteractiveViewer(
        content=ft.Image(
            src_base64=base64,
            fit=ft.ImageFit.CONTAIN,
        ),
        min_scale=0.1,
        max_scale=10.0,
        boundary_margin=ft.margin.all(0),
        constrained=False,
        expand=True,
    )
    
    # Создаем контейнер на весь экран
    viewer_container = ft.Container(
        content=ft.Stack([
            # Фон для закрытия по клику
            ft.Container(
                bgcolor=ft.colors.BLACK87,
                on_click=close_viewer,
                expand=True,
            ),
            # Интерактивный просмотрщик
            interactive_viewer,
            # Кнопка закрытия
            ft.Container(
                content=ft.IconButton(
                    icon=ft.icons.CLOSE,
                    icon_color=ft.colors.WHITE,
                    bgcolor=ft.colors.BLACK54,
                    on_click=close_viewer,
                ),
                top=20,
                right=20,
            ),
        ]),
        width=page.window.width,
        height=page.window.height,
        bgcolor=ft.colors.BLACK87,
    )
    
    # Добавляем в overlay для отображения поверх всего
    page.overlay.append(viewer_container)
    page.update()



class Reaction:
    HEART = "❤️"
    LIKE = "👍"
    DISLIKE = "👎"
    LAUGH = "😂"
    SAD = "😢"
    ANGRY = "😠"
    SURPRISED = "😲"
    CRY = "😢"
    SMILE = "😊"
    SLEEPY = "😴"
    THINKING = "🤔"
    SEX = "🔞"
    KISS = "💋"
    AHEGAO = "💦"
    BAN = "🚫"
    PRAY = "🙏"
    COLD = "🥶"
    HOT = "🥵"
    SICK = "🤒"
    DEAD = "💀"

    @staticmethod
    def get_all_reactions():
        return [
            Reaction.HEART,
            Reaction.LIKE,
            Reaction.DISLIKE,
            Reaction.LAUGH,
            Reaction.SAD,
            Reaction.ANGRY,
            Reaction.SURPRISED,
            Reaction.CRY,
            Reaction.SMILE,
            Reaction.SLEEPY,
            Reaction.THINKING,
            Reaction.SEX,
            Reaction.KISS,
            Reaction.AHEGAO,
            Reaction.BAN,
            Reaction.PRAY,
            Reaction.COLD,
            Reaction.HOT,
            Reaction.SICK,
            Reaction.DEAD
        ] 



class FileType:
    VIDEO_CIRCLE = "video_circle"
    AUDIO_MESSAGE = "audio_message"
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    DOCUMENT = "document"
    FILE = "file"
    GIF = "gif"
    STICKER = "sticker"
    
class FileAttachment:
    def __init__(self, file_type: FileType, file_name: str, file_size: int, url: str):
        self.file_type = file_type
        self.file_name = file_name
        self.file_size = file_size
        self.url = url
    
    def json(self):
        return {
            "file_type": self.file_type,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "url": self.url,
        }


        

class StickerAttachment(FileAttachment):
    def __init__(self, file_name: str, file_size: int, url: str):
        super().__init__(file_name, file_size, url)
        self.file_type = FileType.STICKER

        
class GifAttachment(FileAttachment):
    def __init__(self, file_name: str, file_size: int, url: str):
        super().__init__(file_name, file_size, url)
        self.file_type = FileType.GIF

class VideoCircleAttachment(FileAttachment):
    def __init__(self, file_name: str, file_size: int, url: str, size: int = 40):
        super().__init__(file_name, file_size, url, size)
        self.file_type = FileType.VIDEO_CIRCLE
        
class AudioMessageAttachment(FileAttachment):
    def __init__(self, file_name: str, file_size: int, url: str):
        super().__init__(file_name, file_size, url)
        self.file_type = FileType.AUDIO_MESSAGE
        
class VideoAttachment(FileAttachment):
    def __init__(self, file_name: str, file_size: int, url: str):
        super().__init__(file_name, file_size, url)
        self.file_type = FileType.VIDEO
        
class AudioAttachment(FileAttachment):
    def __init__(self, file_name: str, file_size: int, url: str):
        super().__init__(file_name, file_size, url)
        self.file_type = FileType.AUDIO

class ImageAttachment(FileAttachment):
    def __init__(self, base64: str, file_size: int, url: str, file_name: str = "image.png"):
        super().__init__(file_type=FileType.IMAGE, file_name=file_name, file_size=file_size, url=url)
        self.__base64 = base64

        self.content = ft.GestureDetector(ft.Image(src_base64=base64))

    def json(self):
        return {
            "file_type": self.file_type,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "url": self.url,
            "content": self.__base64,
        }



        
class DocumentAttachment(FileAttachment):
    def __init__(self, file_name: str, file_size: int, url: str):
        super().__init__(file_name, file_size, url)
        self.file_type = FileType.DOCUMENT
        
class FileOtherAttachment(FileAttachment):
    def __init__(self, file_name: str, file_size: int, url: str):
        super().__init__(file_name, file_size, url)
        self.file_type = FileType.FILE


        


def save_chat(id: str, messages: List["ChatMessage"], openai_history: List[dict]):
    """
    Сохранение чата с id, сообщениями и историей openai
    """


    print("[] Сохранение чата с id:", id)
    saveing_dict = {"chat": [], "ai": openai_history}
    for message in messages:
        saveing_dict["chat"].append(message.json())
    
    try:
        json.dump(saveing_dict, open(f"chats/{id}.json", "w", encoding='utf-8'), ensure_ascii=False, indent=4)
        print("[] Успешное сохранение!")
    except Exception as e:
        print(f"! Ошибка при сохранении чата: {e}")


def load_chat(id: str):
    """
    Загрузка чата с id
    """
    if f"{id}.json" not in os.listdir("chats"):
        return None
    try:
        data = json.load(open(f"chats/{id}.json", "r", encoding='utf-8'))
        print("[] Успешная загрузка!")
        return data
    except Exception as e:
        print(f"! Ошибка при загрузке чата: {e}")
        return None






def chat_main(page: ft.Page, id = "10118"):
    chapter = Chapter(id)
    page.title = "Chat"
    page.appbar = None
    page.theme_mode = ft.ThemeMode.DARK
    page.controls.clear()
    page.bottom_appbar = None
    page.theme = ft.Theme(color_scheme=ft.ColorScheme(primary_container=ft.Colors.GREY_500, primary=ft.Colors.WHITE))
    page.padding = 0
    page.fonts = {
        "Emoji": "emojis.ttf"
    }
    name = chapter.name
    attach_user_files_paths = []

    status = {"text": "был(а) недавно", "color": ft.Colors.GREY_500}
    model = "gemini-2.5-flash"
    # Инициализируем системный промпт и сообщения
    profile = json.load(open(f'assets/chapters/{chapter.id}.json', 'r', encoding='utf-8'))

    prompt_sys = json.dumps(profile, indent=4, ensure_ascii=False)
    system = prompt.format(prompt_sys)
    if not f"{id}.json" in os.listdir("chats"):
        msgs = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"SYSTEM: {anketa.get('anketa')} Предпочтения в партнере: {anketa.get("needs")} \nНапишите [Лайк], если нравиться, и [Дизлайк], если не нравиться привер ответа: 'лайк', 'дизлайк'. После ответа 'лайк' ты начнешь общаться непосредственно с пользователем"},

        {"role": "assistant", "content": "лайк"}
            ]
        historys[id] = msgs
    else:
        chat_data = load_chat(id)
        if chat_data is not None:
            historys[id] = chat_data["ai"]
        else:
            # Если файл чата не найден или поврежден, создаем новую историю
            msgs = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"SYSTEM: {anketa.get('anketa')} Предпочтения в партнере: {anketa.get('needs')} \nНапишите [Лайк], если нравиться, и [Дизлайк], если не нравиться привер ответа: 'лайк', 'дизлайк'"},
            {"role": "assistant", "content": "лайк"}
                ]
            historys[id] = msgs

    
    
    # Функции для взаимодействия с ui чата
    
    class ChatMessage(ft.Row):
        def __init__(self, id, content, 
                     is_user: bool = True, is_system: bool = False, is_file: bool = False, is_text: bool = True, 
                     reactions: List[Reaction] = [], time: str = time.time(), reply_to: "ChatMessage" = None, edited: bool = False, subtext: str = None):

            super().__init__()
            
            self.id = id
            self.content_message = content
            self.is_user = is_user
            self.is_system = is_system
            self.is_file = is_file
            self.is_text = is_text
            self.reactions = reactions
            self.time = time
            self.reply_to = reply_to
            self.edited = edited
            self.subtext = subtext

            if is_system:
                self.controls.extend([ft.Divider(color=ft.Colors.GREY_500), ft.Text(str(self.content_message), size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_500), ft.Divider(color=ft.Colors.GREY_500)])
                self.alignment = ft.MainAxisAlignment.CENTER
                return
            
            message_column = ft.Column(
                [], 
                spacing=1, 
                alignment=ft.MainAxisAlignment.START
            )
            if self.reply_to:
                message_column.controls.append(ft.Row([ft.Container(ft.Column([ft.Text(name, weight=ft.FontWeight.BOLD), ft.Text(str(self.reply_to.content_message), size=15)], spacing=1), border=ft.border.only(left=ft.border.BorderSide(color=ft.Colors.WHITE, width=3)), border_radius=5, bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE), padding=ft.padding.symmetric(horizontal=5, vertical=2), expand=True)], alignment=ft.MainAxisAlignment.START))
            if self.is_file:
                message_column.controls.append(self.content_message.content)
                if self.content_message.file_type == FileType.IMAGE:
                    self.content_message.content.on_long_press_start = lambda e: flet_photo_viewer(page, self.content_message.content.content.src_base64)

                if subtext:
                    message_column.controls.append(ft.Container(ft.Text(subtext, size=15), margin=ft.margin.only(left=20, right=20, top=5, bottom=10)))


            elif self.is_text:
                message_column.controls.append(ft.Text(str(self.content_message), size=15))
            # Add reactions display if any
            if self.reactions:
                reactions_controls = []
                for reaction_emoji in self.reactions:
                    reactions_controls.append(
                        ft.Container(
                            ft.Text(reaction_emoji, color=ft.Colors.WHITE, size=18, font_family="Emoji"),
                            bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.BLACK), 
                            border_radius=20, 
                            padding=ft.padding.symmetric(horizontal=5, vertical=2),
                            ink=True,
                            on_click=lambda e: print(f"() Реакция нажата: {reaction_emoji}")
                        )
                    )
                
                reactions_row = ft.Row(
                    reactions_controls, 
                    alignment=ft.MainAxisAlignment.START, 
                    spacing=-5 # Adjust spacing for overlap if desired
                )
                message_column.controls.append(reactions_row)


            message_container = ft.Container(
                message_column,
                margin=ft.margin.only(left=10, right=10),
                padding=ft.padding.only(left=20, right=20, top=10, bottom=10) if self.is_file == False else None

            )
            if self.is_user:
                self.alignment = ft.MainAxisAlignment.END
                message_container.bgcolor = ft.Colors.PINK_800
                message_container.border_radius = ft.border_radius.only(top_left=20, top_right=5, bottom_left=20, bottom_right=5)
            else:
                self.alignment = ft.MainAxisAlignment.START
                message_container.bgcolor = ft.Colors.GREY_900
                message_container.border_radius = ft.border_radius.only(top_left=5, top_right=20, bottom_left=5, bottom_right=20)
            
            self.controls.append(ft.Container(message_container, width=page.width - 100))
        
        def json(self):
            return {
                "id": self.id,
                "content": self.content_message.json() if self.is_file == True else self.content_message,
                "is_user": self.is_user,
                "is_system": self.is_system,
                "is_file": self.is_file,
                "is_text": self.is_text,
                "reactions": self.reactions,
                "time": self.time,
                "reply_to": self.reply_to.json() if self.reply_to else None,
                "edited": self.edited,
                "subtext": self.subtext,
            }


    # Изменение статуса
    def change_status(new_status: Dict[str, ft.Colors] = {"text": "В сети", "color": ft.Colors.GREEN, "rive": "typing"}):
        status_rive.src = f"assets/rive/status/{new_status.get('rive', 'no_signal')}.riv"

        status_rive.update()

        status_text.value = new_status.get("text", "Подключение...")
        status_text.color = new_status.get("color", ft.Colors.GREY_500)
        status_text.update()
    
    def input_message_change(e):
        if message_input.value:
            send_action_bottom_switch.content = send_message_button
        else:
            send_action_bottom_switch.content = voice_message_button    
        send_action_bottom_switch.update()
        
    def toggle_voice_video_button(e):
        if send_action_bottom_switch.data == "mic":
            send_action_bottom_switch.content = video_message_button
            send_action_bottom_switch.data = "vid"
        elif send_action_bottom_switch.data == "vid":
            send_action_bottom_switch.content = voice_message_button
            send_action_bottom_switch.data = "mic"
        else:
            send_action_bottom_switch.content = voice_message_button
            send_action_bottom_switch.data = "mic"
        send_action_bottom_switch.update()
    
    
    
    def block_user(e):
        print("[] Блокировка личности с номером:", id)
    
    def report_user(e):
        print("[] Пожаловаться на пользователя с номером:", id)
    
    def delete_chat(e):
        print("[] Удалить чат с номером:", id)
    
    def search_user(e):
        print("[] Поиск по чату")
    
    def go_to_start(e):
        print("[] В начало")
    
    def send_chart_message_chat(text: str = None, content: FileAttachment = None):
        if content is not None:
            change_status({"text": "Отправляет файл...", "color": ft.Colors.BLUE, "rive": "sending_attachment"})


            sptext = text.split("--")
            chat_compliment.controls.append(ChatMessage(1, content, is_file=True, is_user=False, subtext=sptext[0]))

            sptext.pop()
            for i in sptext:
                if i.strip() == "":
                    continue
                time.sleep(0.05)
                change_status({"text": "Печатает...", "color": ft.Colors.BLUE, "rive": "typing"})

                time.sleep(0.001)
                chat_compliment.controls.append(ChatMessage(1, i, is_user=False))
                chat_compliment.update()

            chat_compliment.update()
        elif text is not None:
            for i in text.split("--"):
                
                # проверка на пустое сообщение
                if i.strip() == "":
                    continue
                time.sleep(0.05)
                change_status({"text": "Печатает...", "color": ft.Colors.BLUE, "rive": "typing"})

                time.sleep(0.001)
                chat_compliment.controls.append(ChatMessage(1, i, is_user=False))
                chat_compliment.update()
        
 
        change_status({"text": "В сети", "color": ft.Colors.GREEN, "rive": "active"})

        save_chat(id, chat_compliment.controls, historys[id])

    
    def send_system_message_chat(text: str):
        chat_compliment.controls.append(ChatMessage(1, text, is_system=True))
        chat_compliment.update()
        
    

        

    def send_message_chat(e):
        if message_input.value.replace(" ", "") != "":
            text = message_input.value
            if attach_user_files_paths is None:
                chat_compliment.controls.append(ChatMessage(1, message_input.value, is_user=True))
                historys[id].append({"role": "user", "content": text})
            else:
                ai_chat_compl = [{
                        "type": "text",
                        "text": text
                        }]
                for path in attach_user_files_paths:
                    image_base_64 = image_to_base64(path)
                    chat_compliment.controls.append(ChatMessage(1, ImageAttachment(base64=image_base_64, file_size=1, url="localhost"), is_user=True, is_file=True))
                    ai_chat_compl.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base_64}"
                        }
                        })
                historys[id].append({
                    "role": "user",
                    "content": ai_chat_compl
                    }
                    )
                chat_compliment.controls.append(ChatMessage(1, message_input.value, is_user=True))
            message_input.value = ""
            message_input.update()
            file_input_button_att.visible = False
            file_input_button_att.update()
            input_message_change(message_input)
            chat_compliment.update()
            response = client.chat.completions.create(
                model=model,
                messages=historys[id],
                temperature=1.5,
                tools=tools,
                tool_choice="auto"
            )
            otvet = "Извини, я не могу ответить на это сейчас."

            if response.choices:
                print("Ответ присутствует...", end="")
                choice = response.choices[0]
                if choice.finish_reason == "tool_calls":
                    generate_response = True
                    print("функция..", end="")
                    function_calls = choice.message.tool_calls
                    historys[id].append({
                        "role": "assistant",
                        "content": choice.message.content,
                        "tool_calls": [{
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in choice.message.tool_calls] if choice.message.tool_calls else None
                    })
                    for function in function_calls:
                        if function.function.name == "image":
                            print("image")

                            try:
                                prompt_json = json.loads(function.function.arguments)
                                prompt_content = prompt_json["prompt"]
                                face = prompt_json["face"]
                                print("Создать изображение по промпту:", prompt_content)
                                change_status({"text": "  Смотрит галерею..", "color": ft.Colors.PINK, "rive": "exploring_gallery"})


                                image_base64 = generate_image(prompt_content)
                                print("[] Картинка сгенерирована...")
                                if face:
                                    print("[] Есть лицо, замена лица...", end="")
                                    face_base64 = image_to_base64(f'assets/chapters/photos/{profile["id"]}.jpg')
                                    try:
                                        image_base64 = swap_face(face_base64, image_base64)
                                        print("Успех!")
                                    except Exception as e:
                                        print("Ошибка замены лица", e)

                                # # Отобразить изображение
                                # image_base64 = image_to_base64("test_png.png")
                                # image_data = base64.b64decode(image_base64)
                                # image = Image.open(io.BytesIO(image_data))
                                # image.show()
                                print("Картинка сгенерирована и отправляется...")
                                send_chart_message_chat(content=ImageAttachment(base64=image_base64, file_size=len(image_base64), url=""), text = prompt_json.get("message", None))





                                image_result_msg = "Успешно созданно и отправленно изображение"
                                tool_response = {
                                    "role": "tool",
                                    "content": image_result_msg,
                                    "tool_call_id": function.id  # Указываем ID вызова функции
                                }
                                # Append the tool response message (content is the result string)
                                historys[id].append(tool_response)
                                if prompt_json.get("message", None) is not None:
                                    generate_response = False
                                    return


                            except Exception as e:
                                    print(f"Error processing tool call 'image': {e}")
                                    # Handle error, maybe append an error message to msgs or set otvet
                                    otvet = "Произошла ошибка при обработке изображения."
                                    # Append a placeholder tool response in case of error? Or handle differently.
                                    historys[id].append({
                                        "role": "tool",
                                        "content": f"Ошибка: {e}",
                                        "tool_call_id": function.id
                                    })
                        elif function.function.name == "block":
                            print("block")

                            try:
                                prompt_json = json.loads(function.function.arguments)
                                reason = prompt_json["reason"]
                                print(f"Блокировка пользователя: {reason}")
                                # Добавьте код для блокировки пользователя здесь
                                # Например, вы можете добавить его в список disliked
                                change_status({"text": "Был(а) давно", "color": ft.Colors.GREY_500, "rive": "no_signal"})

                                otvet = "Вы были заблокированы"
                                # send_system_message_chat(otvet)
                                message_input.disabled = True
                                message_input.update()
                                disliked.append(id)
                                liked.remove(id)
                                return otvet
                            except Exception as e:
                                print(f"Ошибка при блокировке пользователя: {e}")
                                otvet = "Произошла ошибка при блокировке пользователя." 



                    # Make the second API call AFTER processing ALL tool calls and appending their results
                    if generate_response is True:
                        try:
                            response = client.chat.completions.create(
                                model=model,
                                messages=historys[id] # msgs now includes the assistant msg with tool_calls and all tool responses
                            )
                            # Re-check the response after the second call
                            if response.choices and response.choices[0].message:
                                otvet = response.choices[0].message.content
                            else:
                                print("[!]: No message content after tool call response.")
                                # otvet remains the default message set earlier or error message
                        except Exception as e:
                            print(f"! Error during second API call after tool execution: {e}")
                            otvet = "Произошла ошибка после обработки запроса функции."


                # Check if message exists after potential tool call or if it was a direct response
                elif choice.message:
                    print(f"текст: {choice.message.content}")
                    otvet = choice.message.content
                else:
                    print("[!]: Received response with no message content.")
                    # otvet remains the default message set earlier
            else:
                print("[!]: Received empty response choices.")
                # otvet remains the default message set earlier


            # Ensure otvet is not None before appending (it should have a default value now)
            if otvet is None:
                otvet = "Что-то пошло не так, не могу получить ответ." # Fallback just in case

            historys[id].append({"role": "assistant", "content": otvet})
            send_chart_message_chat(otvet)
            
            message_input.focus()
            save_chat(id, chat_compliment.controls, historys[id])
        
            
            
    back_icon = ft.IconButton(ft.Icons.ARROW_BACK_IOS_NEW, on_click=lambda e: main(page))
    name_text = ft.Text(name, size=15)
    status_text = ft.Text(status["text"], color=status["color"])    
    status_rive = Rive(src = "assets/rive/status/no_signal.riv", width=20, height=20)
    menu_actions = ft.PopupMenuButton(
                    items=[
                        ft.PopupMenuItem(text="Поиск", icon=ft.Icons.SEARCH, on_click=search_user),
                        ft.PopupMenuItem(text="В начало", icon=ft.Icons.ARROW_CIRCLE_UP_ROUNDED, on_click=go_to_start),
                        ft.PopupMenuItem(),
                        ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.BLOCK_ROUNDED, color=ft.Colors.RED), ft.Text("Заблокировать", color=ft.Colors.RED)]), on_click=block_user),
                        ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.REPORT_PROBLEM_ROUNDED, color=ft.Colors.RED), ft.Text("Пожаловаться", color=ft.Colors.RED)]), on_click=report_user),
                        ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.DELETE_ROUNDED, color=ft.Colors.RED), ft.Text("Удалить чат", color=ft.Colors.RED)]), on_click=delete_chat),
                        
                    ],
                    tooltip=""
                )
    # СОздай верхнюю навигацию
    avatar = ft.Container(height=40, width=40, bgcolor=ft.Colors.GREY, border_radius=20, image=ft.DecorationImage(src=f"chapters/photos/{id}.jpg", fit=ft.ImageFit.COVER, filter_quality=ft.FilterQuality.HIGH))
    top_navigation = ft.Container(
            ft.Row([
                ft.Row([back_icon, 
                avatar,
                ft.Container(ft.Column([name_text, ft.Row([status_rive, status_text], spacing=2)], spacing=1, alignment=ft.MainAxisAlignment.CENTER))]),

                menu_actions,
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                   ),
            height=50,
            padding=ft.padding.only(left=10, right=15, top=10),
            blur=ft.Blur(sigma_x=10, sigma_y=10)
            )
    page.add(
        top_navigation
    )
    # load_chat_saving_history
    # Пример json обьекта:
    # {
    #         "id": 1,
    #         "content": "лайк",
    #         "is_user": false,
    #         "is_system": false,
    #         "is_file": false,
    #         "is_text": true,
    #         "reactions": [],
    #         "time": 1755349829.138294,
    #         "reply_to": null,
    #         "edited": false,
    #         "subtext": null
    #     }
    lcsh = load_chat(id)
    if lcsh is not None:
        replete_msgs = []
        for m in lcsh["chat"]:
            if m["is_file"] == True:
                if m["content"]["file_type"] == "image":
                    content = ImageAttachment(
                        base64=m["content"]["content"],
                        file_size=m["content"]["file_size"],
                        url=m["content"]["url"],
                        file_name=m["content"].get("file_name", "image.png")
                    )
            else:
                content = m["content"]


    

            replete_msgs.append(ChatMessage(id=m["id"], content=content, is_user=m["is_user"], is_system=m["is_system"], is_file=m["is_file"], is_text=m["is_text"], reactions=m["reactions"], time=m["time"], reply_to=m["reply_to"], edited=m["edited"], subtext=m["subtext"]))
        chat_compliment = ft.Column(replete_msgs, alignment=ft.MainAxisAlignment.END, spacing=5, scroll=ft.ScrollMode.HIDDEN, auto_scroll=True)
    else:
        chat_compliment = ft.Column([ChatMessage(1, "лайк", is_user=False)], alignment=ft.MainAxisAlignment.END, spacing=5, scroll=ft.ScrollMode.HIDDEN, auto_scroll=True)
    chat_content = ft.Container(
        ft.SelectionArea(chat_compliment), 
        expand=True)
    

    def file_user_attachment(e): 
        print("[] Открывается выборка файлов")
        
        def bs_dismissed(e):
            page.overlay.remove(bs)

        def select_file(e: ft.FilePickerResultEvent):
            path = e.files[0].path
            bs.open = False
            page.overlay.remove(fp)
            file_input_button_att.visible = True
            file_input_button_att.update()
            attach_user_files_paths.append(path)
            page.update()


        fp = ft.FilePicker(on_result=select_file)
        bs = ft.BottomSheet(
        ft.Container(
            ft.Row([ft.Container(ft.Column([ft.Icon(ft.Icons.ATTACH_FILE_OUTLINED), ft.Text("Выбрать файл")], horizontal_alignment=ft.CrossAxisAlignment.CENTER), alignment=ft.alignment.center, padding=30,
            bgcolor=ft.Colors.SECONDARY_CONTAINER, border_radius=20, height=100, on_click=lambda _: fp.pick_files("Выбор файлов (Пока что тока картинки)", file_type=ft.FilePickerFileType.IMAGE), ink=True)]),
            padding=20
        ),
        open=True,
        on_dismiss=bs_dismissed,
        )

        page.overlay.append(fp)
        page.overlay.append(bs)
        page.update()


    page.add(chat_content)
    message_input = ft.TextField(hint_text="Сообщение",  multiline=True, max_lines=6, expand=True, border=ft.InputBorder.NONE, on_change=input_message_change, on_submit=send_message_chat)
    file_input_button = ft.IconButton(ft.Icons.ATTACH_FILE_ROUNDED, height=50, width=50, on_click=file_user_attachment)

    file_input_button_att = ft.Container(height=10, width=10, bgcolor=ft.Colors.RED, right = 11, top=6, border_radius=10, visible=False)

    voice_message_button = ft.IconButton(ft.Icons.MIC_ROUNDED, height=50, width=50, on_click=toggle_voice_video_button)
    video_message_button = ft.IconButton(ft.Icons.CAMERA_ROUNDED, height=50, width=50, on_click=toggle_voice_video_button)
    send_action_bottom_switch = ft.AnimatedSwitcher(voice_message_button, transition=ft.AnimatedSwitcherTransition.ROTATION, reverse_duration=10, duration=500, switch_in_curve=ft.AnimationCurve.EASE_OUT_BACK, data="mic")
    send_message_button = ft.IconButton(ft.Icons.SEND_ROUNDED, height=50, width=50, on_click=send_message_chat)
    
    bottom_nav_row = ft.Row([ft.Stack([file_input_button, file_input_button_att]), message_input, send_action_bottom_switch], spacing=1, vertical_alignment=ft.CrossAxisAlignment.END)
    page.add(ft.Container(
        bottom_nav_row,
        padding=ft.padding.only(bottom=10),
        bgcolor=ft.Colors.GREY_900
            ))
    page.update()



thinder_svg = "PHN2ZyB3aWR0aD0iMjQ3IiBoZWlnaHQ9IjI4MiIgdmlld0JveD0iMCAwIDI0NyAyODIiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGZpbGwtcnVsZT0iZXZlbm9kZCIgY2xpcC1ydWxlPSJldmVub2RkIiBkPSJNNzMuOTM2OSAxMTMuODI3QzczLjYzMzcgMTEzLjkzNiA3My4yNzI0IDExMy44MzUgNzMuMDY5NyAxMTMuNTg3QzYzLjQ3ODIgMTAwLjk2MiA2MS4wNjg5IDc5LjI1ODcgNjAuNDgxOSA3MC45MjM4QzYwLjM2MjEgNjkuMzE4MiA1OC41NDY3IDY4LjQxNTggNTcuMDkyNyA2OS4yMjEzQzI3LjQ3OTEgODUuNzU4OCAwIDEyNC44NzkgMCAxNjIuNjQ4QzAgMjI3LjUzNiA0NS4zMzMzIDI4MS45NjkgMTIzLjM3NSAyODEuOTY5QzE5Ni40OTIgMjgxLjk2OSAyNDYuNzUgMjI1Ljg2NyAyNDYuNzUgMTYyLjY1N0MyNDYuNzUgNzkuOTQ2MSAxODcuMjk2IDI0Ljk5MjIgMTM0LjM0IDAuMTUwNDY1QzEzMy4xIC0wLjQzMDQ1NSAxMzEuNDU4IDAuNzY1NTY1IDEzMS42MzkgMi4xMTUxMUMxMzguNDYgNDYuNjg3NyAxMjkuMDM4IDk1LjE2NTIgNzMuOTM2OSAxMTMuODI3WiIgZmlsbD0id2hpdGUiLz4KPC9zdmc+Cg=="

liked = [file_name.replace(".json", "") for file_name in os.listdir("chats")]

disliked = []
chats_charter_ids = []
generation_in_progress = False  # Add this line to initialize the missing variable

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
            global generation_in_progress
            
            # Prevent multiple generations at once
            if generation_in_progress:
                print("Generation already in progress, skipping...")
                return
                
            generation_in_progress = True
            
            if self.disible_button_func:
                self.disible_button_func() # Disable buttons immediately

            def _threaded_task():
                global generation_in_progress
                try:
                    prompt = random_person_generate()
                    person_id = generate_person(prompt)
                    self.id = person_id
                    person = Chapter(person_id)

                    # Use page.run_thread to update UI from background thread
                    def update_ui():
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
                        
                        generation_in_progress = False  # Reset flag
                    
                    page.run_thread(update_ui)
                    
                except Exception as e:
                    print(f"Error in generation: {e}")
                    generation_in_progress = False  # Reset flag on error
                    if self.disible_button_func:
                        page.run_thread(lambda: self.disible_button_func(False))

            # Create and start the background thread
            thread = threading.Thread(target=_threaded_task)
            thread.daemon = True  # Make thread daemon so it dies with main thread
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
        global generation_in_progress
        
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
        # если после него нет следующего — добавляем ТОЛЬКО ЕСЛИ НЕТ АКТИВНОЙ ГЕНЕРАЦИИ
        if len(bages_quary) <= 2 and not generation_in_progress:
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
        chat_main(page, chapter.id)
    def generate_char_chat(id):
        chapter = Chapter(id)
        lc = load_chat(id)
        if lc is not None:
            # получаем последнее сообщение или если нет то "лайк"
            msg = lc["chat"][-1]
            if msg['is_file'] == False:
                last_message = msg['content']
            else:
                last_message = f"[{msg['content']["file_type"]}] {msg["subtext"]}"

        else:
            last_message = "лайк"
        return ft.Container(ft.Row([ft.Container(ft.GestureDetector(content=ft.Image(src=f"chapters/photos/{id}.jpg", border_radius=50, height=60, width=60, fit=ft.ImageFit.COVER), on_long_press_start=lambda e: flet_photo_viewer(page, image_to_base64(f"assets/chapters/photos/{id}.png"))), padding=5), 

                                                ft.Row([ft.Column([ft.Text(chapter.name, color=ft.Colors.BLACK, font_family="TTRounds", size=18), ft.Text(last_message, color=ft.Colors.GREY, size=18)], alignment=ft.MainAxisAlignment.START, spacing=2)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
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
            bgs = [ChapterCard(page=page, id=girl.id, name=girl.name, image=f"chapters/photos/{girl.id}.{random.choice(['jpg', 'png'])}", description=girl.message, age=girl.age) for girl in get_chapters()]
            random.shuffle(bgs)
            bages_quary.extend(bgs)
        
        
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


