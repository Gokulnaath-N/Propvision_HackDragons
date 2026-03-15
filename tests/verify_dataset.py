
import sys
import os
import torch
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.data.dataset import RoomDataset

def test_dataset():
    print("--- Starting Dataset Verification ---")
    
    # Use the existing train data directory if it exists, otherwise use a temp one
    data_dir = Path("data/processed/train")
    if not data_dir.exists():
        print(f"Directory {data_dir} not found. Creating a mock structure for testing...")
        data_dir = Path("tests/mock_data")
        for cls in ["bathroom", "bedroom", "kitchen"]:
            (data_dir / cls).mkdir(parents=True, exist_ok=True)
            # Create a dummy image file
            (data_dir / cls / "dummy.jpg").touch()
            
    try:
        # Initialize dataset (no transform for basic metadata check)
        dataset = RoomDataset(root_dir=data_dir)
        print(f"Dataset initialized successfully with {len(dataset)} images.")
        
        # Check class mapping
        classes = dataset.get_class_names()
        print(f"Classes found: {classes}")
        
        # Check distribution
        dist = dataset.get_class_distribution()
        print(f"Class distribution: {dist}")
        
        # Check weights
        weights = dataset.get_class_weights()
        print(f"Class weights: {weights}")
        
        # Check a sample
        if len(dataset) > 0:
            img, label = dataset[0]
            path = dataset.get_sample_path(0)
            print(f"Sample 0: Label={label} ({dataset.classes[label]}), Path={path}, Tensor Shape={img.shape}")
            
        print("\n--- All Dataset Verification Tests Passed ---")
        return True
    except Exception as e:
        print(f"\n--- Dataset Verification Failed ---")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_dataset()
    # Cleanup mock data if created
    if Path("tests/mock_data").exists():
        import shutil
        shutil.rmtree("tests/mock_data")
        
    sys.exit(0 if success else 1)
