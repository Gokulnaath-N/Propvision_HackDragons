import os
import json
import redis
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(prefix="/status", tags=["status"])

redis_client = redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379")
)

@router.get("/{job_id}")
async def get_status(job_id: str):
    STATUS_KEY = f"job_status:{job_id}"
    cached = redis_client.get(STATUS_KEY)
    
    if not cached:
        return {
            "job_id": job_id,
            "status": "pending",
            "progress": 0,
            "stage": "queued",
            "message": "Waiting to start processing",
            "details": {}
        }
    
    data = json.loads(cached)
    
    stage_messages = {
        "starting":    "Initializing pipeline...",
        "enhancing":   "Enhancing images with Real-ESRGAN...",
        "classifying": "Classifying rooms with AI...",
        "scoring":     "Scoring image quality...",
        "analyzing":   "Analyzing spatial features...",
        "embedding":   "Generating CLIP embeddings...",
        "synthesizing":"Generating listing intelligence...",
        "indexing":    "Indexing to vector database...",
        "complete":    "Processing complete!",
        "failed":      "Processing failed",
        "queued":      "Queued for processing...",
        "files_saved": "Files saved, starting AI pipeline..."
    }
    
    stage = data.get("stage", "pending")
    message = stage_messages.get(stage, "Processing...")
    
    response = {
        "job_id": job_id,
        "status": data.get("status", "pending"),
        "progress": data.get("progress", 0),
        "stage": stage,
        "message": message,
        "details": data.get("details", {}),
        "timestamp": data.get("timestamp")
    }
    
    if data.get("status") == "complete":
        response["result"] = data.get("details", {})
        
    return response

@router.get("/queue/info")
async def get_queue_info():
    """
    PURPOSE: Get Redis queue length
    Admin info endpoint
    """
    try:
        queue_length = redis_client.llen("propvision_jobs")
        return {
            "queue_length": queue_length,
            "status": "ok"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
