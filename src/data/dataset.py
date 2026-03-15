import os
import json
from pathlib import Path
from PIL import Image
import torch
from torch.utils.data import Dataset
from collections import Counter
from src.utils.logger import get_logger
from src.utils.exceptions import ImageLoadError

logger = get_logger(__name__)

class RoomDataset(Dataset):
    """
    PyTorch Dataset class that reads organized room image folders
    and returns image tensors with class labels for training.
    """
    def __init__(self, root_dir, transform=None):
        self.root_dir = Path(root_dir)
        self.transform = transform
        
        # LOAD CLASS NAMES
        # List all subdirectories in root_dir and sort alphabetically
        try:
            self.classes = sorted([d.name for d in os.scandir(self.root_dir) if d.is_dir()])
        except FileNotFoundError:
            logger.error(f"Root directory not found: {self.root_dir}")
            raise ValueError(f"Root directory {self.root_dir} does not exist.")
            
        self.class_to_idx = {class_name: i for i, class_name in enumerate(self.classes)}
        self.idx_to_class = {i: class_name for i, class_name in enumerate(self.classes)}
        
        # COLLECT ALL SAMPLES
        self.samples = []
        for class_name in self.classes:
            class_idx = self.class_to_idx[class_name]
            class_dir = self.root_dir / class_name
            
            # Support jpg, jpeg, png, webp
            for ext in ('*.jpg', '*.jpeg', '*.png', '*.webp'):
                for img_path in class_dir.glob(ext):
                    self.samples.append((str(img_path), class_idx))
                    
        if not self.samples:
            msg = f"No images found in {self.root_dir}. Ensure structure is root/class/image.ext"
            logger.error(msg)
            raise ValueError(msg)
            
        # LOG ON INIT
        num_images = len(self.samples)
        num_classes = len(self.classes)
        logger.info(f"Dataset loaded: {num_images} images across {num_classes} classes")
        logger.info(f"Classes: {self.classes}")
        
        # Log per-class counts using Counter
        counts = Counter([label for _, label in self.samples])
        for idx, count in counts.items():
            logger.info(f"  Class '{self.idx_to_class[idx]}': {count} images")

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx) -> tuple:
        image_path, label = self.samples[idx]
        
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as e:
            logger.error(f"Image Load Error: {image_path} | {e}")
            raise ImageLoadError(f"Could not load image at {image_path}: {e}")
            
        if self.transform:
            image = self.transform(image)
        else:
            # Fallback if no transform is provided (minimal tensor conversion)
            # Typically, transforms would handle normalization and ToTensor()
            from torchvision import transforms
            image = transforms.ToTensor()(image)
            
        return image, label

    def get_class_names(self) -> list:
        return self.classes

    def get_class_to_idx(self) -> dict:
        return self.class_to_idx

    def get_class_weights(self) -> torch.Tensor:
        """
        Handle class imbalance in loss function using inverse frequency.
        weight = total_samples / (num_classes * class_count)
        """
        counts = Counter([label for _, label in self.samples])
        total_samples = len(self.samples)
        num_classes = len(self.classes)
        
        weights = []
        for i in range(num_classes):
            class_count = counts.get(i, 0)
            if class_count > 0:
                weight = total_samples / (num_classes * class_count)
            else:
                weight = 0.0
            weights.append(weight)
            
        weight_tensor = torch.FloatTensor(weights)
        logger.info(f"Class weights calculated: {weights}")
        return weight_tensor

    def get_class_distribution(self) -> dict:
        """
        Return dict of class mappings sorted by count descending.
        """
        counts = Counter([label for _, label in self.samples])
        distribution = {}
        for idx, count in counts.items():
            distribution[self.idx_to_class[idx]] = count
            
        # Sort by count descending
        sorted_dist = dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True))
        return sorted_dist

    def get_sample_path(self, idx) -> str:
        """
        Return image path for given index.
        Used by evaluator for failure case analysis.
        """
        return self.samples[idx][0]
