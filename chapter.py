import json

class Appearance:
    def __init__(self, appearance: dict) -> None:
        self.face: str = appearance["face"]
        self.body: str = appearance["body"]
        self.defects: list[str] = appearance["defects"]
        self.clothing: str = appearance["clothing"]

class SpeechStyle:
    def __init__(self, speech_style: dict) -> None:
        self.vocabulary: str = speech_style["vocabulary"]
        self.slang: str = speech_style["slang"]
        self.message_length: str = speech_style["message_length"]
        self.swearing: bool = speech_style["swearing"]
        self.style_type: str = speech_style["style_type"]


class ChapterStatic:
    def __init__(self, static: dict) -> None:
        self.family: str = static["family"]
        self.hobbies: list[str] = static["hobbies"]
        self.dislikes: list[str] = static["dislikes"]
        self.character: list[str] = static["character"]
        self.childhood: str = static["childhood"]
        self.appearance: Appearance = Appearance(static["appearance"])
        self.speech_style: SpeechStyle = SpeechStyle(static["speech_style"])
        self.humor_style: str = static["humor_style"]
        self.mental_traumas_and_disorders: str = static["mental_traumas_and_disorders"]
        self.political_preferences: str = static["political_preferences"]
        self.professional_skills: str = static["professional_skills"]

class Chapter:
    def __init__(self, id) -> None:
        self.id = id
        with open(f"assets/chapters/{id}.json", "r", encoding='utf-8') as f:
            self.data = json.load(f)

        self.name: str = self.data["name"]
        self.last_name: str = self.data["last_name"]
        self.age: int = self.data["age"]
        self.date_of_birth: str = self.data["date_of_birth"]
        self.height: int = self.data["height"]
        self.weight: int = self.data["weight"]
        self.gender: str = self.data["gender"]
        self.city: str = self.data["city"]
        self.country: str = self.data["country"]
        self.language: str = self.data["language"]
        self.state_of_life: str = self.data["state_of_life"]
        self.description: str = self.data["description"]
        self.message: str = self.data["message"]
        self.static: ChapterStatic = ChapterStatic(self.data["static"])
        self.image_prompt: str = self.data["image_prompt"]