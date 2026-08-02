from fastapi import APIRouter
from ..models.schemas import UserCreate, UserResponse
import uuid

router = APIRouter(
    prefix="/user",
    tags=["user"]
)

@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate):
    # Logic to save user would go here (Service/DB)
    user_id = str(uuid.uuid4())
    # Mock response
    return UserResponse(id=user_id, **user.model_dump())

@router.get("/{user_id}")
async def get_user(user_id: str):
    return {"id": user_id, "name": "Test User"}
