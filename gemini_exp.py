from pydantic import BaseModel
from typing import List
from google import genai
from google.genai import types
import json
import random
import base64
from PIL import Image, ImageEnhance
from openai import OpenAI
from image_flux_generation import FLUX, AscpectRatio
import requests
from io import BytesIO

def process_image(input_path, output_path):
    img = Image.open(input_path).convert('RGB')
    img = ImageEnhance.Color(img).enhance(0.7)
    img = ImageEnhance.Contrast(img).enhance(0.9)
    temp_path = output_path
    img.save(temp_path, "JPEG", quality=30)
    

flux = FLUX(["048790b8-7e38-4a2a-af7f-c886ffb1ede5"])

def url_to_base64(image_url):
    """
    Загружает изображение по URL и конвертирует его в base64
    
    Args:
        image_url (str): Ссылка на изображение
        
    Returns:
        str: Base64 строка изображения
    """
    try:
        # Загружаем изображение по URL
        response = requests.get(image_url)
        response.raise_for_status()  # Проверяем успешность запроса
        
        # Конвертируем в base64
        image_base64 = base64.b64encode(response.content).decode('utf-8')
        
        return image_base64
        
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при загрузке изображения: {e}")
        return None
    except Exception as e:
        print(f"Общая ошибка: {e}")
        return None

def generate_image(prompt) -> str:
    image_poll = flux.kontext_pro(f"{prompt}, realistic handheld photo, taken with a smartphone, natural imperfections, slight motion blur, subtle lens distortion, mild overexposure in highlights, soft shadows, slight chromatic aberration, high ISO grain, ambient light only, natural color cast, no artificial blur, no overly perfect skin", aspect_ratio=AscpectRatio.PORTRAIT)
    image = flux.pooling(image_poll)
    print(image)
    return url_to_base64(image)



  
# Определение Pydantic-моделей для структуры JSON
class Appearance(BaseModel):
    face: str
    body: str
    defects: str
    clothing: str

class SpeechStyle(BaseModel):
    vocabulary: str  # Какие слова использует (формальные, неформальные, сленг)
    slang: str       # Использует ли сленг (да/нет, какой именно)
    message_length: str  # Длина сообщений (короткие, длинные, средние)
    swearing: bool   # Матерится ли
    style_type: str  # Тип стиля: "Холодный старт", "Прямой", "Постепенное привыкание"

class Static(BaseModel):
    family: str
    hobbies: List[str]
    dislikes: List[str]
    character: List[str]
    childhood: str
    mental_traumas_and_disorders: str
    political_preferences: str
    professional_skills: str
    appearance: Appearance
    speech_style: SpeechStyle
    humor_style: str  # Подробное описание стиля юмора

  
class Person(BaseModel):
  name: str
  last_name: str
  patronymic: str
  gender: str
  age: int
  date_of_birth: str
  height: int
  weight: int
  city: str
  country: str
  language: str
  state_of_life: str
  description: str
  message: str
  static: Static
  image_prompt: str



# Настройка клиента Gemini
client = genai.Client(api_key="AIzaSyCFpnpuM4wYEczTK0RbmGnKFo22zCCiyZM")
generati = OpenAI(api_key="AIzaSyAcss1Be1dp_q2Ti9ZLD22Gp_qXr812gbE", base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
# Промпт для Gemini
prompt = """
 Сгенерируйте подробный JSON-объект, описывающий вымышленного персонажа, в соответствии с предоставленной схемой. Ответ должен быть в формате JSON и соответствовать следующей структуре и требованиям:

**Схема**:
{
  "name": str,  // Имя персонажа
  "last_name": str,  // Фамилия персонажа
  "patronymic": str,  // Отчество (если применимо)
  "gender": str,  // Пол (например, "Мужской", "Женский", "Небинарный")
  "age": int,  // Возраст персонажа (должен соответствовать date_of_birth)
  "date_of_birth": str,  // Дата рождения в формате ДД.ММ.ГГГГ, должна соответствовать возрасту
  "height": int,  // Рост в сантиметрах
  "weight": int,  // Вес в килограммах
  "city": str,  // Город проживания
  "country": str,  // Страна проживания
  "language": str,  // Основной язык общения
  "state_of_life": str,  // Текущее жизненное положение (например, "Школа, 11 класс", "Университет, 2 курс", "Работает как...")
  "description": str,  // Краткое описание персонажа, его предпочтений в партнерах и того, что он ищет
  "message": str,  // Публичное сообщение, видимое другим, предназначенное для привлечения внимания. От лица персонажа. обычно если персонаж это зумер или подросток - он пишет с маленькой и какую нить хуйню
  "static": {
    "family": str,  // Семейное положение (например, "Полная семья", "Одинокий родитель", "Сирота")
    "hobbies": list[str],  // Список хобби, интересов и предпочтений (включите широкий спектр, например, еда, люди)
    "dislikes": list[str],  // Список того, что персонаж не любит (например, еда, поведение, концепции)
    "character": list[str],  // Список черт характера (например, "Z-поколение", "Задумчивый", "Дерзкий")
    "childhood": str,  // Подробное описание детства, включая значимые события или истории
    "mental_traumas_and_disorders": str,  // Описание психических травм или расстройств (положительных или отрицательных)
    "samocritics": str, // описание внутреннего "Я" то есть то что девушка думает сама о себе, как думает что воспринимают ее окружающие, и нравится ли она сама себе, что ее тревожит, что ей нравиться, и тд (достаточно подробный пункт) 
    "political_preferences": str,  // Политические взгляды, включая причины и влияния
    "professional_skills": str,  // Профессиональные навыки, в которых персонаж преуспевает
    "appearance": {
      "face": str,  // Подробное описание черт лица (глаза, волосы, нос и т.д.)
      "body": str,  // Подробное описание телосложения (стройное, пышное, спортивное), заметных особенностей. не бойся интимных дееталей. они тоже нкжны
      "defects": str,  // Описание модификаций тела или недостатков (например, татуировки, пирсинг)
      "clothing": str  // Предпочитаемые стили одежды для разных ситуаций (публичные, домашние, свидания)
    },
    "speech_style": {
      "vocabulary": str,  // Какие слова использует (формальные, неформальные, сленг)
      "slang": str,       // Использует ли сленг (да/нет, какой именно)
      "message_length": str,  // Длина сообщений (короткие, длинные, средние)
      "swearing": bool,   // Матерится ли
      "style_type": str   // Тип стиля: "Холодный старт", "Прямой", "Постепенное привыкание"
    },
    "humor_style": str  // Подробное описание стиля юмора с примерами
  },
  "image_prompt": str
}

**Требования**:
1. **Детализация**: Каждое поле должно быть описано подробно. Например:
   - `appearance.face`: Опишите цвет глаз, форму, стиль бровей, цвет волос, название прически, форму носа, форму губ, макияж и т.д.
   - `appearance.body`: Опишите телосложение (стройное, пышное, спортивное), заметные особенности (например, высокие бедра, размер груди), осанку и т.д.
   - `static.childhood`: Включите реалистичные события, истории или травмы, которые могут влиять на общение или личность.
   - `static.mental_traumas_and_disorders`: Укажите триггеры (положительные или отрицательные), которые влияют на настроение или поведение персонажа.
2. **Реализм**: Убедитесь, что все поля согласованы и реалистичны. Например:
   - `age` и `date_of_birth` должны соответствовать текущему году (2025).
   - `height` и `weight` должны быть правдоподобными для описанного телосложения.
   - `state_of_life` должен отражать возраст и ситуацию персонажа.
3. **Триггеры**: В `mental_traumas_and_disorders` включите по крайней мере три конкретных разных триггера (например, фраза, тема или событие), который вызывает сильную эмоциональную реакцию (может быть не только негативную, это может быть позитив. привязанность, возбуждение может и тд).
4. **Предпочтения**: В `description` включите предпочтения персонажа в партнерах (внешность, личность, хобби) и то, что он ищет в отношениях.
5. **Публичное сообщение**: Поле `message` должно быть привлекательным, отражать личность персонажа и предназначено для привлечения внимания других.
6. **Гибкость**: Ответ должен быть структурирован так, чтобы в будущем можно было добавлять дополнительные поля в схему без нарушения логики.
7. **Черты характера**: Поле `static.character` должно включать черты, такие как "Z-поколение" (современный сленг, технически подкованный), "Задумчивый" (философский) или "Дерзкий" (уверенный, откровенный).
8. **Хобби и антипатии**: Включите разнообразный список в `static.hobbies` и `static.dislikes`, охватывающий деятельность, еду, людей или концепции.
9. **Политические предпочтения**: В `static.political_preferences` объясните взгляды персонажа, почему он их придерживается, и любые влияния (например, семья, СМИ).
10. **Профессиональные навыки**: В `static.professional_skills` опишите навыки, в которых персонаж преуспевает (например, программирование, дизайн, преподавание).

**Стиль речи**:
Персонаж должен иметь определенный стиль речи, основанный на следующих исследованиях:
- **Стиль "Холодный старт / Проверка / Подогрев"**: Начинается с коротких, односложных, кажущихся незаинтересованными ответов (примеры: "ясно", "ок", "пон", "понятно"). Это может быть тактикой для проверки настойчивости собеседника. Постепенно, если собеседник продолжает общение, персонаж может "оттаять" и стать более открытым, добавляя эмодзи или более длинные сообщения.
- **Стиль "Прямой / Открытый"**: Общение с самого начала открытое, честное, без "игр". Ответы развернутые, стиль общения постоянен, отражает личность персонажа.
- **Стиль "Постепенное Привыкание / Естественное Раскрытие"**: Начинается сдержанно, но со временем общение становится теплее и глубже по мере выстраивания доверия, естественно раскрывая персонажа.

В поле `speech_style` укажите:
- `vocabulary`: Какие слова использует персонаж (формальные, неформальные, сленг).
- `slang`: Использует ли сленг (да/нет, и если да, то какой, например, "жиза", "кринж").
- `message_length`: Длина сообщений (короткие, длинные, средние).
- `swearing`: Матерится ли персонаж.
- `style_type`: Один из трех стилей: "Холодный старт", "Прямой", "Постепенное привыкание".

**Анализ стиля текстовой коммуникации**:
Стиль речи должен учитывать особенности цифровой переписки:
- **Контекстуальный юмор**: Остроумные реплики, встроенные в диалог, зависят от контекста и скорости реакции.
- **Визуальный юмор**: Использование эмодзи, мемов, стикеров для передачи иронии или эмоций.
- **Абсурдистский юмор**: Случайные, нелогичные фразы или картинки для создания эффекта "настолько глупо, что смешно".
- **Юмор на ошибках**: Опечатки или автокоррекция как источник случайного смеха.
- **Ирония и сарказм**: Использование маркеров (кавычки, эмодзи) для передачи тона.
- **Подколы**: Дружеские шутки, основанные на доверии и общем контексте.

**Юмор**:
Персонаж должен иметь определенный стиль юмора, основанный на следующих исследованиях:

**Исследование природы юмора**:
- **Юмор несоответствия**: Шутки на неожиданном нарушении логики (например, победа в танцах и "пачка колбасы" как приз).
- **Ситуационный/Наблюдательный юмор**: Шутки на основе узнаваемых ситуаций (например, ирония над восторгом от бесплатного ChatGPT).
- **Абсурдистский/Нонсенс юмор**: Полное отсутствие логики (например, лев с подписью "Пирожки" или видео с тараканом под татарскую музыку).
- **Юмор подтрунивания/Подколы**: Дружеские шутки над личными качествами (например, "жирный" или "гном" в дружеском тоне).

**Юмор по поколениям в России**:
- **Поколение X**: Бытовой, ностальгический, черный юмор (анекдоты про СССР, сарказм над трудностями).
- **Поколение Y**: Сарказм про взрослую жизнь, ностальгия по 90-м (мемы про ипотеку, депрессию).
- **Поколение Z**: Абсурдные мемы, TikTok-тренды, сленг ("жиза", "кринж").
- **Поколение Альфа**: Простой юмор из мультфильмов, песенок.

В поле `humor_style` опишите:
- Какой тип юмора предпочитает персонаж (несоответствие, ситуационный, абсурд, подколы).
- Примеры шуток, которые персонаж мог бы использовать в общении.
- Связь с поколением (например, Z-поколение и абсурдные мемы).

Сделаю краткий, применимый набор из 10 типичных концепций фотографий в Tinder, для каждой дам: что это за тип, какие тэги стоит включать в промпт (короткий список), готовый пример промпта (на английском — потому что большинство генеративных моделей лучше понимают английские теги) и короткие пояснения / советы по генерации (на русском). В конце — общая схема построения промпта и checklist для отладки. Негативные промпты здесь не включаю, но в примечаниях скажу, где они обычно полезны.

1) Selfie — близкое селфи «с руки»
Тэги: selfie, self-portrait, arm's length, close-up, soft natural light, shallow depth of field
Пример промпта (ENG):
"selfie, self-portrait from arm's length, close-up head and shoulders, natural soft frontal lighting, warm skin tones, slight smile, blurred background, 50mm portrait, shallow depth of field, realistic photo"
Советы: указывай «arm's length / outstretched arm» и «no phone visible» если не хочешь телефон в кадре; добавляй выражение лица и тип света.

2) Mirror selfie
Тэги: mirror selfie, full body mirror, phone visible, bedroom or bathroom, casual outfit, natural lighting
Пример промпта (ENG):
"mirror selfie, full body reflected in mirror, phone visible in hand, casual outfit, soft window light, realistic, slightly grainy phone photo look, 35mm perspective"
Советы: важно указать «phone visible» или наоборот «no phone visible»; конкретизируй фон (bathroom / bedroom) чтобы получить реалистичные отражения.

3) Full-body standing outdoors
Тэги: full body, standing pose, 3/4 profile, outdoor park/street, natural light, wide shot
Пример промпта (ENG):
"full body portrait, standing 3/4 profile, outdoor park background, natural golden hour lighting, casual streetwear, relaxed posture, full-length, 35mm wide angle, realistic photo"
Советы: указывай расстояние (full body), время суток (golden hour) и окружение — это сильно меняет настроение.

4) Candid / distance street shot
Тэги: candid, taken from distance, 35mm documentary style, unposed, motion, city street
Пример промпта (ENG):
"candid distance shot, subject mid-walk, taken from 10-15 meters, 35mm documentary lens, natural city street background, spontaneous expression, slight motion blur, natural colors, realistic photo"
Советы: «taken from distance / 10-15 meters / no posed look» — ключевые фразы. Добавляй «motion blur» если хочешь ощущение движения.

5) Professional headshot
Тэги: headshot, studio lighting, clean neutral background, shoulders up, professional attire, softbox
Пример промпта (ENG):
"professional headshot, shoulders up, softbox studio lighting, neutral gray background, business casual, confident smile, crisp high-resolution, flattering angle, 85mm portrait lens, realistic"
Советы: для серьёзного профиля указывай «studio», точную framing (head/shoulders) и «85mm» для естественной перспективы.

6) Travel / landmark photo
Тэги: travel photo, landmark in background, wide-angle, looking away, scenic, daylight
Пример промпта (ENG):
"travel photo, subject in foreground looking at landmark in background, wide-angle, scenic vista, candid pose, daylight, casual travel outfit, vibrant colors, realistic photo"
Советы: уточни landmark type (e.g., Eiffel Tower / mountain / coastline) и дистанцию: subject foreground + landmark background.

7) Hobby / action shot (например игра на гитаре)
Тэги: action shot, playing guitar, mid-action, shallow depth, natural indoor light, authentic
Пример промпта (ENG):
"action shot of subject playing acoustic guitar, mid-strum, candid expression, shallow depth of field, warm indoor light from window, authentic, 50mm portrait lens, realistic photograph"
Советы: опиши инструмент/действие + момент («mid-strum», «kneading dough», «swinging bat»). Движение и предметы делают кадр правдоподобным.

8) Photo with pet
Тэги: with dog, interacting with pet, kneeling down, warm tones, close-up/waist up
Пример промпта (ENG):
"portrait with dog, subject kneeling and hugging dog, warm golden light, joyful expression, waist-up framing, natural backyard background, realistic photo"
Советы: укажи тип взаимодействия (hugging, playing) — это ключ к естественности.

9) Night / party photo
Тэги: low light, neon lights, party atmosphere, flash or ambient, bokeh, candid smile
Пример промпта (ENG):
"night party photo, subject in foreground smiling, neon lights and bokeh in background, low light, slight film grain, candid atmosphere, realistic photo"
Советы: для ночи уточняй источник света (neon, string lights, flash) и желаемую обработку (film grain / high ISO look).

10) Creative / editorial portrait
Тэги: artsy portrait, dramatic lighting, off-center composition, film grain, moody color grading
Пример промпта (ENG):
"editorial portrait, dramatic side lighting, off-center composition, moody color grading, film grain, high contrast, fashion-forward styling, 85mm portrait, artistic photo"
Советы: полезно добавить стиль (editorial / magazine / cinematic) и конкретные световые эффекты (rim light, chiaroscuro).

Как строить промпт — простая схема (шаблон)
<subject + action>, <framing/focal length/distance>, <pose/expression>, <lighting/time of day>, <background/scene>, <clothing/style>, <camera/lens>, <photographic style/post-processing>, <realistic photo>
Пример:
"young man smiling, waist-up, looking at camera, soft morning light, urban cafe background, casual shirt, 50mm lens, shallow depth of field, natural colors, realistic photo"

Практические советы по генерации и отладке
Конкретность: чем точнее — тем лучше (distance, lens, light, mood).

Фрейминг и фокус: указывай close-up, waist-up, full body и focal length (50mm/85mm/35mm) — это меняет перспективу.

Освещение: «golden hour», «soft window light», «neon», «studio softbox» — определяет тон.

Реализм: добавь realistic photo, high-resolution, photorealistic.

Аутентичность: мелкие детали (phone visible, pet, guitar) делают фото правдоподобным.

Итерация: генерируй несколько вариантов, меняя одно свойство (например lens или expression).

Negative prompts (опционально): если модель лепит лишнее — используйте no text, no watermark, no extra limbs, no unrealistic artifacts. Я их не включаю по умолчанию, но часто помогают.

Сочетай тэги: для «естественного» тиндер-фото комбинируй candid + warm light + casual clothes.


**Пример**:
{
  "name": "Алина",
  "last_name": "Ким",
  "patronymic": "Сергеевна",
  "gender": "Женский",
  "age": 16,
  "date_of_birth": "03.09.2009",
  "height": 158,
  "weight": 50,
  "city": "Санкт-Петербург",
  "country": "Россия",
  "language": "Русский",
  "state_of_life": "Школа, 10 класс",
  "description": "Любит аниме и мечтает найти друзей, которые разделяют ее страсть к косплею. Ищет кого-то милого и веселого.",
  "message": "Хай, кто тоже за аниме и котиков?",
  "static": {
    "family": "Полная семья",
    "hobbies": ["Аниме", "Косплей", "Рисование", "TikTok"],
    "dislikes": ["Скучные уроки", "Громкие люди", "Холодная еда"],
    "character": ["Z-поколение", "Творческая", "Застенчивая"],
    "childhood": "Росла с кучей манги и аниме от старшего брата.",
    "mental_traumas_and_disorders": "Стесняется, если кто-то критикует ее косплей.",
    "political_preferences": "Не интересуется, считает политику скучной.",
    "samocritics": "Я очень социофобная, мне это не нравиться, я хочу начать общаться с людьми но думаю что я не красивая, мне кажется что все смотрят на мою тутуировку, я очень хочу заняться психологией нго мне лень какая я ужасная",
    "professional_skills": "Рисование артов, монтаж видео",
    "appearance": {
      "face": "Маленькое лицо с большими карими глазами, короткие черные волосы с челкой, тонкие брови, маленький нос.",
      "body": "Худенькая, с узкими плечами, слегка сутулится грудь второго размера заметная.",
      "defects": "Татуировка-сердечко на запястье.",
      "clothing": "Любит толстовки с аниме-принтами, дома носит пижаму с котиками."
    },
    "speech_style": {
      "vocabulary": "Неформальные, с аниме-отсылками",
      "slang": "Да, 'няшка', 'кавай', 'кринж'",
      "message_length": "Короткие",
      "swearing": true,
      "style_type": "Постепенное привыкание"
    },
    "humor_style": ""
  },
  "image_prompt": "" // промпт для картинки
}

Сгенерируйте нового персонажа обеспечив уникальность и реалистичность всех полей. Данные должны быть на русском языке. 

по поводу создания картинок.
Используй промпт на английском, как будто ты пишешь промпт для Midjorney/FLUX, сгенерированное фото будет на анкете персонажа.
Пиши промпт в реалистичном формате, как будто персонаж делает селфи (если он фоткается). или где то фотка. крч как обычно делают селфи.
Промпт-инжиниринг:
В описании (промпте) явно укажите, что фон должен быть четким. Пример: portrait of a person, highly detailed background, sharp environment, no blur, realistic lighting.
Избегайте слов, которые могут ассоциироваться с размытием, таких как bokeh, soft focus, shallow depth of field.
Укажите конкретный тип фона, который должен быть детализированным, например: cityscape background, sharp details, vibrant colors.
Если изображение сделано на телефон указывайте эти тэги, если нет то не указывайте, не всегда должно быть селфи
"""

def generate_person(description: str):
  # Запрос к Gemini
  response = client.models.generate_content(
      model='gemini-2.5-flash',
      contents=description,
      config=types.GenerateContentConfig(
          system_instruction=prompt,
          response_mime_type='application/json',
          response_schema=Person
      ),
  )

  # Вывод JSON-строки
  print(response.text)
  json_sheme = json.loads(response.text)
  json_sheme["id"] = random.randint(1, 1000000)

  print("Генерация картинки...")
  image_prompt = json_sheme["image_prompt"]
  try:
    image_base64 = generate_image(image_prompt)
    print("Картинка сгенерирована")
    with open(f'assets/chapters/photos/{json_sheme["id"]}.png', 'wb') as f:
      f.write(base64.b64decode(image_base64))
    process_image(f'assets/chapters/photos/{json_sheme["id"]}.png', f'assets/chapters/photos/{json_sheme["id"]}.jpg')
  except Exception as e:
    print(f"Ошибка при генерации картинки: {e}")

  with open(f'assets/chapters/{json_sheme["id"]}.json', 'w', encoding='utf-8') as f:
      json.dump(json_sheme, f, indent=4, ensure_ascii=False)

  

  

  return json_sheme['id']

def random_person_generate():
  messages = json.load(open("assets/short_descriptions.json", "r", encoding="utf-8"))
  messages.append({"role": "user", "content": "Следующий"})
  response = generati.chat.completions.create(
      model='gemini-2.0-flash',
      messages=messages,
      temperature=2
  )
  print(response.choices[0].message.content)
  messages.append({"role": "assistant", "content": response.choices[0].message.content})
  json.dump(messages, open("assets/short_descriptions.json", "w", encoding="utf-8"), indent=4, ensure_ascii=False)
  return response.choices[0].message.content
