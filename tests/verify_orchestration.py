
import sys
from unittest.mock import MagicMock

# --- CRITICAL: Mock matplotlib and seaborn BEFORE any imports ---
mock_plt = MagicMock()
mock_sns = MagicMock()
sys.modules['matplotlib'] = MagicMock()
sys.modules['matplotlib.pyplot'] = mock_plt
sys.modules['seaborn'] = mock_sns

import os
import torch
import yaml
import json
from pathlib import Path
from unittest.mock import patch

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

def test_orchestration():
    print("--- Starting Orchestration Verification (Dry Run) ---")
    
    # 1. Setup mock data loaders
    mock_dataset = MagicMock()
    mock_dataset.get_class_names.return_value = ["Living Room", "Bedroom", "Kitchen", "Bathroom", "Hall", "Dining Room"]
    mock_dataset.__len__.return_value = 100
    
    # Mock labels for dummy dataset
    mock_dataset.labels = [0] * 100
    
    # Create a batch
    batch_images = torch.randn(4, 3, 224, 224)
    batch_labels = torch.zeros(4, dtype=torch.long)
    
    mock_loader = MagicMock()
    mock_loader.dataset = mock_dataset
    mock_loader.__len__.return_value = 25 # 100 / 4
    mock_loader.__iter__.return_value = iter([(batch_images, batch_labels)] * 5) # 5 batches
    
    # 2. Setup mock config
    mock_config = {
        'model': {'dropout': 0.3, 'pretrained': False, 'image_size': 380},
        'training': {'epochs': 1},
        'paths': {
            'best_model_path': 'tests/checkpoints/best_model.pth',
            'class_labels_path': 'tests/checkpoints/class_labels.json'
        },
        'scheduler': {'name': 'cosine_annealing', 'T_max': 1, 'eta_min': 1e-6}
    }
    
    # 3. Mocks for external dependencies
    with patch('src.data.dataloader.get_dataloaders', return_value=(mock_loader, mock_loader, mock_loader)), \
         patch('src.models.trainer.RoomClassifierTrainer.fit', return_value={'val_acc': [85.0]}), \
         patch('wandb.init'), patch('wandb.log'), patch('wandb.finish'), \
         patch('yaml.safe_load', return_value=mock_config), \
         patch('os.path.exists', return_value=True), \
         patch('builtins.open', MagicMock()):
        
        # Now import main
        from scripts.train_model import main
        
        try:
            main("mock_config.yaml")
            print("\n--- Orchestration Verification Successful ---")
            return True
        except Exception as e:
            print(f"\n--- Orchestration Verification Failed ---")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    # Ensure tests/checkpoints exists for label saving
    Path("tests/checkpoints").mkdir(parents=True, exist_ok=True)
    success = test_orchestration()
    
    # Cleanup
    if Path("tests/checkpoints/class_labels.json").exists():
        os.remove("tests/checkpoints/class_labels.json")
    if Path("tests/checkpoints/best_model.pth").exists():
        os.remove("tests/checkpoints/best_model.pth")
    if Path("tests/checkpoints").exists():
        try:
            Path("tests/checkpoints").rmdir()
        except OSError:
            pass
        
    sys.exit(0 if success else 1)
