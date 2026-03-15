
import sys
import yaml
import torch
from pathlib import Path
from PIL import Image
import numpy as np

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.data.dataloader import get_dataloaders

def create_mock_image(path):
    # Create a small 64x64 valid RGB image
    img_data = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
    img = Image.fromarray(img_data)
    img.save(path)

def test_dataloaders():
    print("--- Starting DataLoader Verification ---")
    
    # 1. Setup mock data and config
    mock_data_dir = Path("tests/mock_data_dl")
    mock_data_dir.mkdir(parents=True, exist_ok=True)
    
    for split in ["train", "val", "test"]:
        for cls in ["bathroom", "bedroom"]:
            (mock_data_dir / split / cls).mkdir(parents=True, exist_ok=True)
            for i in range(4): # 4 images per class per split
                create_mock_image(mock_data_dir / split / cls / f"img_{i}.jpg")
                
    mock_config = {
        'model': {'image_size': 224},
        'training': {
            'batch_size': 2,
            'num_workers': 0,
            'pin_memory': False
        },
        'paths': {
            'train_dir': str(mock_data_dir / "train"),
            'val_dir': str(mock_data_dir / "val"),
            'test_dir': str(mock_data_dir / "test")
        }
    }
    
    config_path = mock_data_dir / "test_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(mock_config, f)
        
    try:
        # 2. Test get_dataloaders
        train_loader, val_loader, test_loader = get_dataloaders(config_path)
        
        print("\nVerification Results:")
        print(f"Train batches: {len(train_loader)} (Expected 4 since batch_size=2, images=8)")
        print(f"Val batches:   {len(val_loader)} (Expected 4)")
        print(f"Test batches:  {len(test_loader)} (Expected 4)")
        
        # 3. Check a batch
        images, labels = next(iter(train_loader))
        print(f"Batch Image Shape: {images.shape} (Expected [2, 3, 224, 224])")
        print(f"Batch Labels: {labels}")
        
        assert images.shape == (2, 3, 224, 224), "Incorrect batch shape"
        assert len(train_loader) == 4, "Incorrect number of train batches"
        
        print("\n--- All DataLoader Verification Tests Passed ---")
        return True
    except Exception as e:
        print(f"\n--- DataLoader Verification Failed ---")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        import shutil
        if mock_data_dir.exists():
            shutil.rmtree(mock_data_dir)

if __name__ == "__main__":
    success = test_dataloaders()
    sys.exit(0 if success else 1)
