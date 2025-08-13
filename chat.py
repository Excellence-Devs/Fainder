from openai import OpenAI
import json
import os
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


client = OpenAI(api_key="sk-fd001c141070405d89a171c2c4bba0d4", base_url="https://api.deepseek.com")
clienti = Together(api_key="34fc99d79109ef8d1342ce42dd2aa27ac50eefea4d4a966b5f5355ba455750d8")
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
                    }
                },
                "required": ["prompt", "face"]
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
Если просят скинуть/показать/сделать фотографию используй функцию image. НИЧЕГО НЕ УТОЧНЯЙ
"""







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
    def __init__(self, file_name: str, file_size: int, url: str):
        super().__init__(file_name, file_size, url)
        self.file_type = FileType.IMAGE
        
class DocumentAttachment(FileAttachment):
    def __init__(self, file_name: str, file_size: int, url: str):
        super().__init__(file_name, file_size, url)
        self.file_type = FileType.DOCUMENT
        
class FileOtherAttachment(FileAttachment):
    def __init__(self, file_name: str, file_size: int, url: str):
        super().__init__(file_name, file_size, url)
        self.file_type = FileType.FILE


        

def main(page: ft.Page, id = "10118"):
    chapter = Chapter(id)
    page.title = "Chat"
    page.appbar = None
    page.bottom_appbar = None
    page.theme = ft.Theme(color_scheme=ft.ColorScheme(primary_container=ft.Colors.GREY_500, primary=ft.Colors.WHITE))
    page.padding = 0
    page.fonts = {
        "Emoji": "emojis.ttf"
    }
    name = chapter.name
    status = {"text": "был(а) недавно", "color": ft.Colors.GREY_500}
    model = "deepseek-chat"
    # Инициализируем системный промпт и сообщения
    profile = json.load(open(f'assets/chapters/{chapter.id}.json', 'r', encoding='utf-8'))

    prompt_sys = json.dumps(profile, indent=4, ensure_ascii=False)
    system = prompt.format(prompt_sys)
    msgs = [
        {"role": "system", "content": system},
        {"role": "user", "content": "SYSTEM: Вам пришел лайк от пользователя 'Алексей 17 лет, ищу обычную красивую девушку. Хожу в качалку' \nНапишите [Лайк], если нравиться, и [Дизлайк], если не нравиться привер ответа: 'лайк', 'дизлайк'"},
        {"role": "assistant", "content": "лайк"}
            ]
    
    
    
    # Функции для взаимодействия с ui чата
    
    class ChatMessage(ft.Row):
        def __init__(self, id, content, 
                     is_user: bool = True, is_voice: bool = False, is_video: bool = False, is_file: bool = False, is_text: bool = True, 
                     reactions: List[Reaction] = [], time: str = time.time(), reply_to: "ChatMessage" = None, edited: bool = False):
            super().__init__()
            
            self.id = id
            self.content_text = content if is_text else ""
            self.content_message = content
            self.is_user = is_user
            self.is_voice = is_voice
            self.is_video = is_video
            self.is_file = is_file
            self.is_text = is_text
            self.reactions = reactions
            self.time = time
            self.reply_to = reply_to
            self.edited = edited

            message_column = ft.Column(
                [], 
                spacing=1, 
                alignment=ft.MainAxisAlignment.START
            )
            if self.reply_to:
                message_column.controls.append(ft.Row([ft.Container(ft.Column([ft.Text(name, weight=ft.FontWeight.BOLD), ft.Text(self.reply_to.content_text, size=15)], spacing=1), border=ft.border.only(left=ft.border.BorderSide(color=ft.Colors.WHITE, width=3)), border_radius=5, bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE), padding=ft.padding.symmetric(horizontal=5, vertical=2), expand=True)], alignment=ft.MainAxisAlignment.START))
    
            message_column.controls.append(ft.Text(self.content_text, size=18))
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
                            on_click=lambda e: print(f"Reaction clicked: {reaction_emoji}")
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
                padding=ft.padding.only(left=20, right=20, top=10, bottom=10)
            )

            if self.is_user:
                self.alignment = ft.MainAxisAlignment.END
                message_container.bgcolor = ft.Colors.PINK_800
                message_container.border_radius = ft.border_radius.only(top_left=20, top_right=5, bottom_left=20, bottom_right=5)
            else:
                self.alignment = ft.MainAxisAlignment.START
                message_container.bgcolor = ft.Colors.GREY_900
                message_container.border_radius = ft.border_radius.only(top_left=5, top_right=20, bottom_left=5, bottom_right=20)
            
            self.controls.append(message_container)

    # Изменение статуса
    def change_status(new_status: Dict[str, ft.Colors] = {"text": "В сети", "color": ft.Colors.GREEN}):
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
    
    
    def send_chart_message_chat(text: str):
        chat_compliment.controls.append(ChatMessage(1, text, is_user=False))
        chat_compliment.update()
        
    
    
        

    def send_message_chat(e):
        if message_input.value.replace(" ", "") != "":
            text = message_input.value
            chat_compliment.controls.append(ChatMessage(1, message_input.value, is_user=True))
            message_input.value = ""
            message_input.update()
            input_message_change(message_input)
            chat_compliment.update()
            msgs.append({"role": "user", "content": text})
            change_status({"text": "Печатает...", "color": ft.Colors.BLUE})
            response = client.chat.completions.create(
                model=model,
                messages=msgs,
                temperature=1.5,
                # tools=tools,
                # tool_choice="auto"
            )
            otvet = "Извини, я не могу ответить на это сейчас."

            if response.choices:
                choice = response.choices[0]
                if choice.finish_reason == "tool_calls":
                    function_calls = choice.message.tool_calls
                    # Append the assistant message that contained the tool_calls request
                    msgs.append(choice.message)
                    for function in function_calls:
                        if function.function.name == "image":
                            try:
                                prompt_json = json.loads(function.function.arguments)
                                prompt_content = prompt_json["prompt"]
                                face = prompt_json["face"]
                                print("Создать изображение по промпту:", prompt_content)
                                image_base64 = generate_image(prompt_content)
                                if face:
                                    face_base64 = image_to_base64(f'assets/chapters/photos/{profile["id"]}.jpg')
                                    image_base64 = swap_face(face_base64, image_base64)
                                # Отобразить изображение
                                image_data = base64.b64decode(image_base64)
                                image = Image.open(io.BytesIO(image_data))
                                image.show()

                                image_result_msg = "Успешно созданно и отправленно изображение"
                                tool_response = {
                                    "role": "tool",
                                    "content": image_result_msg,
                                    "tool_call_id": function.id  # Указываем ID вызова функции
                                }
                                # Append the tool response message (content is the result string)
                                msgs.append(tool_response)

                            except Exception as e:
                                    print(f"Error processing tool call 'image': {e}")
                                    # Handle error, maybe append an error message to msgs or set otvet
                                    otvet = "Произошла ошибка при обработке изображения."
                                    # Append a placeholder tool response in case of error? Or handle differently.
                                    msgs.append({
                                        "role": "tool",
                                        "content": f"Ошибка: {e}",
                                        "tool_call_id": function.id
                                    })


                    # Make the second API call AFTER processing ALL tool calls and appending their results
                    try:
                        response = client.chat.completions.create(
                            model=model,
                            messages=msgs # msgs now includes the assistant msg with tool_calls and all tool responses
                        )
                        # Re-check the response after the second call
                        if response.choices and response.choices[0].message:
                            otvet = response.choices[0].message.content
                        else:
                            print("Warning: No message content after tool call response.")
                            # otvet remains the default message set earlier or error message
                    except Exception as e:
                        print(f"Error during second API call after tool execution: {e}")
                        otvet = "Произошла ошибка после обработки запроса функции."


                # Check if message exists after potential tool call or if it was a direct response
                elif choice.message:
                    otvet = choice.message.content
                else:
                    print("Warning: Received response with no message content.")
                    # otvet remains the default message set earlier
            else:
                print("Warning: Received empty response choices.")
                # otvet remains the default message set earlier


            # Ensure otvet is not None before appending (it should have a default value now)
            if otvet is None:
                otvet = "Что-то пошло не так, не могу получить ответ." # Fallback just in case

            msgs.append({"role": "assistant", "content": otvet})
            send_chart_message_chat(otvet)
            change_status({"text": "В сети", "color": ft.Colors.GREEN})
            message_input.focus()
            
            
    back_icon = ft.IconButton(ft.Icons.ARROW_BACK_IOS_NEW)
    name_text = ft.Text(name, size=15)
    status_text = ft.Text(status["text"], color=status["color"])    
    menu_actions = ft.PopupMenuButton(
                    items=[
                        ft.PopupMenuItem(text="Поиск", icon=ft.Icons.SEARCH),
                        ft.PopupMenuItem(text="В начало", icon=ft.Icons.ARROW_CIRCLE_UP_ROUNDED),
                        ft.PopupMenuItem(),
                        ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.BLOCK_ROUNDED, color=ft.Colors.RED), ft.Text("Заблокировать", color=ft.Colors.RED)])),
                        ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.REPORT_PROBLEM_ROUNDED, color=ft.Colors.RED), ft.Text("Пожаловаться", color=ft.Colors.RED)])),
                        ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.DELETE_ROUNDED, color=ft.Colors.RED), ft.Text("Удалить чат", color=ft.Colors.RED)])),
                        
                    ],
                    tooltip=""
                )
    # СОздай верхнюю навигацию
    avatar = ft.Container(height=40, width=40, bgcolor=ft.Colors.GREY, border_radius=20, image=ft.DecorationImage(src=f"chapters/photos/{id}.jpg", fit=ft.ImageFit.COVER, filter_quality=ft.FilterQuality.HIGH))
    top_navigation = ft.Container(
            ft.Row([
                ft.Row([back_icon, 
                avatar,
                ft.Container(ft.Column([name_text, status_text], spacing=1, alignment=ft.MainAxisAlignment.CENTER))]),
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
    chat_compliment = ft.Column([
        ChatMessage(1, "Взаимно вас лайнул(а)", is_user=False)
            ], alignment=ft.MainAxisAlignment.END, spacing=5)
    chat_content = ft.Container(
        ft.SelectionArea(chat_compliment), 
        expand=True)
    
    page.add(chat_content)
    message_input = ft.TextField(hint_text="Сообщение",  multiline=True, max_lines=6, expand=True, border=ft.InputBorder.NONE, on_change=input_message_change, on_submit=send_message_chat)
    file_input_button = ft.IconButton(ft.Icons.ATTACH_FILE_ROUNDED, height=50, width=50)
    voice_message_button = ft.IconButton(ft.Icons.MIC_ROUNDED, height=50, width=50, on_click=toggle_voice_video_button)
    video_message_button = ft.IconButton(ft.Icons.CAMERA_ROUNDED, height=50, width=50, on_click=toggle_voice_video_button)
    send_action_bottom_switch = ft.AnimatedSwitcher(voice_message_button, transition=ft.AnimatedSwitcherTransition.ROTATION, reverse_duration=10, duration=500, switch_in_curve=ft.AnimationCurve.EASE_OUT_BACK, data="mic")
    send_message_button = ft.IconButton(ft.Icons.SEND_ROUNDED, height=50, width=50, on_click=send_message_chat)
    
    bottom_nav_row = ft.Row([file_input_button, message_input, send_action_bottom_switch], spacing=1, vertical_alignment=ft.CrossAxisAlignment.END)
    page.add(ft.Container(
        bottom_nav_row,
        padding=ft.padding.only(bottom=10),
        bgcolor=ft.Colors.GREY_900
            ))
    page.update()


