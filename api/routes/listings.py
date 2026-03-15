import os
import json
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from api.database import get_db, Listing
from api.routes.auth import get_current_user_optional, get_current_user
from src.utils.logger import get_logger
import redis
from dotenv import load_dotenv

load_dotenv()
logger = get_logger(__name__)
router = APIRouter(prefix="/listings", tags=["listings"])

redis_client = redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379")
)

def format_price_indian(price: float) -> str:
    """Format large numerical Indian Rupee values to Crores or Lakhs."""
    if not price: return "₹0"
    if price >= 10000000:
        return f"₹{price/10000000:.2f} Cr"
    if price >= 100000:
        return f"₹{price/100000:.2f} L"
    return f"₹{int(price):,}"

@router.get("/{listing_id}")
async def get_listing(
    listing_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    # FIND LISTING IN DB
    listing = db.query(Listing).filter(
        Listing.id == listing_id
    ).first()
  
    # CHECK SEEDS FOLDER AS FALLBACK
    metadata = {}
    if not listing:
        seeds_path = Path(f"data/seeds/{listing_id}")
        if not seeds_path.exists():
            raise HTTPException(404, "Listing not found")
      
        metadata_file = seeds_path / "metadata.json"
        if metadata_file.exists():
            metadata = json.loads(metadata_file.read_text())
        else:
            metadata = {"city": "Unknown", "price": 0, "bhk": 0}
  
    # LOAD PIPELINE RESULTS FROM REDIS
    status_key = f"job_status:{listing_id}"
    cached = redis_client.get(status_key)
    pipeline_results = {}
    if cached:
        data = json.loads(cached)
        if data.get("status") == "complete":
            pipeline_results = data.get("details", {})
  
    # LOAD FROM SEEDS FOLDER
    listing_dir = Path(f"data/seeds/{listing_id}")
    enhanced_dir = Path(f"data/enhanced/{listing_id}")
    
    # Find all raw images in listing_dir/raw/
    raw_path = listing_dir / "raw"
    raw_images = []
    if raw_path.exists():
        for ext in ["*.jpg", "*.png", "*.webp"]:
            raw_images.extend(sorted(raw_path.glob(ext)))
    else:
        # Fallback to listing_dir root if no 'raw' subfolder
        for ext in ["*.jpg", "*.png", "*.webp"]:
            raw_images.extend(sorted(listing_dir.glob(ext)))
            
    # Find all enhanced images in enhanced_dir/
    enhanced_images = []
    if enhanced_dir.exists():
        enhanced_images = sorted(list(enhanced_dir.glob("*.webp")))
  
    # BUILD ROOM GALLERY
    room_classifications = pipeline_results.get(
        "room_classifications", []
    )
    
    gallery = []
    gallery_source = pipeline_results.get("gallery_order", enhanced_images)
    
    for idx, img_path in enumerate(gallery_source):
        room_info = next(
            (r for r in room_classifications
             if r.get("image_path") == str(img_path)),
            {"room_type": "room", "confidence": 0}
        )
      
        raw_equivalent = raw_images[idx] if idx < len(raw_images) else None
      
        gallery.append({
            "index": idx,
            "enhanced_url": str(img_path),
            "original_url": str(raw_equivalent) if raw_equivalent else None,
            "room_type": room_info.get("room_type", "room"),
            "room_label": room_info.get("room_type","room").replace("_"," ").title(),
            "confidence": room_info.get("confidence", 0),
            "is_hero": str(img_path) == pipeline_results.get("hero_image")
        })
  
    # BUILD SPATIAL STATS
    spatial = pipeline_results.get("spatial_analyses", [])
    
    all_vastu_signals = []
    all_key_features = []
    conditions = []
    natural_lights = []
    
    for analysis in spatial:
        all_vastu_signals.extend(analysis.get("vastu_signals",[]))
        all_key_features.extend(analysis.get("key_features",[]))
        conditions.append(analysis.get("condition","average"))
        natural_lights.append(analysis.get("natural_light","medium"))
    
    spatial_stats = {
        "vastu_signals": list(set(all_vastu_signals)),
        "vastu_compliant": len(all_vastu_signals) > 0,
        "key_features": list(set(all_key_features))[:8],
        "overall_condition": max(set(conditions),
            key=conditions.count) if conditions else "average",
        "natural_light": max(set(natural_lights),
            key=natural_lights.count) if natural_lights else "medium"
    }
  
    # BUILD QUALITY STATS
    quality_scores = pipeline_results.get("quality_scores", [])
    if quality_scores:
        avg_sharpness = sum(q.get("sharpness_score",0) for q in quality_scores) / len(quality_scores)
        avg_lighting = sum(q.get("lighting_score",0) for q in quality_scores) / len(quality_scores)
        grades = [q.get("grade","C") for q in quality_scores]
    else:
        avg_sharpness = 0
        avg_lighting = 0
        grades = []
    
    quality_stats = {
        "overall_grade": pipeline_results.get("overall_grade","C"),
        "avg_sharpness": round(avg_sharpness, 1),
        "avg_lighting": round(avg_lighting, 1),
        "image_grades": grades,
        "total_images": len(gallery)
    }

    price = metadata.get("price") or (listing.price if listing else 0)
  
    # RETURN COMPLETE LISTING RESPONSE
    return {
        "listing_id": listing_id,
        "city": metadata.get("city") or (listing.city if listing else "Unknown"),
        "location": metadata.get("location") or (listing.location if listing else ""),
        "price": price,
        "price_display": format_price_indian(price),
        "bhk": metadata.get("bhk") or (listing.bhk if listing else 0),
        "vastu_compliant": spatial_stats["vastu_compliant"],
      
        "hero_image": pipeline_results.get("hero_image") or
            (str(enhanced_images[0]) if enhanced_images else None),
        "gallery": gallery,
        "total_images": len(gallery),
      
        "overall_grade": quality_stats["overall_grade"],
        "listing_summary": pipeline_results.get(
            "listing_summary", "Property listing analysis complete."
        ),
        "action_items": pipeline_results.get("action_items",[]),
      
        "spatial_stats": spatial_stats,
        "quality_stats": quality_stats,
      
        "rooms_available": list(set(
            g["room_type"] for g in gallery
        )),
      
        "processing_status": pipeline_results.get(
            "status", "complete"
        )
    }

@router.get("")
async def query_listings(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    PURPOSE: Get all listings for broker dashboard
    Requires auth
    """
    query = db.query(Listing).order_by(Listing.created_at.desc())

    if current_user.role == "broker":
        query = query.filter(Listing.broker_id == current_user.id)
    else:
        query = query.filter(Listing.status == "complete")
    
    listings = query.limit(limit).all()
    
    results = []
    for l in listings:
        results.append({
            "listing_id": l.id,
            "city": l.city,
            "location": l.location,
            "price": l.price,
            "price_display": format_price_indian(l.price),
            "bhk": l.bhk,
            "vastu_compliant": l.vastu_compliant,
            "hero_image": l.hero_image_path,
            "overall_grade": l.overall_grade,
            "status": l.status,
            "created_at": str(l.created_at)
        })
        
    return {"total": len(results), "listings": results}

from fastapi import APIRouter
properties_router = APIRouter(prefix="/properties", tags=["properties"])

@properties_router.get("/{listing_id}")
async def get_property_alias(
    listing_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    return await get_listing(listing_id, db, current_user)
