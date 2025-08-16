from openai import OpenAI
import json
import os
from together import Together
import base64
import io
import requests
from PIL import Image, ImageEnhance
from gemini_exp import generate_image
# def generate_image(prompt: str) -> str:
#     api_key = "SG_4e09e8a1e3933972"
#     url = "https://api.segmind.com/v1/juggernaut-pro-flux"
    
#     data = {
#         "positivePrompt": prompt,
#         "width": 704,
#         "height": 1024,
#         "steps": 4,
#         "seed": 1184522,
#         "CFGScale": 7,
#         "outputFormat": "PNG",
#         "scheduler": "Euler"
#     }
    
#     headers = {'x-api-key': api_key}
    
#     response = requests.post(url, json=data, headers=headers)
    
#     if response.status_code == 200:
#         # Convert the image response content to base64
#         image_data = response.content
#         b64_string = base64.b64encode(image_data).decode('utf-8')
#         return b64_string
#     else:
#         raise Exception(f"Image generation failed with status code {response.status_code}: {response.text}")


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
    

# def generate_image(prompt) -> str:
#     response = clienti.images.generate(
        
#     prompt=prompt,
#     model="black-forest-labs/FLUX.1-schnell-Free",
#     width=704,
#     height=1024,
#     steps=4,
#     n=1,
#         response_format="b64_json",
#         stop=[]
#     )
#     return response.data[0].b64_json

# client = OpenAI(api_key="AIzaSyCFpnpuM4wYEczTK0RbmGnKFo22zCCiyZM", base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
client = OpenAI(api_key="sk-fd001c141070405d89a171c2c4bba0d4", base_url="https://api.deepseek.com")
clienti = Together(api_key="34fc99d79109ef8d1342ce42dd2aa27ac50eefea4d4a966b5f5355ba455750d8")


# prompt = """
#
# Твоя единственная задча это быть персонажем {0}
# Твоя задача, сплатить все качества описанной личности в соответствии с предоставленной схемой, и как можно более точно воплатить и  в общении.
# ВСе то что описанно должно как тов лиять на твою лючность, и формироваться таким образом, чтобы она была вполне реалистична и уникальна.
# Ты зарегестрировался на платформе Fainder и ищищ себе кого то. тебе могут приходить лайки
# **Схема**:
# {1}
# """

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

# Выводим все профили из assets/chapters
print("Напишите имя персонажа:")
for profile in os.listdir('assets/chapters'):
    print(profile.replace('.json', ''))

name = input("> ")

profile = json.load(open(f'assets/chapters/{name}.json', 'r', encoding='utf-8'))

prompt_sys = json.dumps(profile, indent=4, ensure_ascii=False)
system = prompt.format(prompt_sys)
msgs = [
    {"role": "system", "content": system},
    {"role": "user", "content": "SYSTEM: Вам пришел лайк от пользователя 'Алексей 17 лет, ищу обычную красивую девушку. Хожу в качалку' \nНапишите [Лайк], если нравиться, и [Дизлайк], если не нравиться привер ответа: 'лайк', 'дизлайк'"},
    {"role": "assistant", "content": "лайк"}
        ]

#  Проверяем на дизлайк (ОТключено)
# resp = client.chat.completions.create(
#         model="gemini-2.5-flash-preview-04-17",
#         messages=msgs,
#         temperature=0.5,
#     )
# otvet = resp.choices[0].message.content
# msgs.append({"role": "assistant", "content": otvet})
# if "диз" in otvet:
#     print()
#     print("Вы ей не понравились))))", otvet)
#     msgs.append({"role": "user", "content": "SYSTEM: Пожалуйста расскажите причину почему вы отвергли пользователя, она останеться ананимной"})
#     res = client.chat.completions.create(
#         model="gemini-2.5-flash-preview-04-17",
#         messages=msgs,
#         temperature=0.5,
#     )
#     otvet = res.choices[0].message.content
#     print(otvet)
#     msgs.append({"role": "assistant", "content": otvet})
#     exit(0)

print(f"""
{profile["name"]}, {profile['age']}
{profile["message"]}""")
while True:
    message = input("> ")
    msgs.append({"role": "user", "content": message})
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=msgs,
        temperature=0.5,
        tools=tools,
        tool_choice="auto"
    )

    # Initialize otvet to a default value
    otvet = "Извини, я не могу ответить на это сейчас." # Or some other default message

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

                        # Не отправляем base64 в tool_response, только подтверждение
                        image_result_msg = "Изображение отправлено"
                        tool_response = {
                            "role": "tool",
                            "content": image_result_msg,
                            "tool_call_id": function.id
                        }
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
                   model="gemini-2.5-flash-preview-04-17",
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
    print(f"\n{otvet}\n")