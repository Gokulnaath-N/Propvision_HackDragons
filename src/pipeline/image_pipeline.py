import os
import json
import time
import redis
from pathlib import Path
from typing import List, Dict, Any, Callable
from src.enhancement.preprocessor import ImagePreprocessor
from src.enhancement.realesrgan import RealESRGANEnhancer
from src.enhancement.postprocessor import ImagePostprocessor
from src.enhancement.quality_gate import QualityGate
from src.agents.orchestrator import process_listing
from src.search.indexer import ListingIndexer
from src.utils.logger import get_logger
from dotenv import load_dotenv

load_dotenv()

logger = get_logger(__name__)


class PropertyPipeline:
    """
    Master pipeline that processes a complete property listing end to end. 
    Connects enhancement, agents, and indexing.
    Reports progress via Redis for frontend polling.
    """

    def __init__(self):
        logger.info("Initializing PropertyPipeline...")

        self.preprocessor = ImagePreprocessor()
        self.enhancer = RealESRGANEnhancer()
        self.postprocessor = ImagePostprocessor()
        self.quality_gate = QualityGate()
        self.indexer = ListingIndexer()

        self.redis_client = None
        try:
            self.redis_client = redis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379")
            )
            self.redis_client.ping()
            logger.info("Redis connected for status updates")
        except Exception as e:
            logger.warning(f"Redis not available - status updates disabled: {e}")
            self.redis_client = None

        logger.info("PropertyPipeline ready")

    def _update_status(self, job_id: str, status: str, progress: int,
                       stage: str, details: dict = None):
        """
        Push progress update to Redis. 
        Frontend polls this to show progress bar.
        """
        update = {
            "job_id": job_id,
            "status": status,
            "progress": progress,
            "stage": stage,
            "details": details or {},
            "timestamp": time.time()
        }

        if self.redis_client:
            try:
                self.redis_client.setex(
                    f"job_status:{job_id}",
                    86400,  # 24 hours expiry
                    json.dumps(update)
                )
            except Exception as e:
                logger.warning(f"Status update failed: {e}")

    def run(self, listing_id: str, raw_image_paths: List[str], metadata: dict) -> Dict:
        """
        Run complete pipeline for one listing.
        """
        start_time = time.time()
        logger.info(f"Pipeline starting for {listing_id}")
        logger.info(f"Images to process: {len(raw_image_paths)}")

        self._update_status(
            listing_id, "processing", 5,
            "starting", {"total_images": len(raw_image_paths)}
        )

        # STAGE 1 — ENHANCEMENT (progress 5 to 30)
        enhanced_paths = []
        failed_enhancement = []

        logger.info("Stage 1: Image Enhancement")
        self._update_status(listing_id, "processing", 10, "enhancing")

        for idx, raw_path in enumerate(raw_image_paths):
            try:
                preprocessed = self.preprocessor.preprocess_to_pil(raw_path)
                enhanced = self.enhancer.enhance(preprocessed)
                paths = self.postprocessor.postprocess(enhanced, listing_id, idx)

                gate_result = self.quality_gate.check(paths["hero"])

                if gate_result["passed"]:
                    enhanced_paths.append(paths["hero"])
                else:
                    logger.warning(f"Quality gate failed for {raw_path}")
                    enhanced_paths.append(str(raw_path))

            except Exception as e:
                logger.warning(f"Enhancement failed for {raw_path}: {e}")
                enhanced_paths.append(str(raw_path))
                failed_enhancement.append(str(raw_path))

            progress = 10 + int((idx + 1) / len(raw_image_paths) * 20)
            self._update_status(listing_id, "processing", progress, "enhancing",
                                {"enhanced": idx + 1, "total": len(raw_image_paths)})

        logger.info(f"Enhancement: {len(enhanced_paths)} processed")

        # STAGE 2 — AI AGENTS (progress 30 to 80)
        logger.info("Stage 2: AI Agent Pipeline")
        self._update_status(listing_id, "processing", 35, "classifying")

        try:
            agent_state = process_listing(
                listing_id=listing_id,
                image_paths=enhanced_paths,
                metadata=metadata
            )

            self._update_status(listing_id, "processing", 75, "synthesizing")

        except Exception as e:
            logger.error(f"Agent pipeline failed: {e}")
            agent_state = {
                "listing_id": listing_id,
                "room_classifications": [],
                "quality_scores": [],
                "clip_embeddings": [],
                "spatial_analyses": [],
                "hero_image": enhanced_paths[0] if enhanced_paths else None,
                "gallery_order": enhanced_paths,
                "overall_grade": "C",
                "listing_summary": f"Property in {metadata.get('city', '')}",
                "action_items": [],
                "processing_status": "partial",
                "error": str(e)
            }

        # STAGE 3 — QDRANT INDEXING (progress 80 to 95)
        logger.info("Stage 3: Indexing to Qdrant")
        self._update_status(listing_id, "processing", 82, "indexing")

        try:
            index_result = self.indexer.index_listing(
                listing_id=listing_id,
                image_paths=enhanced_paths,
                metadata=metadata,
                room_classifications=agent_state.get("room_classifications", []),
                clip_embeddings=agent_state.get("clip_embeddings", []),
                quality_scores=agent_state.get("quality_scores", [])
            )
            indexed_count = index_result.get("indexed", 0)
            logger.info(f"Indexed {indexed_count} vectors")

        except Exception as e:
            logger.error(f"Indexing failed: {e}")
            indexed_count = 0

        # STAGE 4 — FINALIZE (progress 95 to 100)
        elapsed = round(time.time() - start_time, 2)

        final_result = {
            "listing_id": listing_id,
            "status": "complete",
            "processing_time_seconds": elapsed,
            "total_images": len(raw_image_paths),
            "enhanced_images": len(enhanced_paths),
            "failed_enhancement": len(failed_enhancement),
            "indexed_vectors": indexed_count,
            "hero_image": agent_state.get("hero_image"),
            "gallery_order": agent_state.get("gallery_order", []),
            "overall_grade": agent_state.get("overall_grade"),
            "listing_summary": agent_state.get("listing_summary"),
            "room_classifications": agent_state.get("room_classifications", []),
            "action_items": agent_state.get("action_items", []),
            "metadata": metadata
        }

        self._update_status(
            listing_id, "complete", 100,
            "complete", final_result
        )

        logger.info(f"Pipeline complete for {listing_id} in {elapsed}s")
        return final_result
