import cv2
import numpy as np
import torch
import sys
import time
from pathlib import Path
from PIL import Image
from tqdm import tqdm

# Ensure local third_party libraries are in path
SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parent.parent.parent

BASI_SR_PATH = str(PROJECT_ROOT / "third_party" / "BasicSR")
REAL_ESRGAN_PATH = str(PROJECT_ROOT / "third_party" / "Real-ESRGAN")

if BASI_SR_PATH not in sys.path:
    sys.path.insert(0, BASI_SR_PATH)
if REAL_ESRGAN_PATH not in sys.path:
    sys.path.insert(0, REAL_ESRGAN_PATH)

from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

from src.utils.logger import get_logger
from src.utils.gpu_utils import get_device, clear_gpu_cache
from src.utils.exceptions import ImageEnhancementError

class RealESRGANEnhancer:
    """
    AI-powered image super-resolution using Real-ESRGAN.
    Turns blurry low-quality property photos into sharp 
    professional-quality images using 4x upscaling.
    """
    def __init__(self):
        self.device = get_device()
        self.scale = 4
        self.logger = get_logger(__name__)
        self.upsampler = None
        self._load_model()

    def _load_model(self):
        """
        Load Real-ESRGAN model onto GPU/CPU.
        """
        self.logger.info("Initializing Real-ESRGAN model...")
        
        try:
            # DEFINE MODEL ARCHITECTURE (standard RRDBNet for x4plus)
            model = RRDBNet(
                num_in_ch=3, 
                num_out_ch=3, 
                num_feat=64, 
                num_block=23, 
                num_grow_ch=32, 
                scale=4
            )
            
            # MODEL WEIGHTS
            # We use the official URL; RealESRGANer handles caching in its weights directoy
            model_url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
            
            # Use FP16 (half precision) for significant speedup on RTX 4050
            is_cuda = (self.device.type == 'cuda')
            
            self.upsampler = RealESRGANer(
                scale=4,
                model_path=model_url,
                model=model,
                tile=400,          # Tiled processing to prevent OOM
                tile_pad=10,
                pre_pad=0,
                half=is_cuda,      # FP16 enabled on GPU
                gpu_id=0 if is_cuda else None
            )
            
            device_name = torch.cuda.get_device_name(0) if is_cuda else "CPU"
            self.logger.info(f"Real-ESRGAN loaded on {device_name} " + 
                              ("(Half-Precision enabled)" if is_cuda else "(Full Precision)"))
            
        except Exception as e:
            msg = f"Failed to load Real-ESRGAN model: {e}"
            self.logger.error(msg)
            raise ImageEnhancementError(msg)

    def enhance(self, image_input) -> Image.Image:
        """
        Enhance a single image using Real-ESRGAN.
        Accepts: str (path), Path, PIL.Image, or np.ndarray (BGR).
        """
        start_time = time.time()
        
        # ACCEPT BOTH INPUT TYPES
        if isinstance(image_input, (str, Path)):
            bgr_array = cv2.imread(str(image_input))
            if bgr_array is None:
                raise ImageEnhancementError(f"File not found or unreadable: {image_input}")
        elif isinstance(image_input, Image.Image):
            # Convert PIL to BGR numpy
            bgr_array = cv2.cvtColor(np.array(image_input), cv2.COLOR_RGB2BGR)
        elif isinstance(image_input, np.ndarray):
            bgr_array = image_input  # Assume BGR
        else:
            raise ImageEnhancementError(f"Unsupported input type: {type(image_input)}")

        h, w = bgr_array.shape[:2]
        
        try:
            # Run enhancement
            output_array, _ = self.upsampler.enhance(
                bgr_array, 
                outscale=4
            )
            
            # Convert output BGR numpy to RGB PIL Image
            output_pil = Image.fromarray(cv2.cvtColor(output_array, cv2.COLOR_BGR2RGB))
            
            duration = time.time() - start_time
            out_h, out_w = output_array.shape[:2]
            self.logger.info(f"Enhancement complete: {w}x{h} -> {out_w}x{out_h} in {duration:.2f}s")
            
            return output_pil
            
        except RuntimeError as e:
            if "CUDA out of memory" in str(e):
                self.logger.warning("CUDA Out of Memory caught. Retrying on CPU...")
                # Clear cache and re-init on CPU as fallback
                clear_gpu_cache()
                self.device = torch.device('cpu')
                self._load_model()
                return self.enhance(image_input) # Recursive retry
            else:
                msg = f"Inference failed: {e}"
                self.logger.error(msg)
                raise ImageEnhancementError(msg)
        except Exception as e:
            msg = f"Unexpected enhancement error: {e}"
            self.logger.error(msg)
            raise ImageEnhancementError(msg)

    def enhance_batch(self, image_inputs, desc="Enhancing") -> list:
        """
        Enhance multiple images with progress bar.
        Returns list of PIL Images (or None if failed).
        """
        results = []
        failed_count = 0
        
        self.logger.info(f"Starting batch enhancement for {len(image_inputs)} images...")
        
        for image_input in tqdm(image_inputs, desc=desc):
            try:
                enhanced = self.enhance(image_input)
                results.append(enhanced)
            except ImageEnhancementError as e:
                self.logger.warning(f"Enhancement failed for image {image_input}: {e}")
                results.append(None)
                failed_count += 1
        
        self.logger.info(f"Batch complete. Success: {len(results)-failed_count}, Failed: {failed_count}")
        return results

    def is_loaded(self) -> bool:
        return self.upsampler is not None

    def get_info(self) -> dict:
        return {
            "model_name": "RealESRGAN_x4plus",
            "scale": 4,
            "device": str(self.device),
            "tile_size": 400,
            "half_precision": True if self.device.type == 'cuda' else False
        }
