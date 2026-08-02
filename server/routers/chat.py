from fastapi import APIRouter
from ..models.schemas import ChatRequest, ChatResponse

router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)

from ..services.chat_service import chat_service

@router.post("/{char_id}/send", response_model=ChatResponse)
async def send_message(char_id: str, chat_request: ChatRequest):
    return chat_service.send_message(char_id, chat_request.content)
