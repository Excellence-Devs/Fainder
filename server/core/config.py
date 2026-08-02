import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "AiFans Server"
    API_V1_STR: str = "/api"
    
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    TOGETHER_API_KEY: str | None = os.getenv("TOGETHER_API_KEY")
    GOOGLE_API_KEY: str | None = os.getenv("GOOGLE_API_KEY")
    SEGMIND_API_KEY: str | None = os.getenv("SEGMIND_API_KEY")
    
    # Paths
    ASSETS_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets")
    CHAPTERS_DIR: str = os.path.join(ASSETS_DIR, "chapters")

settings = Settings()
