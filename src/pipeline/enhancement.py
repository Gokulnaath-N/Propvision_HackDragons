import os
import sys
import torch
import cv2
import numpy as np
from pathlib import Path
from PIL import Image

# Ensure local third_party libraries are in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BASI_SR_PATH = str(PROJECT_ROOT / "third_party" / "BasicSR")
REAL_ESRGAN_PATH = str(PROJECT_ROOT / "third_party" / "Real-ESRGAN")

if BASI_SR_PATH not in sys.path:
    sys.path.append(BASI_SR_PATH)
if REAL_ESRGAN_PATH not in sys.path:
    sys.path.append(REAL_ESRGAN_PATH)

try:
    from basicsr.archs.rrdbnet_arch import RRDBNet
    from realesrgan import RealESRGANer
    from gfpgan import GFPGANer
except ImportError as e:
    # This might happen if PYTHONPATH is not correctly set during import
    print(f"Warning: Could not import enhancement libraries: {e}")

from src.utils.logger import get_logger
from src.utils.gpu_utils import get_device

logger = get_logger(__name__)

class PropertyImageEnhancer:
    """
    Unified utility for upscaling and restoring property images
    using Real-ESRGAN (4x) and GFPGAN.
    """
    def __init__(self, use_gpu=True, upscale_factor=4):
        self.device = get_device() if use_gpu else torch.device('cpu')
        self.upscale_factor = upscale_factor
        
        # Paths for weights
        self.realesrgan_weights = PROJECT_ROOT / "third_party" / "Real-ESRGAN" / "weights" / "RealESRGAN_x4plus.pth"
        
        # GFPGAN weights usually handle themselves if URL is provided, 
        # but we'll specify the one we downloaded if possible.
        self.gfpgan_url = 'https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth'
        
        # Initialize Real-ESRGAN
        self._setup_realesrgan()
        
        # Initialize GFPGAN
        self._setup_gfpgan()
        
        logger.info(f"PropertyImageEnhancer initialized on {self.device}")

    def _setup_realesrgan(self):
        model = RRDBNet(
            num_in_ch=3, num_out_ch=3,
            num_feat=64, num_block=23, num_grow_ch=32, scale=4
        )
        
        self.upsampler = RealESRGANer(
            scale=4,
            model_path=str(self.realesrgan_weights),
            model=model,
            tile=400,
            tile_pad=10,
            pre_pad=0,
            half=True if 'cuda' in str(self.device).lower() else False
        )
        logger.info("Real-ESRGAN setup complete.")

    def _setup_gfpgan(self):
        # arch='clean', channel_multiplier=2 for GFPGANv1.3
        self.face_restorer = GFPGANer(
            model_path=self.gfpgan_url,
            upscale=self.upscale_factor,
            arch='clean',
            channel_multiplier=2,
            bg_upsampler=self.upsampler
        )
        logger.info("GFPGAN setup complete.")

    def enhance_image(self, input_path, output_path=None):
        """
        Enhance a single image: 4x upscaling + face restoration + artifact removal.
        """
        input_path = str(input_path)
        img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
        if img is None:
            raise ValueError(f"Could not read image at {input_path}")
            
        # Run enhancement (GFPGANer handles background upsampling via bg_upsampler)
        # Returns: (cropped_faces, restored_faces, restored_img)
        _, _, restored_img = self.face_restorer.enhance(
            img, 
            has_aligned=False, 
            only_center_face=False, 
            paste_back=True
        )
        
        if output_path:
            cv2.imwrite(str(output_path), restored_img)
            logger.info(f"Enhanced image saved to {output_path}")
            
        return restored_img

    def enhance_batch(self, input_paths, output_dir):
        """
        Enhance a list of images and save to output_dir.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        for path in input_paths:
            path = Path(path)
            out_path = output_dir / f"enhanced_{path.name}"
            try:
                self.enhance_image(path, out_path)
                results.append(out_path)
            except Exception as e:
                logger.error(f"Failed to enhance {path}: {e}")
                
        return results
