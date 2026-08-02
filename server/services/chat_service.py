from ..models.schemas import ChatRequest, ChatResponse

class ChatService:
    def send_message(self, char_id: str, content: str) -> ChatResponse:
        # Logic to call LLM (OpenAI/Together)
        # For now, echo
        return ChatResponse(response=f"Echo from {char_id}: {content}")

chat_service = ChatService()
