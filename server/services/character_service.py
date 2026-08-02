import json
import random
import base64
import os
from typing import List, Optional
from google import genai
from google.genai import types
from openai import OpenAI
from ..core.config import settings
from ..models.schemas import Person

# Initialize clients
# Ensure API keys are set in .env or config
# client = genai.Client(api_key=settings.GOOGLE_API_KEY) 
# generati = OpenAI(api_key=settings.OPENAI_API_KEY, base_url="...") 

# Placeholder for FLUX generation import
# from image_flux_generation import FLUX, AscpectRatio 

class CharacterService:
    def __init__(self):
        self.chapters_dir = settings.CHAPTERS_DIR
        os.makedirs(self.chapters_dir, exist_ok=True)

    def get_all_characters(self) -> List[Person]:
        characters = []
        if not os.path.exists(self.chapters_dir):
            return []
            
        for filename in os.listdir(self.chapters_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.chapters_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # Validate with Pydantic
                        # person = Person(**data) 
                        characters.append(data) # Return dict for now or Person object
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
        return characters

    def get_character(self, char_id: str) -> Optional[dict]:
        filepath = os.path.join(self.chapters_dir, f"{char_id}.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    # Logic from gemini_exp.py would go here (generate_person, etc.)
    # For now, I'm setting up the structure.
    
character_service = CharacterService()
