import cv2
import numpy as np
from PIL import Image
from pathlib import Path
import os
import time
from src.utils.logger import get_logger
from src.utils.exceptions import ImageEnhancementError

logger = get_logger(__name__)

class ImagePostprocessor:
    """
    Post-process Real-ESRGAN output for web delivery.
    Handles smart crop, aspect ratio, resizing, and 
    generating three size variants per image (Hero, Gallery, Thumbnail).
    """
    def __init__(self):
        # Output sizes (width, height)
        self.hero_size = (1920, 1080)        # Full res for detail page
        self.gallery_size = (1280, 720)      # Medium res for gallery
        self.thumbnail_size = (400, 300)      # Small for card preview
        
        self.output_quality = 92
        self.output_base = Path("data/enhanced")
        
        logger.info("ImagePostprocessor initialized")

    def postprocess(self, enhanced_image: Image.Image, listing_id: str, image_idx: int) -> dict:
        """
        Full post-processing for one enhanced image.
        Returns paths and metadata for all generated variants.
        """
        start_time = time.time()
        
        try:
            # STEP 1 — SMART CROP
            # Remove black borders sometimes produced by tilt correction
            cropped = self._remove_black_borders(enhanced_image)
            
            # STEP 2 — CREATE OUTPUT DIRECTORY
            output_dir = self.output_base / listing_id
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # STEP 3-5 — GENERATE VARIANTS
            results = {
                "listing_id": listing_id,
                "image_idx": image_idx
            }
            
            # HERO (16:9 padded)
            hero_path = output_dir / f"hero_{image_idx:03d}.webp"
            hero_img = self._resize_and_pad(cropped, self.hero_size)
            hero_size_kb = self.save_webp(hero_img, hero_path)
            results["hero"] = str(hero_path)
            results["hero_size_kb"] = hero_size_kb
            
            # GALLERY (16:9 padded)
            gallery_path = output_dir / f"gallery_{image_idx:03d}.webp"
            gallery_img = self._resize_and_pad(cropped, self.gallery_size)
            self.save_webp(gallery_img, gallery_path)
            results["gallery"] = str(gallery_path)
            
            # THUMBNAIL (Smart Crop)
            thumb_path = output_dir / f"thumb_{image_idx:03d}.webp"
            thumb_img = self._smart_thumbnail(cropped, self.thumbnail_size)
            self.save_webp(thumb_img, thumb_path)
            results["thumbnail"] = str(thumb_path)
            
            duration = time.time() - start_time
            logger.info(f"Post-processing complete for {listing_id}_{image_idx:03d} in {duration:.2f}s")
            logger.info(f"Hero size: {hero_size_kb:.1f} KB")
            
            return results
            
        except Exception as e:
            msg = f"Post-processing failed for {listing_id} idx {image_idx}: {e}"
            logger.error(msg)
            raise ImageEnhancementError(msg)

    def _remove_black_borders(self, image: Image.Image) -> Image.Image:
        """
        Remove thin black lines at edges produced by tilt correction.
        """
        # Convert to numpy for analysis
        img_np = np.array(image)
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        
        # Pixels below threshold 15 are considered black
        threshold = 15
        mask = gray > threshold
        
        # Find the bounding box of non-black content
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)
        
        if not np.any(rows) or not np.any(cols):
            return image # Fallback if image is all dark
            
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]
        
        # Add 5 pixel safety padding to avoid over-trimming
        pad = 5
        h, w = gray.shape
        rmin = max(0, rmin + pad)
        rmax = min(h, rmax - pad)
        cmin = max(0, cmin + pad)
        cmax = min(w, cmax - pad)
        
        # If the padded crop is still valid, crop it
        if rmax > rmin and cmax > cmin:
            return image.crop((cmin, rmin, cmax, rmax))
            
        return image

    def _resize_and_pad(self, image: Image.Image, target_size: tuple) -> Image.Image:
        """
        Resize image keeping aspect ratio, then pad with black to reach exact target size.
        Ensures a consistent aspect ratio (e.g. 16:9) without stretching.
        """
        target_w, target_h = target_size
        
        # Calculate scale factor to fit within target
        scale_w = target_w / image.width
        scale_h = target_h / image.height
        scale = min(scale_w, scale_h)
        
        new_w = int(image.width * scale)
        new_h = int(image.height * scale)
        
        # Resize with high-quality filter
        resized = image.resize((new_w, new_h), Image.LANCZOS)
        
        # Create black canvas
        canvas = Image.new("RGB", (target_w, target_h), (0, 0, 0))
        
        # Paste centered
        x_offset = (target_w - new_w) // 2
        y_offset = (target_h - new_h) // 2
        canvas.paste(resized, (x_offset, y_offset))
        
        return canvas

    def _smart_thumbnail(self, image: Image.Image, target_size: tuple) -> Image.Image:
        """
        Resize for thumbnails by center-cropping to target aspect ratio first.
        Ensures the thumbnail is filled without black bars.
        """
        target_w, target_h = target_size
        target_ratio = target_w / target_h
        image_ratio = image.width / image.height
        
        if image_ratio > target_ratio:
            # Image is wider than target
            new_w = int(image.height * target_ratio)
            offset = (image.width - new_w) // 2
            cropped = image.crop((offset, 0, offset + new_w, image.height))
        else:
            # Image is taller than target
            new_h = int(image.width / target_ratio)
            offset = (image.height - new_h) // 2
            cropped = image.crop((0, offset, image.width, offset + new_h))
            
        return cropped.resize(target_size, Image.LANCZOS)

    def save_webp(self, image: Image.Image, path: Path, quality: int = None) -> float:
        """
        Save PIL image as WebP and return file size in KB.
        """
        if quality is None:
            quality = self.output_quality
            
        # Ensure path is a Path object
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        image.save(str(path), format='WEBP', quality=quality)
        
        # Return size in KB
        return os.path.getsize(path) / 1024
