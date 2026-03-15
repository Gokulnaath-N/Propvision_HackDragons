import os
import json
import uuid
import time
import shutil
import redis
from pathlib import Path
from typing import List, Optional
from fastapi import (
    APIRouter, Depends, HTTPException,
    UploadFile, File, Form, status, BackgroundTasks
)
from sqlalchemy.orm import Session
from api.database import get_db, save_listing, Listing
from api.routes.auth import get_current_user
from src.utils.logger import get_logger
from dotenv import load_dotenv

load_dotenv()
logger = get_logger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])

def get_redis():
    """Returns a Redis client if available, else None."""
    try:
        r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        r.ping()
        return r
    except Exception:
        return None

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE_MB = 20
MAX_IMAGES = 100

# ==========================================
# ENDPOINTS
# ==========================================
@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def upload_listing(
    listing_id: Optional[str] = Form(None),
    images: List[UploadFile] = File(...),
    city: str = Form(...),
    location: str = Form(""),
    price: float = Form(0.0),
    bhk: int = Form(2),
    vastu: bool = Form(False),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Accepts property imagery from broker agents, commits them locally for workers, 
    and inserts the job manifest to Redis queues.
    """
    # 1. VALIDATE FILES
    if not images:
        raise HTTPException(status_code=400, detail="No images provided")
    if len(images) > MAX_IMAGES:
        raise HTTPException(status_code=400, detail=f"Max {MAX_IMAGES} images allowed")
    
    for image in images:
        ext = Path(image.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Invalid format: {image.filename}")

    # 2. GENERATE GLOBAL ID
    if not listing_id:
        listing_id = f"listing_{uuid.uuid4().hex[:8]}"

    # 3. SAVE TO LOCAL PIPELINE VOLUME
    save_dir = Path(f"data/seeds/{listing_id}")
    save_dir.mkdir(parents=True, exist_ok=True)
    
    saved_paths = []
    
    for idx, image_file in enumerate(images):
        content = await image_file.read()
        
        # Guard limits
        if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
            logger.warning(f"File too large, omitting: {image_file.filename}")
            continue
            
        ext = Path(image_file.filename).suffix.lower()
        save_path = save_dir / f"image_{idx:03d}{ext}"
        
        with open(save_path, "wb") as f:
            f.write(content)
            
        saved_paths.append(str(save_path))
        
    if not saved_paths:
        raise HTTPException(status_code=400, detail="No valid images saved")
        
    logger.info(f"Saved {len(saved_paths)} images to volume for {listing_id}")

    # 4. INITIALIZE REDIS JOB STATUS (Frontend Callback %20)
    redis_client = get_redis()
    if redis_client:
        redis_client.setex(
            f"job_status:{listing_id}",
            86400, # 24 hrs expiry
            json.dumps({
                "job_id": listing_id,
                "status": "processing",
                "progress": 20,
                "stage": "files_saved",
                "details": {"saved": len(saved_paths)}
            })
        )

    # 5. DUMP AGENT METADATA CONTEXT
    metadata = {
        "listing_id": listing_id,
        "city": city,
        "location": location,
        "price": price,
        "bhk": bhk,
        "vastu": vastu,
        "broker_id": current_user.id,
        "broker_email": current_user.email
    }
    
    metadata_path = save_dir / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    # 6. COMMIT TO SUPABASE REGISTRY (Pending State)
    try:
        listing_record = Listing(
            id=listing_id,
            broker_id=current_user.id,
            city=city,
            location=location,
            price=price,
            bhk=bhk,
            vastu_compliant=vastu,
            status="pending"
        )
        db.add(listing_record)
        db.commit()
    except Exception as e:
        logger.warning(f"Initial DB commit failed: {e}")

    # 7. ENQUEUE TASK IN REDIS BLPOP WORKER (Frontend Callback %50)
    if redis_client:
        job_data = {
            "listing_id": listing_id,
            "image_paths": saved_paths,
            "metadata": metadata,
            "retry_count": 0
        }
        redis_client.lpush("propvision_jobs", json.dumps(job_data))
        
        redis_client.setex(
            f"job_status:{listing_id}",
            86400,
            json.dumps({
                "job_id": listing_id,
                "status": "processing",
                "progress": 50,
                "stage": "queued",
                "details": {"queue": "propvision_jobs"}
            })
        )

    return {
        "job_id": listing_id,
        "status": "queued",
        "message": "Processing started in background",
        "image_count": len(saved_paths),
        "listing_id": listing_id
    }

@router.post("/demo")
async def upload_demo():
    """
    Mock endpoint to cleanly support demonstration interface workflows 
    without enforcing authentication or expensive local GPU tasks.
    """
    return {
        "job_id": f"demo_{uuid.uuid4().hex[:8]}",
        "status": "complete",
        "message": "Demo processing complete",
        "progress": 100,
        "results": {
            "hero_image": "/demo/sample_hero.jpg",
            "overall_grade": "A",
            "rooms_detected": ["hall", "kitchen", "bedroom"],
            "listing_summary": "Demo property listing showcasing Vastu compliant 2BHK flat."
        }
    }
