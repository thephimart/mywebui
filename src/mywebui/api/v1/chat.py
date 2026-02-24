"""Chat API routes with WebSocket support."""

import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from mywebui.db import connection
from mywebui.schemas.api import UserResponse
from mywebui.core.agents import AgentOrchestrator

router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message model."""
    content: str
    session_id: uuid.UUID | None = None


class ChatMessageResponse(BaseModel):
    """Chat message response."""
    msg_id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    timestamp: datetime


class StreamRequest(BaseModel):
    """Streaming chat request."""
    message: str
    session_id: uuid.UUID | None = None


async def get_current_user(request: Request) -> dict:
    """Get current authenticated user from request state."""
    if not hasattr(request.state, "user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    return {
        "user_id": request.state.user_id,
        "username": request.state.username,
    }


@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket):
    """WebSocket endpoint for chat."""
    await websocket.accept()
    
    orchestrator = AgentOrchestrator()
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            msg_type = message.get("type")
            
            if msg_type == "user_message":
                payload = message.get("data", {})
                content = payload.get("content", "")
                session_id = payload.get("session_id")
                
                result = await orchestrator.process_message(content)
                
                if result.error:
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": result.error}
                    })
                else:
                    await websocket.send_json({
                        "type": "assistant_delta",
                        "data": {"content": result.content}
                    })
                
                await websocket.send_json({
                    "type": "done",
                    "data": {}
                })
                
            elif msg_type == "cancel":
                orchestrator.reset()
                await websocket.send_json({
                    "type": "done",
                    "data": {}
                })
            else:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": f"Unknown message type: {msg_type}"}
                })
                
    except WebSocketDisconnect:
        pass


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessage,
    http_request: Request,
    db: AsyncSession = Depends(connection.get_docs_db),
):
    """Send a chat message (REST fallback)."""
    if not hasattr(http_request.state, "user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    return ChatMessageResponse(
        msg_id=uuid.uuid4(),
        session_id=request.session_id or uuid.uuid4(),
        role="user",
        content=request.content,
        timestamp=datetime.utcnow(),
    )


@router.post("/stream")
async def stream_chat(
    request: StreamRequest,
    http_request: Request,
):
    """Stream chat response using Server-Sent Events."""
    if not hasattr(http_request.state, "user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    async def event_generator():
        orchestrator = AgentOrchestrator()
        
        result = await orchestrator.process_message(request.message)
        
        if result.error:
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': result.error}})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'assistant_delta', 'data': {'content': result.content}})}\n\n"
        
        yield f"data: {json.dumps({'type': 'done', 'data': {}})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
