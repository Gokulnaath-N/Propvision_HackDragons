import cv2
import numpy as np
from PIL import Image
from pathlib import Path
import os
from src.utils.logger import get_logger
from src.utils.exceptions import ImageQualityError

logger = get_logger(__name__)

class QualityGate:
    """
    Quality verification gate for enhanced images.
    Ensures only acceptable quality images proceed to
    storage and indexing. Flags failures for review.
    """
    def __init__(self):
        # QUALITY THRESHOLDS
        self.min_sharpness = 35.0  # Reduced from 50.0 to handle upscaled textures
        self.min_width = 1280      # Minimum hero width
        self.min_height = 720      # Minimum hero height
        self.min_brightness = 30   # Minimum mean pixel value
        self.max_brightness = 230  # Maximum mean pixel value
        self.min_file_size_kb = 20 # Reduced from 50KB for efficient WebP
        
        logger.info("QualityGate initialized")

    def check(self, image_path: str) -> dict:
        """
        Run all quality checks on enhanced image.
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found at {image_path}")
            
        try:
            # LOAD IMAGE
            # Load with PIL for resolution check
            pil_img = Image.open(path)
            width, height = pil_img.size
            
            # Convert PIL to BGR numpy for OpenCV operations
            bgr_array = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            
            # RUN ALL CHECKS
            sharpness = self._check_sharpness(bgr_array)
            res_passed = self._check_resolution(pil_img)
            brightness = self._check_brightness(bgr_array)
            file_size_kb = self._check_file_size(path)
            
            # DETERMINE PASS OR FAIL
            passed = True
            failures = []
            
            if sharpness < self.min_sharpness:
                passed = False
                failures.append(f"Too blurry: {sharpness:.1f} < {self.min_sharpness}")
                
            if not res_passed:
                passed = False
                failures.append(f"Too small: {width}x{height} (Min: {self.min_width}x{self.min_height})")
                
            if brightness < self.min_brightness:
                passed = False
                failures.append(f"Too dark: {brightness:.1f} (Min: {self.min_brightness})")
                
            if brightness > self.max_brightness:
                passed = False
                failures.append(f"Overexposed: {brightness:.1f} (Max: {self.max_brightness})")
                
            if file_size_kb < self.min_file_size_kb:
                passed = False
                failures.append(f"File too small: {file_size_kb:.1f}KB (Min: {self.min_file_size_kb}KB)")
                
            result = {
                "passed": passed,
                "sharpness_score": round(float(sharpness), 2),
                "brightness_score": round(float(brightness), 2),
                "resolution": (width, height),
                "file_size_kb": round(float(file_size_kb), 2),
                "failures": failures,
                "grade": "PASS" if passed else "FAIL"
            }
            
            if not passed:
                logger.warning(f"Quality check failed for {path.name}: {', '.join(failures)}")
            else:
                logger.info(f"Quality check passed for {path.name} (Sharpness: {sharpness:.1f})")
                
            return result
            
        except Exception as e:
            msg = f"Quality check failed for {image_path}: {e}"
            logger.error(msg)
            raise ImageQualityError(msg)

    def _check_sharpness(self, bgr_array: np.ndarray) -> float:
        """
        Measure image sharpness using Laplacian variance.
        Higher variance = many sharp edges = sharper image.
        """
        gray = cv2.cvtColor(bgr_array, cv2.COLOR_BGR2GRAY)
        # Apply Laplacian operator and return variance
        return cv2.Laplacian(gray, cv2.CV_64F).var()

    def _check_resolution(self, pil_image: Image.Image) -> bool:
        """
        Check if image meets minimum resolution requirements.
        """
        width, height = pil_image.size
        return width >= self.min_width and height >= self.min_height

    def _check_brightness(self, bgr_array: np.ndarray) -> float:
        """
        Check mean brightness of the image (0-255 grayscale).
        """
        gray = cv2.cvtColor(bgr_array, cv2.COLOR_BGR2GRAY)
        return float(np.mean(gray))

    def _check_file_size(self, image_path: Path) -> float:
        """
        Return file size in KB.
        """
        return os.path.getsize(image_path) / 1024.0

    def check_batch(self, image_paths: list) -> dict:
        """
        Run check() on all paths and return summary report.
        """
        results = []
        failed_paths = []
        
        logger.info(f"Starting batch quality check for {len(image_paths)} images...")
        
        for path in image_paths:
            try:
                res = self.check(path)
                results.append(res)
                if not res["passed"]:
                    failed_paths.append(str(path))
            except Exception as e:
                logger.error(f"Error checking {path}: {e}")
                
        total = len(results)
        passed_count = sum(1 for r in results if r["passed"])
        failed_count = total - passed_count
        
        summary = {
            "total": total,
            "passed": passed_count,
            "failed": failed_count,
            "pass_rate": (passed_count / total * 100) if total > 0 else 0,
            "failed_paths": failed_paths,
            "results": results
        }
        
        logger.info(f"Batch quality check complete: {passed_count}/{total} passed.")
        return summary
