from fastapi import APIRouter, Depends

from app.modules.auth.interfaces.http.deps import get_current_user
from app.modules.chat.application.dtos import ChatRequest, ChatResponse, FinancialSummaryRequest
from app.modules.chat.application.service import ChatService
from app.modules.users.infrastructure.models import User

router = APIRouter(prefix="/chat", tags=["chat"])


def get_chat_service() -> ChatService:
    return ChatService()


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    return await service.chat(request, user.id)


@router.post("/summary", response_model=dict[str, str])
async def generate_summary(
    request: FinancialSummaryRequest,
    user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> dict[str, str]:
    summary = await service.generate_summary(request, user.id)
    return {"summary": summary}
