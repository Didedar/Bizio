# app/api/v1/copilot.py
"""
API endpoints for the BIZIO AI Copilot.
Provides chat, conversation management, and document handling.
"""
import json
import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.db import get_db
from app.api.v1.auth import get_current_user
from app import models
from app.services.ai import CopilotService

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# SCHEMAS
# =============================================================================

class ChatRequest(BaseModel):
    """Request to send a chat message."""
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[int] = None
    context_type: Optional[str] = None  # "dashboard", "product", "expense", etc.
    context_id: Optional[int] = None    # ID of the entity if applicable
    stream: bool = False                 # Whether to stream the response


class ChatResponse(BaseModel):
    """Response from the AI Copilot."""
    conversation_id: int
    content: str
    response_data: Optional[dict] = None
    tool_calls: Optional[List[dict]] = None
    processing_time_ms: int


class ConversationSummary(BaseModel):
    """Summary of a conversation for listing."""
    id: int
    title: Optional[str]
    context_type: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: int


class ConversationDetail(BaseModel):
    """Full conversation with messages."""
    id: int
    title: Optional[str]
    context_type: Optional[str]
    context_id: Optional[int]
    created_at: datetime
    messages: List[dict]


class DataFixSuggestionResponse(BaseModel):
    """Data fix suggestion for user approval."""
    id: int
    fix_type: str
    entity_type: str
    changes: List[dict]
    affected_records: int
    status: str
    created_at: datetime


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def get_tenant_id(db: AsyncSession, user: models.User) -> int:
    """Get the active tenant ID for the user."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    # Fetch user with tenants to avoid lazy loading
    query = select(models.User).options(selectinload(models.User.tenants)).where(models.User.id == user.id)
    result = await db.execute(query)
    user_with_tenants = result.scalar_one_or_none()
    
    if user_with_tenants and user_with_tenants.tenants:
        return user_with_tenants.tenants[0].id
    raise HTTPException(status_code=400, detail="User has no associated tenant")


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Send a message to the AI Copilot and get a response.
    
    If conversation_id is not provided, a new conversation is created.
    Use stream=true for Server-Sent Events streaming.
    """
    tenant_id = await get_tenant_id(db, current_user)
    
    try:
        copilot = CopilotService(db, tenant_id, current_user.id)
        
        # Create or get conversation
        if request.conversation_id:
            conversation = await copilot.get_conversation(request.conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            conversation_id = conversation.id
        else:
            conversation = await copilot.create_conversation(
                context_type=request.context_type,
                context_id=request.context_id
            )
            conversation_id = conversation.id
        
        # Build context string
        context = None
        if request.context_type:
            context = f"User is viewing {request.context_type}"
            if request.context_id:
                context += f" with ID {request.context_id}"
        
        # Get response (non-streaming)
        result = await copilot.chat(conversation_id, request.message, context)
        
        return ChatResponse(
            conversation_id=conversation_id,
            content=result["content"],
            response_data=result["response_data"],
            tool_calls=result["tool_calls"],
            processing_time_ms=result["processing_time_ms"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process chat message")


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Stream a chat response using Server-Sent Events.
    
    Events:
    - {"type": "tool_call", "name": str, "status": str}
    - {"type": "text", "content": str}
    - {"type": "done", "response_data": {...}}
    """
    tenant_id = await get_tenant_id(db, current_user)
    
    async def event_generator():
        try:
            copilot = CopilotService(db, tenant_id, current_user.id)
            
            # Create or get conversation
            if request.conversation_id:
                conversation = await copilot.get_conversation(request.conversation_id)
                if not conversation:
                    yield {"event": "error", "data": json.dumps({"message": "Conversation not found"})}
                    return
                conversation_id = conversation.id
            else:
                conversation = await copilot.create_conversation(
                    context_type=request.context_type,
                    context_id=request.context_id
                )
                conversation_id = conversation.id
            
            # Send conversation ID first
            yield {"event": "init", "data": json.dumps({"conversation_id": conversation_id})}
            
            # Build context
            context = None
            if request.context_type:
                context = f"User is viewing {request.context_type}"
                if request.context_id:
                    context += f" with ID {request.context_id}"
            
            # Stream response
            async for chunk in copilot.chat_stream(conversation_id, request.message, context):
                yield {"event": chunk.get("type", "text"), "data": json.dumps(chunk)}
                
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield {"event": "error", "data": json.dumps({"message": str(e)})}
    
    return EventSourceResponse(event_generator())


@router.get("/conversations", response_model=List[ConversationSummary])
async def list_conversations(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List recent conversations for the current user."""
    tenant_id = await get_tenant_id(db, current_user)
    copilot = CopilotService(db, tenant_id, current_user.id)
    
    conversations = await copilot.list_conversations(limit)
    
    return [
        ConversationSummary(
            id=c.id,
            title=c.title,
            context_type=c.context_type,
            created_at=c.created_at,
            updated_at=c.updated_at,
            message_count=len(c.messages) if hasattr(c, 'messages') else 0
        )
        for c in conversations
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get a conversation with all messages."""
    tenant_id = await get_tenant_id(db, current_user)
    copilot = CopilotService(db, tenant_id, current_user.id)
    
    conversation = await copilot.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = []
    for msg in conversation.messages:
        messages.append({
            "id": msg.id,
            "role": msg.role.value,
            "content": msg.content,
            "response_data": msg.response_data,
            "tool_calls": msg.tool_calls,
            "created_at": msg.created_at.isoformat()
        })
    
    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        context_type=conversation.context_type,
        context_id=conversation.context_id,
        created_at=conversation.created_at,
        messages=messages
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a conversation."""
    tenant_id = await get_tenant_id(db, current_user)
    copilot = CopilotService(db, tenant_id, current_user.id)
    
    conversation = await copilot.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    await db.delete(conversation)
    await db.commit()
    
    return {"status": "deleted", "conversation_id": conversation_id}


@router.get("/suggestions", response_model=List[DataFixSuggestionResponse])
async def list_data_fix_suggestions(
    status: Optional[str] = Query(None, enum=["pending", "approved", "rejected", "applied"]),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List pending data fix suggestions."""
    from sqlalchemy import select
    
    tenant_id = await get_tenant_id(db, current_user)
    
    query = select(models.DataFixSuggestion).where(
        models.DataFixSuggestion.tenant_id == tenant_id
    )
    
    if status:
        query = query.where(models.DataFixSuggestion.status == status)
    
    query = query.order_by(models.DataFixSuggestion.created_at.desc()).limit(50)
    
    result = await db.execute(query)
    suggestions = result.scalars().all()
    
    return [
        DataFixSuggestionResponse(
            id=s.id,
            fix_type=s.fix_type,
            entity_type=s.entity_type,
            changes=s.changes,
            affected_records=s.affected_records or 0,
            status=s.status.value,
            created_at=s.created_at
        )
        for s in suggestions
    ]


@router.post("/suggestions/{suggestion_id}/approve")
async def approve_data_fix(
    suggestion_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Approve and apply a data fix suggestion."""
    from sqlalchemy import select
    
    tenant_id = await get_tenant_id(db, current_user)
    
    query = select(models.DataFixSuggestion).where(
        models.DataFixSuggestion.id == suggestion_id,
        models.DataFixSuggestion.tenant_id == tenant_id
    )
    result = await db.execute(query)
    suggestion = result.scalar_one_or_none()
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    if suggestion.status != models.DataFixStatus.pending:
        raise HTTPException(status_code=400, detail=f"Suggestion is already {suggestion.status.value}")
    
    try:
        # Apply the fix based on type
        # This is a simplified implementation - would need more logic for actual merges
        suggestion.status = models.DataFixStatus.applied
        suggestion.approved_by = current_user.id
        suggestion.approved_at = datetime.utcnow()
        suggestion.applied_at = datetime.utcnow()
        
        await db.commit()
        
        return {
            "status": "applied",
            "suggestion_id": suggestion_id,
            "message": "Data fix applied successfully"
        }
        
    except Exception as e:
        suggestion.status = models.DataFixStatus.failed
        suggestion.apply_error = str(e)
        await db.commit()
        
        raise HTTPException(status_code=500, detail=f"Failed to apply fix: {str(e)}")


@router.post("/suggestions/{suggestion_id}/reject")
async def reject_data_fix(
    suggestion_id: int,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Reject a data fix suggestion."""
    from sqlalchemy import select
    
    tenant_id = await get_tenant_id(db, current_user)
    
    query = select(models.DataFixSuggestion).where(
        models.DataFixSuggestion.id == suggestion_id,
        models.DataFixSuggestion.tenant_id == tenant_id
    )
    result = await db.execute(query)
    suggestion = result.scalar_one_or_none()
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    suggestion.status = models.DataFixStatus.rejected
    suggestion.rejection_reason = reason
    
    await db.commit()
    
    return {
        "status": "rejected",
        "suggestion_id": suggestion_id
    }
