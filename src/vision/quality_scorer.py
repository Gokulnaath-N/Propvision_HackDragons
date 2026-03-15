import cv2
import numpy as np
from PIL import Image
from pathlib import Path
import math
from src.utils.logger import get_logger
from src.utils.exceptions import ImageLoadError
from tqdm import tqdm

class ImageQualityScorer:
    """
    Score property images on 5 quality dimensions using
    OpenCV computer vision metrics. Output grade A+ to D
    used for search ranking and broker feedback.
    """
    def __init__(self):
        # SCORING WEIGHTS must sum to 1.0
        self.weights = {
            "sharpness":   0.35,
            "lighting":    0.30,
            "resolution":  0.20,
            "saturation":  0.10,
            "noise":       0.05
        }
        
        # GRADE THRESHOLDS (normalized to 0-100)
        self.grades = {
            "A+": 90,
            "A":  80,
            "B+": 70,
            "B":  60,
            "C":  50
        }
        
        self.logger = get_logger(__name__)
        self.logger.info("ImageQualityScorer initialized")
        self.logger.info(f"Weights: {self.weights}")

    def score(self, image_input) -> dict:
        """
        Score single image across all dimensions.
        Accepts: str (path), Path, PIL.Image, or np.ndarray (BGR).
        """
        try:
            # LOAD IMAGE
            if isinstance(image_input, (str, Path)):
                bgr = cv2.imread(str(image_input))
                if bgr is None:
                    raise ImageLoadError(f"Failed to load image from path: {image_input}")
                pil_img = Image.open(str(image_input)).convert("RGB")
            elif isinstance(image_input, Image.Image):
                pil_img = image_input.convert("RGB")
                bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            elif isinstance(image_input, np.ndarray):
                bgr = image_input
                pil_img = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
            else:
                raise ImageLoadError(f"Unsupported input type: {type(image_input)}")

            # CALCULATE ALL 5 SCORES (0-100 each)
            sharpness_score  = self._score_sharpness(bgr)
            lighting_score   = self._score_lighting(bgr)
            resolution_score = self._score_resolution(pil_img)
            saturation_score = self._score_saturation(bgr)
            noise_score      = self._score_noise(bgr)
            
            # CALCULATE WEIGHTED TOTAL
            weighted = (
                sharpness_score  * self.weights["sharpness"]  +
                lighting_score   * self.weights["lighting"]   +
                resolution_score * self.weights["resolution"] +
                saturation_score * self.weights["saturation"] +
                noise_score      * self.weights["noise"]
            )
            final_score = round(weighted, 2)
            
            # ASSIGN GRADE
            grade = "D"
            for label, threshold in sorted(self.grades.items(), key=lambda x: x[1], reverse=True):
                if final_score >= threshold:
                    grade = label
                    break
            
            width, height = pil_img.size
            
            return {
                "sharpness_score": float(round(sharpness_score, 2)),
                "lighting_score": float(round(lighting_score, 2)),
                "resolution_score": float(round(resolution_score, 2)),
                "saturation_score": float(round(saturation_score, 2)),
                "noise_score": float(round(noise_score, 2)),
                "final_score": final_score,
                "grade": grade,
                "width": width,
                "height": height
            }
            
        except Exception as e:
            self.logger.error(f"Scoring failed: {e}")
            if isinstance(e, ImageLoadError):
                raise
            raise ImageLoadError(f"Error during image processing: {e}")

    def _score_sharpness(self, bgr) -> float:
        """
        Calculate sharpness using Laplacian variance.
        Normalized to 0-100 using log scale.
        """
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        
        # NORMALIZE TO 0-100
        # Use logarithmic scale because range is huge (0 to 10k+)
        # We target variance around 1000 as a very sharp image
        if variance < 10:
            return float(max(0, variance * 3))
            
        # Log scale: log(1001) is ~6.9, log(10) is 2.3
        score = (math.log(variance + 1) / math.log(1000)) * 100
        return float(min(100.0, score))

    def _score_lighting(self, bgr) -> float:
        """
        Score lighting based on mean brightness.
        Ideal range: 80-180.
        """
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        mean_brightness = gray.mean()
        
        # PENALIZE EXTREMES
        if 80 <= mean_brightness <= 180:
            score = 100.0
        elif mean_brightness < 80:
            # Linear drop to 0
            score = (mean_brightness / 80) * 100
        else: # mean > 180
            # Faster drop for overexposure
            score = 100.0 - (mean_brightness - 180) * 2
            
        return float(min(100.0, max(0.0, score)))

    def _score_resolution(self, pil_img) -> float:
        """
        Score based on megapixel count.
        2MP+ = 100, 1MP = 80, 0.5MP = 60, etc.
        """
        width, height = pil_img.size
        megapixels = (width * height) / 1_000_000
        
        if megapixels >= 2.0: # 1920x1080 is ~2MP
            return 100.0
        elif megapixels >= 1.0: # 1280x720 is ~0.9MP
            return 80.0
        elif megapixels >= 0.5:
            return 60.0
        elif megapixels >= 0.3: # 640x480 is ~0.3MP
            return 40.0
        else:
            return 20.0

    def _score_saturation(self, bgr) -> float:
        """
        Score based on HSV saturation mean.
        Prevents dull/grey photos.
        """
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        mean_saturation = hsv[:,:,1].mean()
        
        # Mean saturation is 0-255
        # Ideal range for property: 60-180
        if mean_saturation < 30:
            score = 20.0
        elif 30 <= mean_saturation < 60:
            score = 20.0 + (mean_saturation - 30) * 2.66 # Scale up to 100
        elif 60 <= mean_saturation <= 180:
            score = 100.0
        else: # mean > 180 (oversaturated)
            score = max(50.0, 100.0 - (mean_saturation - 180))
            
        return float(min(100.0, max(0.0, score)))

    def _score_noise(self, bgr) -> float:
        """
        Estimate noise by comparing image to its blurred version.
        """
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3,3), 0)
        noise = cv2.absdiff(gray, blurred)
        noise_level = noise.mean()
        
        # Lower noise = higher score
        if noise_level < 3.0:
            return 100.0
        elif noise_level < 6.0:
            return 85.0
        elif noise_level < 10.0:
            return 70.0
        elif noise_level < 15.0:
            return 50.0
        else:
            return 30.0

    def score_batch(self, image_inputs, desc="Scoring") -> list:
        """
        Score multiple images with progress bar.
        """
        results = []
        for img in tqdm(image_inputs, desc=desc):
            try:
                results.append(self.score(img))
            except Exception as e:
                self.logger.warning(f"Failed to score {img}: {e}")
                results.append(None)
        return results

    def get_listing_grade(self, image_scores: list) -> str:
        """
        Calculate overall grade for a listing based on multiple images.
        """
        valid_scores = [s["final_score"] for s in image_scores if s and "final_score" in s]
        if not valid_scores:
            return "D"
            
        mean_score = sum(valid_scores) / len(valid_scores)
        
        grade = "D"
        for label, threshold in sorted(self.grades.items(), key=lambda x: x[1], reverse=True):
            if mean_score >= threshold:
                grade = label
                break
        return grade
