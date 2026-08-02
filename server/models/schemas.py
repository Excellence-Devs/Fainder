from pydantic import BaseModel
from typing import List, Optional

# --- Character Models (from gemini_exp.py) ---

class Appearance(BaseModel):
    face: str
    body: str
    defects: str
    clothing: str

class SpeechStyle(BaseModel):
    vocabulary: str
    slang: str
    message_length: str
    swearing: bool
    style_type: str

class Static(BaseModel):
    family: str
    hobbies: List[str]
    dislikes: List[str]
    character: List[str]
    childhood: str
    mental_traumas_and_disorders: str
    samocritics: Optional[str] = None # Added based on view_file output
    political_preferences: str
    professional_skills: str
    appearance: Appearance
    speech_style: SpeechStyle
    humor_style: str

class Person(BaseModel):
    id: Optional[str] = None # ID might be generated
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

# --- User Models ---

class UserCreate(BaseModel):
    name: str
    gender: str
    birth_date: str
    photo_base64: Optional[str] = None

class UserResponse(UserCreate):
    id: str
    photo_url: Optional[str] = None

# --- Chat Models ---

class ChatMessage(BaseModel):
    role: str
    content: str
    attachments: List[dict] = []

class ChatRequest(BaseModel):
    content: str
    user_id: str

class ChatResponse(BaseModel):
    response: str
    attachments: List[dict] = []
