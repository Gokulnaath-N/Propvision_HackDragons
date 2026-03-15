from torchvision import transforms
from src.utils.logger import get_logger

logger = get_logger(__name__)

# CONSTANTS
# Standard ImageNet normalization values
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

def get_train_transforms(image_size=380) -> transforms.Compose:
    """
    Return augmentation transforms for training.
    Creates variations to prevent overfitting and improve robustness.
    """
    transform = transforms.Compose([
        # 1. Resize slightly larger than target
        transforms.Resize(image_size + 32),
        
        # 2. Random crop to exact target size
        transforms.RandomCrop(image_size),
        
        # 3. Random horizontal flip
        transforms.RandomHorizontalFlip(p=0.5),
        
        # 4. Slight rotation
        transforms.RandomRotation(degrees=8),
        
        # 5. Color jitter for lighting/white-balance simulation
        transforms.ColorJitter(
            brightness=0.3,
            contrast=0.3,
            saturation=0.2,
            hue=0.05
        ),
        
        # 6. Random grayscale (5%)
        transforms.RandomGrayscale(p=0.05),
        
        # 7. Convert to tensor
        transforms.ToTensor(),
        
        # 8. Normalize to ImageNet distribution
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
    ])
    
    logger.info(f"Train transforms created for image size {image_size}")
    return transform

def get_val_transforms(image_size=380) -> transforms.Compose:
    """
    Return minimal transforms for validation/testing.
    Ensures accurate and deterministic evaluation.
    """
    transform = transforms.Compose([
        # 1. Resize slightly larger
        transforms.Resize(image_size + 32),
        
        # 2. Center crop only — no randomness
        transforms.CenterCrop(image_size),
        
        # 3. Convert to tensor
        transforms.ToTensor(),
        
        # 4. Normalize to ImageNet distribution
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
    ])
    
    logger.info(f"Val/Test transforms created for image size {image_size}")
    return transform

def get_inference_transforms(image_size=380) -> transforms.Compose:
    """
    Return transforms for production inference.
    Identical to validation transforms.
    """
    transform = get_val_transforms(image_size)
    logger.info(f"Inference transforms created for image size {image_size}")
    return transform
