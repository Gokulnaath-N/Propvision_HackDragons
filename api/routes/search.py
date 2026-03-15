import os
import time
import uuid
import redis
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from api.database import get_db, SearchHistory
from api.routes.auth import get_current_user_optional
from src.agents.orchestrator import search_properties
from src.utils.logger import get_logger
from dotenv import load_dotenv

load_dotenv()
logger = get_logger(__name__)

router = APIRouter(prefix="/search", tags=["search"])

def get_redis():
    """Helper to lazily connect to Redis, or None if unavailable"""
    try:
        r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        r.ping()
        return r
    except Exception:
        return None

# ==========================================
# PYDANTIC MODELS
# ==========================================
class SearchRequest(BaseModel):
    query: str
    country: Optional[str] = None
    city: Optional[str] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    bhk: Optional[int] = None
    vastu: Optional[bool] = None
    conversation_history: Optional[List[dict]] = []

class SearchResult(BaseModel):
    listing_id: str
    match_score: float
    rerank_score: float
    room_type: str
    image_path: str
    quality_grade: str
    city: str
    price: float
    bhk: int
    vastu: bool
    match_explanation: Optional[str] = None
    component_scores: Optional[dict] = None

class SearchResponse(BaseModel):
    results: List[dict]
    total: int
    query: str
    parsed_intent: dict
    search_time_ms: float
    clip_query_used: Optional[str] = None

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def format_price_indian(price: float) -> str:
    """Format large numerical Indian Rupee values to Crores or Lakhs."""
    if price >= 10000000:
        return f"{price/10000000:.1f} Cr"
    if price >= 100000:
        return f"{price/100000:.1f} L"
    return str(int(price))

# ==========================================
# ENDPOINTS
# ==========================================
@router.post("", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """
    Core Search API endpoint. Evaluates frontend 'query', extracts semantic intents 
    using Gemini, filters Qdrant via Hybrid Search, and reranks match values.
    """
    
    # 1. VALIDATE QUERY
    if not request.query or len(request.query.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query too short")
        
    # 2. RATE LIMIT (Anonymous Users Limited to 3 Searches)
    if not current_user:
         redis_client = get_redis()
         client_ip = http_request.client.host if http_request.client else "unknown_ip"
         
         if redis_client:
             usage_key = f"anon_search_count:{client_ip}"
             current_usage = redis_client.get(usage_key)
             
             if current_usage and int(current_usage) >= 100:
                 raise HTTPException(
                     status_code=429, 
                     detail="Maximum anonymous searches reached. Please log in or sign up to continue."
                 )
             
             redis_client.incr(usage_key)
             redis_client.expire(usage_key, 86400) # Reset anon search limit after 24 hrs
    
    # 3. BUILD FILTERS
    filters = {}
    if request.city: filters["city"] = request.city
    if request.bhk: filters["bhk"] = request.bhk
    if request.price_max: filters["price_max"] = request.price_max
    if request.price_min: filters["price_min"] = request.price_min
    if request.vastu is not None: filters["vastu"] = request.vastu
    
    # 4. RUN SEARCH PIPELINE
    try:
        logger.info(f"Executing search: {request.query}")
        state = search_properties(
            query=request.query,
            filters=filters,
            history=request.conversation_history or [],
            clip_embedder=getattr(http_request.app.state, "clip", None)
        )
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search Engine Error: {str(e)}")
        
    # 5. FORMAT RESULTS FOR FRONTEND
    results = state.get("reranked_results", [])
    explanations = state.get("match_explanations", {})
    
    formatted_results = []
    for result in results:
        listing_id = result.get("listing_id")
        price = result.get("price", 0)
        rerank_score = result.get("rerank_score", 0)
        
        formatted_results.append({
            "listing_id": listing_id,
            "match_score": result.get("match_score", 0),
            "rerank_score": rerank_score,
            "match_percentage": round(rerank_score * 100, 1),
            "room_type": result.get("room_type", ""),
            "image_url": result.get("image_path", ""),
            "quality_grade": result.get("quality_grade", "C"),
            "city": result.get("city", ""),
            "price": price,
            "price_display": format_price_indian(price),
            "bhk": result.get("bhk", 0),
            "vastu": result.get("vastu", False),
            "match_explanation": explanations.get(listing_id, ""),
            "component_scores": result.get("component_scores", {})
        })
        
    # 6. SAVE TO SEARCH HISTORY IF AUTHENTICATED
    if current_user:
        try:
            history = SearchHistory(
                id=str(uuid.uuid4()),
                user_id=current_user.id,
                query=request.query,
                parsed_intent=state.get("parsed_intent", {}),
                results_count=len(formatted_results)
            )
            db.add(history)
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to save search history for {current_user.id}: {e}")
            
    parsed_intent = state.get("parsed_intent", {})
    
    return SearchResponse(
        results=formatted_results,
        total=len(formatted_results),
        query=request.query,
        parsed_intent=parsed_intent,
        search_time_ms=state.get("search_time_ms", 0),
        clip_query_used=parsed_intent.get("clip_search_query", request.query)
    )
