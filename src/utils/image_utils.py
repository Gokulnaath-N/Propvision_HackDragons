import os
from pathlib import Path
import cv2
import numpy as np
import torch
from PIL import Image

from src.utils.logger import get_logger
from src.utils.exceptions import ImageLoadError

logger = get_logger("image_utils")

def load_image(path) -> Image.Image:
    """Load image from path, convert to RGB, and raise error if missing/corrupt."""
    if not os.path.exists(path):
        raise ImageLoadError(f"File not found: {path}")
    
    try:
        img = Image.open(path).convert("RGB")
        img.verify()  # verify it's a valid image
        
        # We need to reopen because verify() closes the file.
        img = Image.open(path).convert("RGB")
        return img
    except Exception as e:
        raise ImageLoadError(f"Corrupted or invalid image at {path}: {str(e)}")

def get_image_info(path) -> dict:
    """Returns image metadata: width, height, file size (KB), aspect ratio, format."""
    try:
        with Image.open(path) as img:
            width, height = img.size
            fmt = img.format
            aspect_ratio = round(width / height, 2) if height > 0 else 0.0
            
        file_size_kb = os.path.getsize(path) / 1024.0
        
        return {
            "width": width,
            "height": height,
            "file_size_kb": round(file_size_kb, 2),
            "aspect_ratio": float(aspect_ratio),
            "format": fmt
        }
    except Exception as e:
        logger.error(f"Failed to get info for {path}: {e}")
        return {}

def pil_to_cv2(image: Image.Image) -> np.ndarray:
    """Convert RGB PIL Image to BGR numpy array."""
    # Convert PIL image to numpy array (which is RGB)
    rgb_array = np.array(image)
    # Convert RGB to BGR for OpenCV
    bgr_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
    return bgr_array

def cv2_to_pil(array: np.ndarray) -> Image.Image:
    """Convert BGR numpy array to RGB PIL Image."""
    # Convert BGR to RGB
    rgb_array = cv2.cvtColor(array, cv2.COLOR_BGR2RGB)
    # Convert numpy array to PIL Image
    return Image.fromarray(rgb_array)

def pil_to_tensor(image: Image.Image, normalize: bool = True) -> torch.Tensor:
    """Convert PIL Image to (3, H, W) tensor with optional ImageNet normalization."""
    # Convert to numpy array and scale to [0, 1]
    img_array = np.array(image, dtype=np.float32) / 255.0
    
    # HWC to CHW
    img_array = img_array.transpose((2, 0, 1))
    tensor = torch.from_numpy(img_array)

    if normalize:
        mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
        tensor = (tensor - mean) / std

    return tensor

def tensor_to_pil(tensor: torch.Tensor) -> Image.Image:
    """Reverse normalize then convert to PIL. Clamp values 0 to 1."""
    tensor = tensor.clone().detach().cpu()
    
    # Reverse normalize
    mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
    
    tensor = tensor * std + mean
    
    # Clamp values 0 to 1
    tensor = torch.clamp(tensor, 0.0, 1.0)
    
    # Convert CHW to HWC
    img_array = tensor.numpy().transpose((1, 2, 0))
    
    # Scale and convert to uint8
    img_array = (img_array * 255.0).astype(np.uint8)
    
    return Image.fromarray(img_array)

def calculate_sharpness(image_array: np.ndarray) -> float:
    """Calculate sharpness of a BGR numpy array using Laplacian variance."""
    gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    return float(variance)

def calculate_brightness(image_array: np.ndarray) -> float:
    """Calculate brightness of a BGR numpy array using mean pixel value (0-255)."""
    gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
    mean_val = np.mean(gray)
    return float(mean_val)

def save_webp(image: Image.Image, path: str, quality: int = 92) -> None:
    """Save PIL Image as WebP, creating directories if needed, and log file size."""
    file_path = Path(path)
    
    # Create parent directories if they don't exist
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save image 
    image.save(file_path, "WEBP", quality=quality)
    
    # Log saved file path and file size
    size_kb = os.path.getsize(file_path) / 1024.0
    logger.info(f"Saved WebP image to {file_path}. Size: {size_kb:.2f} KB")
