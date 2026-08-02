from fastapi import APIRouter, HTTPException
from typing import List
from ..services.character_service import character_service
from ..models.schemas import Person

router = APIRouter(
    prefix="/characters",
    tags=["characters"]
)

@router.get("/feed")
async def get_characters_feed():
    """
    Get a feed of characters.
    """
    return character_service.get_all_characters()

@router.get("/{char_id}")
async def get_character(char_id: str):
    """
    Get a specific character by ID.
    """
    char = character_service.get_character(char_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    return char
