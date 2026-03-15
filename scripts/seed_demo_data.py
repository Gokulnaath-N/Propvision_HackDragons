
import os
import json
import uuid
import sys
from pathlib import Path
from sqlalchemy.orm import Session

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from api.database import SessionLocal, Listing, User, create_tables
from src.search.indexer import ListingIndexer
from src.utils.logger import get_logger

logger = get_logger(__name__)

def seed_data():
    """
    Seeds local SQLite database and Qdrant Cloud from data/seeds directory.
    """
    logger.info("Starting demo data seeding...")
    
    # 1. Ensure tables exist
    create_tables()
    db = SessionLocal()
    
    # 2. Check if we have any users (we need a broker to own the listings)
    broker = db.query(User).filter(User.role == "broker").first()
    if not broker:
        logger.info("No broker found, creating demo broker...")
        broker = User(
            id=str(uuid.uuid4()),
            email="broker@propvision.ai",
            password_hash="$2b$12$LQv3c1VqBWVH5cuEf.DSe.VjHhO8zG9g6v7X8k7f8g9h0i1j2k3l", # 'password'
            full_name="Demo Broker",
            role="broker",
            city="Chennai",
            is_active=True
        )
        db.add(broker)
        db.commit()
        db.refresh(broker)
    
    # 3. Initialize Indexer
    logger.info("Initializing ListingIndexer (loading ML models)...")
    indexer = ListingIndexer()
    
    # 4. Iterate over seeds
    seed_path = Path("data/seeds")
    if not seed_path.exists():
        logger.error("Seeds directory not found at data/seeds")
        return

    listing_folders = [f for f in seed_path.iterdir() if f.is_dir()]
    logger.info(f"Found {len(listing_folders)} listings to seed.")

    for folder in listing_folders:
        listing_id = folder.name
        
        # Check if already exists in DB
        existing = db.query(Listing).filter(Listing.id == listing_id).first()
        if existing:
            logger.info(f"Listing {listing_id} already exists in DB, skipping...")
            continue
            
        # Load metadata
        metadata = {
            "city": "Chennai",
            "location": "Locality",
            "price": 10000000,
            "bhk": 2,
            "vastu": False
        }
        meta_file = folder / "metadata.json"
        if meta_file.exists():
            with open(meta_file, "r") as f:
                metadata.update(json.load(f))
        
        # Find images
        image_exts = (".jpg", ".jpeg", ".png", ".webp")
        image_paths = [p for p in folder.iterdir() if p.suffix.lower() in image_exts]
        
        if not image_paths:
            logger.warning(f"No images in {folder}, skipping.")
            continue

        logger.info(f"Seeding {listing_id} with {len(image_paths)} images...")
        
        # A. Index in Qdrant
        indexer.index_listing(listing_id, image_paths, metadata)
        
        # B. Create in SQLite
        new_listing = Listing(
            id=listing_id,
            broker_id=broker.id,
            city=metadata.get("city", "Chennai"),
            location=metadata.get("location", ""),
            price=float(metadata.get("price", 0)),
            bhk=int(metadata.get("bhk", 2)),
            vastu_compliant=bool(metadata.get("vastu", False)),
            status="complete",
            hero_image_path=str(image_paths[0]),
            gallery_paths=[str(p) for p in image_paths],
            overall_grade="A",
            listing_summary=f"Luxury {metadata.get('bhk')}BHK property in {metadata.get('city')}.",
            indexed_in_qdrant=True
        )
        db.add(new_listing)
        db.commit()
        logger.info(f"Listing {listing_id} indexed and saved to DB.")

    db.close()
    logger.info("Seeding complete! You can now search for properties.")

if __name__ == "__main__":
    seed_data()
