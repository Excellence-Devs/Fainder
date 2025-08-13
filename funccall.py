import json
from openai import OpenAI
client = OpenAI(
    api_key="AIzaSyCFpnpuM4wYEczTK0RbmGnKFo22zCCiyZM",
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
                    }
                },
                "required": ["prompt"]
            }
        }
    }
]

messages = [{"role": "system", "content": "Если просят скинуть/показать/сделать фотографию используй функцию image. НИЧЕГО НЕ УТОЧНЯЙ"}, {"role": "user", "content": "Сделай фотографию в кафе"},
            {"role": "assistant", "content": "Один человек или несоклько? ответьте и я сделаю сразу"}, {"role": "user", "content": "один"}]
response = client.chat.completions.create(
  model="gemini-2.5-flash-preview-04-17",
  messages=messages,
  tools=tools,
  tool_choice="auto"
)
print(response)
if response.choices[0].finish_reason == "tool_calls":
    function_calls = response.choices[0].message.tool_calls
    for function in function_calls:
        if function.function.name == "image":
            prompt = json.loads(function.function.arguments)["prompt"]
            print("Создать изображение по промпту:", prompt)
            # Тут например создалось
            image = "Успешно созданно и отправленно изображение"
            tool_response = {
                "role": "tool",
                "content": image,
                "tool_call_id": function.id  # Указываем ID вызова функции
            }

            messages.append(response.choices[0].message)
            messages.append({"role": "user", "content": image})

    response = client.chat.completions.create(
        model="gemini-2.5-flash-preview-04-17",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    print(response.choices[0].message.content)