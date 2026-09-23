"""Private, persisted tutor conversations using the existing provider service."""
from datetime import datetime, timezone, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from openai import OpenAIError
from app.core.config import settings
from app.core.database import get_db
from app.dependencies import get_current_user
from app.models import User, AIConversation, AIMessage
from app.schemas.ai import ChatRequest, ChatResponse, DebugRequest, DebugResponse
from app.services.ai_tutor import AITutor

from app.core.rate_limit import limit_requests

router = APIRouter(dependencies=[Depends(limit_requests("ai", 60))])


def get_ai_tutor():
    if not settings.openai_api_key.strip():
        raise HTTPException(503, "AI tutor is unavailable. Configure the backend OPENAI_API_KEY.")
    return AITutor()


@router.get("/conversations")
def conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [{"id": c.conversation_id, "title": c.title} for c in db.query(AIConversation).filter_by(user_id=user.user_id).order_by(AIConversation.updated_at.desc()).limit(50)]


@router.get("/conversations/{conversation_id}")
def messages(conversation_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conversation = db.query(AIConversation).filter_by(conversation_id=conversation_id, user_id=user.user_id).first()
    if not conversation:
        raise HTTPException(404, "Conversation not found")
    return [{"role": m.sender_type, "content": m.message} for m in db.query(AIMessage).filter_by(conversation_id=conversation_id).order_by(AIMessage.created_at, AIMessage.message_id)]


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(payload: ChatRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not settings.openai_api_key.strip():
        raise HTTPException(503, "AI tutor is unavailable. Configure the backend OPENAI_API_KEY.")
    conversation = None
    if payload.conversation_id:
        conversation = db.query(AIConversation).filter_by(conversation_id=payload.conversation_id, user_id=user.user_id).first()
        if not conversation:
            raise HTTPException(404, "Conversation not found")
    # One in-flight paid request per account, across workers; do not block the event loop.
    from sqlalchemy.exc import OperationalError
    try:
        db.query(User).filter_by(user_id=user.user_id).with_for_update(nowait=True).one()
    except OperationalError:
        db.rollback()
        raise HTTPException(429, "A request is already running. Please wait.") from None
    recent = db.query(AIMessage).join(AIConversation).filter(AIConversation.user_id == user.user_id, AIMessage.sender_type == "user", AIMessage.created_at > datetime.now(timezone.utc)-timedelta(minutes=1)).count()
    if recent >= 10:
        raise HTTPException(429, "Please wait a minute before sending another message.")
    history = []
    if conversation:
        history = db.query(AIMessage).filter_by(conversation_id=conversation.conversation_id).order_by(AIMessage.created_at.desc()).limit(20).all()[::-1]
    context = {"conversation": [{"role": m.sender_type, "content": m.message} for m in history]}
    if payload.context:
        import json
        if len(json.dumps(payload.context)) > 4000:
            raise HTTPException(422, "Context is too long")
        context["student_context"] = payload.context
    tutor = get_ai_tutor()
    try:
        reply = await tutor.chat(payload.message, context)
        if not reply or not reply.strip():
            raise HTTPException(502, "The AI provider returned no answer. Please try again.")
        if not conversation:
            conversation = AIConversation(user_id=user.user_id, title=payload.message[:100])
            db.add(conversation)
            db.flush()
        conversation.updated_at = datetime.now(timezone.utc)
        db.add(AIMessage(conversation_id=conversation.conversation_id, sender_type="user", message=payload.message))
        db.flush()
        db.add(AIMessage(conversation_id=conversation.conversation_id, sender_type="assistant", message=reply))
        db.commit()
        return ChatResponse(reply=reply, conversation_id=conversation.conversation_id)
    except OpenAIError:
        db.rollback()
        raise HTTPException(502, "The AI provider is unavailable. Please try again later.") from None
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, "The conversation could not be saved. Please try again.") from None
    finally:
        await tutor.client.close()


@router.post("/debug", response_model=DebugResponse)
async def ai_debug(payload: DebugRequest, user: User = Depends(get_current_user)):
    tutor = get_ai_tutor()
    try:
        return await tutor.debug_code(payload.code, payload.error)
    except OpenAIError:
        raise HTTPException(502, "The AI provider is unavailable. Please try again later.") from None
    finally:
        await tutor.client.close()
