import uuid
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm

from src.search.qdrant_client import QdrantManager
from src.vision.clip_embedder import CLIPEmbedder
from src.vision.quality_scorer import ImageQualityScorer
from src.vision.spatial_analyzer import SpatialAnalyzer
from src.models.predictor import RoomPredictor
from src.utils.logger import get_logger
from src.utils.gpu_utils import clear_gpu_cache

class ListingIndexer:
    """
    Orchestrate the full PropVision AI pipeline to index property 
    listings into Qdrant. Handles enhancement (optional call before),
    classification, quality scoring, spatial analysis, and semantic embedding.
    """
    def __init__(self):
        self.logger = get_logger(__name__)
        self.logger.info("Initializing ListingIndexer...")
        
        self.qdrant = QdrantManager()
        self.qdrant.create_collection()
        
        self.clip = CLIPEmbedder()
        self.scorer = ImageQualityScorer()
        self.predictor = RoomPredictor()
        self.spatial = SpatialAnalyzer()
        
        self.logger.info("ListingIndexer ready")

    def index_listing(self, listing_id: str, image_paths: List[Path], metadata: Dict) -> Dict:
        """
        Index all images for one property listing with full vision processing.
        """
        points_to_upsert = []
        results_summary = []
        failed = []
        
        self.logger.info(f"Indexing listing {listing_id}: {len(image_paths)} images")
        
        for idx, image_path in enumerate(tqdm(image_paths, desc=f"Indexing {listing_id}")):
            try:
                # Ensure path is Path object
                img_path = Path(image_path)
                
                # STEP 1 — CLIP EMBEDDING
                embedding = self.clip.embed_image(img_path)
                if embedding is None:
                    self.logger.warning(f"Embedding failed for {img_path}")
                    failed.append(str(img_path))
                    continue
                
                # STEP 2 — ROOM CLASSIFICATION
                prediction = self.predictor.predict(img_path)
                room_type = prediction["predicted_class"]
                confidence = prediction["confidence"]
                
                # Filter low confidence rooms
                if confidence < 0.60:
                    room_type = "unknown"
                
                # STEP 3 — QUALITY SCORE
                quality = self.scorer.score(img_path)
                grade = quality["grade"]
                final_score = quality["final_score"]
                
                # STEP 4 — SPATIAL ANALYSIS (Added for Datathon completeness)
                # We try-except this individually as it's an external API
                spatial_data = {}
                try:
                    spatial_data = self.spatial.analyze(img_path, room_type)
                except Exception as e:
                    self.logger.warning(f"Spatial analysis skipped for {img_path}: {e}")
                
                # STEP 5 — BUILD PAYLOAD
                payload = {
                    "listing_id": listing_id,
                    "image_index": idx,
                    "image_path": str(img_path),
                    "room_type": room_type,
                    "room_confidence": float(confidence),
                    "quality_grade": grade,
                    "quality_score": float(final_score),
                    "city": metadata.get("city", "Unknown"),
                    "price": float(metadata.get("price", 0)),
                    "bhk": int(metadata.get("bhk", 0)),
                    "vastu": bool(metadata.get("vastu", False) or (len(spatial_data.get("vastu_signals", [])) > 0)),
                    "location": metadata.get("location", ""),
                    "spatial_features": spatial_data
                }
                
                # STEP 6 — GENERATE UNIQUE ID
                # uuid5 is deterministic. Use namespace URL for consistency.
                point_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{listing_id}_{idx}_{img_path.name}"))
                
                # Qdrant accepts UUID strings. We use the deterministic UUID.
                # If int is strictly required:
                # point_id_int = int(hashlib.sha256(point_uuid.encode()).hexdigest(), 16) % (2**63)
                
                points_to_upsert.append({
                    "id": point_uuid,
                    "embedding": embedding,
                    "payload": payload
                })
                
                results_summary.append({
                    "image_path": str(img_path),
                    "room_type": room_type,
                    "grade": grade,
                    "indexed": True
                })
                
            except Exception as e:
                self.logger.warning(f"Failed to process {image_path}: {e}")
                failed.append(str(image_path))
                continue
                
        # BATCH UPSERT TO QDRANT
        if points_to_upsert:
            self.qdrant.upsert_batch(points_to_upsert)
            self.logger.info(f"Indexed {len(points_to_upsert)} vectors for {listing_id}")
        
        clear_gpu_cache()
        
        return {
            "listing_id": listing_id,
            "total_images": len(image_paths),
            "indexed": len(points_to_upsert),
            "failed": len(failed),
            "results": results_summary
        }

    def index_from_directory(self, listings_dir: str) -> Dict:
        """
        Index all property listings from a parent directory.
        Expects: listings_dir/listing_name/ {images + optional metadata.json}
        """
        target_dir = Path(listings_dir)
        if not target_dir.exists():
            self.logger.error(f"Directory not found: {listings_dir}")
            return {}
            
        listing_folders = sorted([d for d in target_dir.iterdir() if d.is_dir()])
        self.logger.info(f"Found {len(listing_folders)} potential listings in {listings_dir}")
        
        all_results = []
        total_indexed = 0
        
        for folder in tqdm(listing_folders, desc="Bulk Indexing"):
            listing_id = folder.name
            
            # Find all images
            image_extensions = (".jpg", ".jpeg", ".png", ".webp")
            image_paths = [p for p in folder.iterdir() if p.suffix.lower() in image_extensions]
            
            if not image_paths:
                self.logger.warning(f"No images found in {folder}, skipping...")
                continue
                
            # Load metadata
            metadata = {}
            metadata_file = folder / "metadata.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)
                except Exception as e:
                    self.logger.warning(f"Could not load metadata for {listing_id}: {e}")
            
            # Index listing
            result = self.index_listing(listing_id, image_paths, metadata)
            all_results.append(result)
            total_indexed += result["indexed"]
            
        self.logger.info(f"Directory indexing complete: {total_indexed} total vectors")
        
        stats = self.qdrant.get_collection_stats()
        self.logger.info(f"Qdrant collection stats: {stats}")
        
        return {
            "total_listings": len(listing_folders),
            "total_vectors": total_indexed,
            "collection_stats": stats,
            "results": all_results
        }
