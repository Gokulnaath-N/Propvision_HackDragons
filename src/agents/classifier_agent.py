import os
from pathlib import Path
from tqdm import tqdm
from src.agents.state import ListingState
from src.models.predictor import RoomPredictor
from src.vision.clip_embedder import CLIPEmbedder
from src.utils.logger import get_logger
from src.utils.gpu_utils import clear_gpu_cache

logger = get_logger(__name__)


class ClassifierAgent:
    """
    LangGraph nodes for room classification and CLIP embedding.
    Wraps trained EfficientNet-B4 and CLIP models as pipeline stages.
    """

    def __init__(self):
        self.predictor = RoomPredictor()
        self.clip = CLIPEmbedder()
        self.confidence_threshold = 0.60
        self.hero_priority_rooms = [
            "hall", "bedroom", "kitchen",
            "bathroom", "pooja_room", "balcony"
        ]
        logger.info("ClassifierAgent initialized")

    def classify_rooms(self, state: ListingState) -> ListingState:
        """
        LangGraph node — classify all images.
        """
        state["processing_status"] = "classifying"
        image_paths = state.get("enhanced_image_paths") or \
                      state.get("raw_image_paths", [])

        if not image_paths:
            state["error"] = "No images to classify"
            return state

        classifications = []

        for image_path in tqdm(image_paths, desc="Classifying"):
            try:
                result = self.predictor.predict(image_path)
                
                if result["confidence"] < self.confidence_threshold:
                    room_type = "unknown"
                else:
                    room_type = result["predicted_class"]

                classifications.append({
                    "image_path": str(image_path),
                    "room_type": room_type,
                    "confidence": result["confidence"],
                    "all_probabilities": result["all_probabilities"]
                })

            except Exception as e:
                logger.warning(f"Classification failed for {image_path}: {e}")
                classifications.append({
                    "image_path": str(image_path),
                    "room_type": "unknown",
                    "confidence": 0.0,
                    "all_probabilities": {}
                })

        state["room_classifications"] = classifications

        # Determine hero image
        hero = self._select_hero_image(
            classifications,
            state.get("quality_scores", [])
        )
        state["hero_image"] = hero

        # Determine gallery order
        ordered = self._order_gallery(classifications)
        state["gallery_order"] = ordered

        logger.info(f"Classified {len(classifications)} images")
        logger.info(f"Hero image: {state.get('hero_image')}")

        clear_gpu_cache()
        return state

    def embed_images(self, state: ListingState) -> ListingState:
        """
        LangGraph node — generate CLIP embeddings.
        """
        state["processing_status"] = "embedding"
        image_paths = state.get("enhanced_image_paths") or \
                      state.get("raw_image_paths", [])

        if not image_paths:
            return state

        embeddings = []
        batch_size = 16

        # Batch embed all images
        for i in range(0, len(image_paths), batch_size):
            batch = image_paths[i:i+batch_size]
            try:
                batch_embeddings = self.clip.embed_images_batch(batch)
                
                for j, emb in enumerate(batch_embeddings):
                    if emb is not None:
                        embeddings.append({
                            "image_path": str(batch[j]),
                            "embedding": emb.tolist()
                        })
                    else:
                        logger.warning(f"Embedding failed for {batch[j]}")
            except Exception as e:
                logger.error(f"Batch embedding failed: {e}")

        state["clip_embeddings"] = embeddings
        logger.info(f"Generated {len(embeddings)} CLIP embeddings")

        clear_gpu_cache()
        return state

    def _select_hero_image(self, classifications: list, quality_scores: list) -> str:
        """
        Pick best image for listing card display based on priority rooms and quality.
        """
        if not classifications:
            return None

        # Build quality lookup: image_path -> grade value
        grade_values = {"A+": 6, "A": 5, "B+": 4, "B": 3, "C": 2, "D": 1}
        quality_map = {}
        for score in quality_scores:
            path = score.get("image_path")
            grade = score.get("grade", "D")
            quality_map[path] = grade_values.get(grade, 1)

        # 1. Search by priority room
        for room in self.hero_priority_rooms:
            candidates = [c for c in classifications if c["room_type"] == room]
            if candidates:
                # Find the one with highest quality grade
                best_candidate = max(
                    candidates,
                    key=lambda c: quality_map.get(c["image_path"], 1)
                )
                return best_candidate["image_path"]

        # 2. If no priority room found, return highest quality image overall
        best_overall = max(
            classifications,
            key=lambda c: quality_map.get(c["image_path"], 1)
        )
        return best_overall["image_path"]

    def _order_gallery(self, classifications: list) -> list:
        """
        Order images for gallery display.
        Preferred order: hall -> kitchen -> bedroom -> bathroom -> pooja_room -> dining_room -> balcony -> exterior -> study -> unknown
        """
        order_weights = {
            "hall": 1,
            "kitchen": 2,
            "bedroom": 3,
            "bathroom": 4,
            "pooja_room": 5,
            "dining_room": 6,
            "balcony": 7,
            "exterior": 8,
            "study": 9,
            "unknown": 10
        }

        # Sort based on order weights, defaulting unknown types to 10
        sorted_classifications = sorted(
            classifications,
            key=lambda c: order_weights.get(c["room_type"], 10)
        )

        return [c["image_path"] for c in sorted_classifications]
