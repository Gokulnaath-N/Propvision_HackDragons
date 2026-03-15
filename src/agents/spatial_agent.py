from src.agents.state import ListingState
from src.vision.spatial_analyzer import SpatialAnalyzer
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SpatialAgent:
    """
    LangGraph node that runs Gemini spatial analysis on the top 8 images 
    of a listing. Updates the ListingState with spatial and Vastu insights.
    """

    def __init__(self):
        self.analyzer = SpatialAnalyzer()
        self.max_images_to_analyze = 8
        logger.info("SpatialAgent initialized")

    def analyze_images(self, state: ListingState) -> ListingState:
        """
        Filters images based on quality score, pairs them with predicted room types, 
        and extracts spatial/Vastu features up to a maximum number of images.
        """
        state["processing_status"] = "analyzing"

        image_paths = state.get("enhanced_image_paths") or \
                      state.get("raw_image_paths", [])

        if not image_paths:
            return state

        classifications = state.get("room_classifications", [])
        quality_scores = state.get("quality_scores", [])

        # Build quality lookup dict: image_path -> final_score
        quality_lookup = {}
        for score in quality_scores:
            path = score.get("image_path")
            final_grade = score.get("final_score", 50.0)
            quality_lookup[path] = final_grade

        # Sort image_paths by quality score descending
        sorted_paths = sorted(
            image_paths, 
            key=lambda path: quality_lookup.get(str(path), 0.0), 
            reverse=True
        )

        # Take strictly the first 8 high-quality images to save Gemini costs
        top_images = sorted_paths[:self.max_images_to_analyze]

        # Build class lookup: image_path -> room_type
        class_lookup = {
            c["image_path"]: c.get("room_type", "room") 
            for c in classifications
        }

        # Build image-room pairs
        pairs = [
            (path, class_lookup.get(str(path), "room")) 
            for path in top_images
        ]

        # Run spatial analysis
        analyses = self.analyzer.analyze_listing(pairs)
        state["spatial_analyses"] = analyses

        total_vastu = sum(len(a.get("vastu_signals", [])) for a in analyses)
        logger.info(
            f"Spatial analysis complete: {len(analyses)} images analyzed, "
            f"{total_vastu} Vastu signals found."
        )

        return state
