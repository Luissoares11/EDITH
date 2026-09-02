"""Chat endpoints for conversation with E.D.I.T.H."""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from core.process import process_input
from memory.context import make_context
from memory.store import add_message, create_conversation, get_conversation_history

router = APIRouter(prefix="/api/chat", tags=["chat"])


class MessageRequest(BaseModel):
    """Request model for chat messages."""
    message: str
    session_id: str = "default"
    intent: Optional[str] = None


class MessageResponse(BaseModel):
    """Response model for chat messages."""
    message_id: int
    response: str
    ok: bool
    error_type: str | None = None
    detail: str | None = None
    intent: Optional[str] = None


class ConversationMessage(BaseModel):
    """A message in conversation history."""
    id: int
    role: str
    content: str
    intent: Optional[str]
    created_at: str


@router.post("/message", response_model=MessageResponse)
async def send_message(request: Request, msg: MessageRequest) -> MessageResponse:
    """
    Send a message to E.D.I.T.H. and get a response.

    - **message**: The user's input message
    - **session_id**: Optional session identifier for context persistence
    - **intent**: Optional pre-parsed intent (for testing)
    """
    # Get or create context for this session
    if not hasattr(request.app.state, 'contexts'):
        request.app.state.contexts = {}
    if not hasattr(request.app.state, 'conversations'):
        request.app.state.conversations = {}

    ctx = request.app.state.contexts.get(msg.session_id)
    if ctx is None:
        ctx = make_context()
        request.app.state.contexts[msg.session_id] = ctx

    # Get or create conversation
    conv_id = request.app.state.conversations.get(msg.session_id)
    if conv_id is None:
        conv_id = create_conversation(msg.session_id)
        request.app.state.conversations[msg.session_id] = conv_id

    # Log user message
    user_msg_id = add_message(conv_id, msg.session_id, "user", msg.message, msg.intent)

    # Process the input
    result = process_input(msg.message, ctx)

    # Log assistant response
    assistant_msg_id = add_message(
        conv_id, msg.session_id, "assistant", result['response'],
        intent=msg.intent
    )

    return MessageResponse(
        message_id=assistant_msg_id,
        response=result['response'],
        ok=result['ok'],
        error_type=result.get('error_type'),
        detail=result.get('detail'),
        intent=msg.intent
    )


@router.post("/reset")
async def reset_session(request: Request, session_id: str = "default") -> dict:
    """
    Reset a conversation session (clear context).

    - **session_id**: The session to reset
    """
    if not hasattr(request.app.state, 'contexts'):
        request.app.state.contexts = {}

    request.app.state.contexts.pop(session_id, None)
    return {"message": f"Session '{session_id}' reset"}


@router.get("/sessions")
async def list_sessions(request: Request) -> dict:
    """List all active sessions."""
    if not hasattr(request.app.state, 'contexts'):
        return {"sessions": []}

    return {"sessions": list(request.app.state.contexts.keys())}


@router.get("/history/{session_id}", response_model=List[ConversationMessage])
async def get_history(session_id: str, limit: int = 50) -> List[ConversationMessage]:
    """
    Get conversation history for a session.

    - **session_id**: The session to retrieve history for
    - **limit**: Maximum number of messages (default 50)
    """
    messages = get_conversation_history(session_id, limit=limit)
    return [ConversationMessage(**msg) for msg in messages]
