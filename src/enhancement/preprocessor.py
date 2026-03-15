import cv2
import numpy as np
import time
from pathlib import Path
from PIL import Image
from src.utils.logger import get_logger
from src.utils.exceptions import ImageLoadError, ImageEnhancementError

logger = get_logger(__name__)

class ImagePreprocessor:
    """
    Pre-process raw property images before Real-ESRGAN enhancement.
    Fixes darkness, noise, and tilt so induction models get clean input.
    """
    def __init__(self):
        # Configuration parameters
        self.min_brightness = 60
        self.clahe_clip_limit = 2.0
        self.clahe_tile_grid = (8, 8)
        
        # Bilateral filter parameters
        self.bilateral_d = 9
        self.bilateral_sigma_color = 75
        self.bilateral_sigma_space = 75
        
        # Tilt correction threshold
        self.tilt_threshold_degrees = 3.0
        
        logger.info("ImagePreprocessor initialized")

    def preprocess(self, image_path: str) -> np.ndarray:
        """
        Full preprocessing pipeline for one image.
        Returns: BGR numpy array
        """
        start_time = time.time()
        image_path_str = str(image_path)
        
        try:
            # STEP 1 — LOAD IMAGE
            img = cv2.imread(image_path_str)
            if img is None:
                raise ImageLoadError(f"Failed to load image at {image_path_str}")
            
            h, w = img.shape[:2]
            logger.info(f"Processing image: {image_path_str} ({w}x{h})")
            
            # STEP 2 — CHECK AND FIX BRIGHTNESS
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            mean_brightness = np.mean(gray)
            
            if mean_brightness < self.min_brightness:
                logger.info(f"Dark image detected (mean={mean_brightness:.1f}), applying CLAHE")
                # Convert BGR to LAB color space
                lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
                l_channel, a, b = cv2.split(lab)
                
                # Apply CLAHE to L channel
                clahe = cv2.createCLAHE(
                    clipLimit=self.clahe_clip_limit,
                    tileGridSize=self.clahe_tile_grid
                )
                l_enhanced = clahe.apply(l_channel)
                
                # Merge back
                lab_enhanced = cv2.merge((l_enhanced, a, b))
                img = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
                logger.info("Brightness enhanced using CLAHE in LAB space")
            
            # STEP 3 — DENOISE
            # Always apply bilateral filter to smooth textures while keeping edges sharp
            img = cv2.bilateralFilter(
                img,
                d=self.bilateral_d,
                sigmaColor=self.bilateral_sigma_color,
                sigmaSpace=self.bilateral_sigma_space
            )
            logger.info("Noise reduction (Bilateral Filter) applied")
            
            # STEP 4 — DETECT AND CORRECT TILT
            tilt_angle = self._detect_tilt(img)
            if abs(tilt_angle) > self.tilt_threshold_degrees:
                img = self._correct_tilt(img, tilt_angle)
                logger.info(f"Tilt corrected: {tilt_angle:.1f} degrees")
            else:
                logger.info(f"No significant tilt detected ({tilt_angle:.1f} degrees)")
            
            duration = time.time() - start_time
            logger.info(f"Preprocessing completed in {duration:.3f}s")
            
            return img
            
        except Exception as e:
            if isinstance(e, ImageLoadError):
                raise
            msg = f"Preprocessing failed for {image_path_str}: {str(e)}"
            logger.error(msg)
            raise ImageEnhancementError(msg)

    def _detect_tilt(self, image: np.ndarray) -> float:
        """
        Detect image tilt angle using Hough lines.
        Focuses on horizontal dominant lines.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Apply Canny edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Detect lines using Probabilistic Hough Transform
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi/180,
            threshold=100,
            minLineLength=100,
            maxLineGap=10
        )
        
        if lines is None:
            return 0.0
            
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            # Calculate angle in degrees
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            
            # Focus on horizontal-ish lines (-45 to 45 degrees)
            if -45 < angle < 45:
                angles.append(angle)
        
        if not angles:
            return 0.0
            
        # Use median to avoid outliers
        return float(np.median(angles))

    def _correct_tilt(self, image: np.ndarray, angle: float) -> np.ndarray:
        """
        Rotate image to correct detected tilt.
        Uses BORDER_REFLECT_101 to avoid black borders.
        """
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        
        # Get rotation matrix (rotate in opposite direction to tilt)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Apply warpAffine with reflection padding for a seamless look
        corrected = cv2.warpAffine(
            image, 
            matrix, 
            (w, h), 
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REFLECT_101
        )
        
        return corrected

    def preprocess_to_pil(self, image_path: str) -> Image.Image:
        """
        Convenience method to get preprocessed image as PIL RGB.
        """
        bgr_img = self.preprocess(image_path)
        rgb_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb_img)
