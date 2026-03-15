import os
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from api.database import get_db, SearchHistory
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["history"])

# PYDANTIC MODELS

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None

class SaveHistoryRequest(BaseModel):
    session_id: Optional[str] = None
    query: str
    results_count: Optional[int] = 0
    messages: Optional[List[ChatMessage]] = []
    parsed_intent: Optional[dict] = {}

class HistoryResponse(BaseModel):
    id: str
    query: str
    results_count: int
    created_at: str
    messages: Optional[List[dict]] = []

@router.get("/history", response_model=List[HistoryResponse])
async def get_history(db: Session = Depends(get_db)):
    """PURPOSE: Get recent search history (No auth required for MVP)"""
    try:
        history = db.query(SearchHistory)\
            .order_by(SearchHistory.created_at.desc())\
            .limit(20)\
            .all()
        
        return [
            {
                "id": h.id,
                "query": h.query,
                "results_count": h.results_count or 0,
                "parsed_intent": h.parsed_intent or {},
                "created_at": str(h.created_at),
                "messages": [] # Not currently stored in database model
            } for h in history
        ]
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        return []

@router.post("/history")
async def save_history(request: SaveHistoryRequest, db: Session = Depends(get_db)):
    """PURPOSE: Save a chat session (No auth required for MVP)"""
    try:
        history = SearchHistory(
            id=str(uuid.uuid4()),
            user_id=None,
            query=request.query,
            parsed_intent=request.parsed_intent or {},
            results_count=request.results_count or 0
        )
        db.add(history)
        db.commit()
        db.refresh(history)
        
        return {
            "id": history.id,
            "query": history.query,
            "status": "saved",
            "created_at": str(history.created_at)
        }
    except Exception as e:
        logger.error(f"Error saving history: {e}")
        raise HTTPException(status_code=500, detail="Failed to save history")

@router.delete("/history/{history_id}")
async def delete_history_item(history_id: str, db: Session = Depends(get_db)):
    """PURPOSE: Delete one history entry"""
    item = db.query(SearchHistory)\
        .filter(SearchHistory.id == history_id)\
        .first()
    if not item:
        raise HTTPException(status_code=404, detail="History not found")
    
    db.delete(item)
    db.commit()
    return {"status": "deleted"}

@router.delete("/history")
async def clear_history(db: Session = Depends(get_db)):
    """PURPOSE: Clear all history"""
    try:
        db.query(SearchHistory).delete()
        db.commit()
        return {"status": "cleared"}
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear history")
