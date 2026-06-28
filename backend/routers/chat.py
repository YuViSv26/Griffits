import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from backend.db import User, get_chat_history
from backend.deps import get_current_user
from backend.schemas.chat import ChatHistoryResponse, ChatMessageItem, ChatRequest
from backend.services.chat import chat_complete, chat_stream
from backend.services.profile import is_profile_complete

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.get("/history", response_model=ChatHistoryResponse)
async def chat_history(user: User = Depends(get_current_user)) -> ChatHistoryResponse:
    messages = await get_chat_history(user.id, limit=50)
    return ChatHistoryResponse(
        messages=[
            ChatMessageItem(
                role=m.role,
                content=m.content,
                created_at=m.created_at.isoformat(),
            )
            for m in messages
        ]
    )


@router.post("")
async def chat(body: ChatRequest, user: User = Depends(get_current_user)):
    if not is_profile_complete(user):
        raise HTTPException(
            status_code=400,
            detail="Заполните профиль ребёнка перед использованием чата",
        )

    try:
        if body.stream:
            return StreamingResponse(
                chat_stream(user, body.message),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                },
            )

        content = await chat_complete(user, body.message)
        return {"role": "assistant", "content": content}

    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception:
        logger.exception("Chat error")
        raise HTTPException(status_code=502, detail="Ошибка NordRouter API")
