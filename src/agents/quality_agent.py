from tqdm import tqdm
from src.agents.state import ListingState
from src.vision.quality_scorer import ImageQualityScorer
from src.utils.logger import get_logger

logger = get_logger(__name__)


class QualityAgent:
    """
    LangGraph node that scores all images for a listing using ImageQualityScorer.
    Updates the ListingState with visual ML heuristics.
    """

    def __init__(self):
        self.scorer = ImageQualityScorer()
        logger.info("QualityAgent initialized")

    def score_images(self, state: ListingState) -> ListingState:
        """
        Calculates sharpness, exposure, and overall grade for each image sequentially.
        """
        state["processing_status"] = "scoring"

        image_paths = state.get("enhanced_image_paths") or \
                      state.get("raw_image_paths", [])

        if not image_paths:
            return state

        quality_scores = []

        for image_path in tqdm(image_paths, desc="Scoring"):
            try:
                result = self.scorer.score(image_path)
                result["image_path"] = str(image_path)
                quality_scores.append(result)
            except Exception as e:
                logger.warning(f"Scoring failed for {image_path}: {e}")
                quality_scores.append({
                    "image_path": str(image_path),
                    "grade": "C",
                    "final_score": 50.0,
                    "sharpness_score": 50.0
                })

        state["quality_scores"] = quality_scores

        grades = [s.get("grade") for s in quality_scores]
        logger.info(f"Quality scoring complete. Grades: {grades}")
        
        return state
