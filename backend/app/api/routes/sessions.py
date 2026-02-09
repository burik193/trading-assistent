"""Sessions: list chats, get session with messages."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.base import Message, Session as ChatSession

router = APIRouter()


@router.get("/sessions")
def list_sessions(db: Session = Depends(get_db)):
    """List all sessions (chats)."""
    sessions = db.query(ChatSession).order_by(ChatSession.created_at.desc()).limit(100).all()
    return [{"id": s.id, "isin": s.isin, "title": s.title, "created_at": s.created_at.isoformat() if s.created_at else None} for s in sessions]


@router.get("/sessions/{session_id}")
def get_session(session_id: int, db: Session = Depends(get_db)):
    """Get session with messages and context."""
    s = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.created_at).all()
    return {
        "id": s.id,
        "isin": s.isin,
        "title": s.title,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "scan_context": s.scan_context,
        "sub_agent_summaries": s.sub_agent_summaries,
        "messages": [{"role": m.role, "content": m.content, "created_at": m.created_at.isoformat() if m.created_at else None} for m in messages],
    }
