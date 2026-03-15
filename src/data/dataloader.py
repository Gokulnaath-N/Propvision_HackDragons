import yaml
from pathlib import Path
from torch.utils.data import DataLoader
from src.data.dataset import RoomDataset
from src.data.augmentation import get_train_transforms, get_val_transforms
from src.utils.logger import get_logger

logger = get_logger(__name__)

def get_dataloaders(config_path="configs/model_config.yaml"):
    """
    Create PyTorch DataLoaders for train, val, and test splits
    with correct augmentation and optimal loading settings.
    
    Returns:
        tuple: (train_loader, val_loader, test_loader)
    """
    # STEP 1 — LOAD CONFIG
    config_path = Path(config_path)
    if not config_path.exists():
        msg = f"Config file not found: {config_path}"
        logger.error(msg)
        raise FileNotFoundError(msg)
        
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error parsing config file: {e}")
        raise
        
    # Extract values
    try:
        image_size = config['model']['image_size']
        batch_size = config['training']['batch_size']
        num_workers = config['training']['num_workers']
        pin_memory = config['training']['pin_memory']
        train_dir = config['paths']['train_dir']
        val_dir = config['paths']['val_dir']
        test_dir = config['paths']['test_dir']
    except KeyError as e:
        logger.error(f"Missing key in config: {e}")
        raise KeyError(f"Missing required configuration key: {e}")

    # STEP 2 — CREATE TRANSFORMS
    train_transform = get_train_transforms(image_size)
    val_transform = get_val_transforms(image_size)

    # STEP 3 — CREATE DATASETS
    logger.info("Initializing datasets...")
    train_dataset = RoomDataset(train_dir, transform=train_transform)
    val_dataset = RoomDataset(val_dir, transform=val_transform)
    test_dataset = RoomDataset(test_dir, transform=val_transform)
    
    # VERIFY CONSISTENCY
    # Check all three datasets have same class names
    train_classes = train_dataset.get_class_names()
    val_classes = val_dataset.get_class_names()
    test_classes = test_dataset.get_class_names()
    
    if not (train_classes == val_classes == test_classes):
        msg = (
            f"Class mismatch between splits!\n"
            f"Train: {train_classes}\n"
            f"Val:   {val_classes}\n"
            f"Test:  {test_classes}"
        )
        logger.error(msg)
        raise ValueError(msg)

    # STEP 4 — CREATE DATALOADERS
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=pin_memory,
        drop_last=True
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
        drop_last=False
    )
    
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
        drop_last=False
    )

    # STEP 5 — LOG SUMMARY
    logger.info("DataLoaders created successfully")
    logger.info(f"Train: {len(train_dataset)} images | {len(train_loader)} batches")
    logger.info(f"Val:   {len(val_dataset)} images | {len(val_loader)} batches")
    logger.info(f"Test:  {len(test_dataset)} images | {len(test_loader)} batches")
    logger.info(f"Classes: {train_classes}")
    logger.info(f"Batch size: {batch_size} | Image size: {image_size}x{image_size}")

    # STEP 6 — RETURN
    return train_loader, val_loader, test_loader
