
import sys
import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Mock wandb before importing trainer
import wandb
wandb.init = MagicMock()
wandb.log = MagicMock()
wandb.finish = MagicMock()

from src.models.room_classifier import RoomClassifier
from src.models.trainer import RoomClassifierTrainer

class DummyDataset(Dataset):
    def __init__(self, size=10, num_classes=6):
        self.size = size
        self.num_classes = num_classes
        
    def __len__(self):
        return self.size
        
    def __getitem__(self, idx):
        return torch.randn(3, 224, 224), torch.randint(0, self.num_classes, (1,)).item()
        
    def get_class_weights(self):
        return [1.0] * self.num_classes

def test_trainer():
    print("--- Starting Trainer Verification ---")
    try:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Using device: {device}")
        
        # Setup model
        model = RoomClassifier(num_classes=6, pretrained=False).to(device)
        
        # Setup data
        train_ds = DummyDataset(size=20)
        val_ds = DummyDataset(size=10)
        train_loader = DataLoader(train_ds, batch_size=4)
        val_loader = DataLoader(val_ds, batch_size=4)
        
        # Setup config
        config = {
            'epochs': 2,
            'lr_pretrained': 0.0001,
            'lr_head': 0.001,
            'project_name': 'TestProject',
            'checkpoint_dir': 'tests/checkpoints'
        }
        
        # Initialize trainer
        trainer = RoomClassifierTrainer(model, train_loader, val_loader, config, device)
        print("Trainer initialized successfully.")
        
        # Verify differential learning rates
        print("\nVerifying learning rates:")
        for i, group in enumerate(trainer.optimizer.param_groups):
            print(f"  Group {i} LR: {group['lr']}")
        
        if trainer.optimizer.param_groups[0]['lr'] == 0.0001 and trainer.optimizer.param_groups[1]['lr'] == 0.001:
            print("Differential learning rates verified.")
        else:
            print("Error: Differential learning rates not applied correctly.")
            return False
            
        # Run fit (mocked wandb)
        print("\nRunning fit for 2 epochs...")
        history = trainer.fit()
        
        print("\nTraining History:")
        for k, v in history.items():
            print(f"  {k}: {v}")
            
        if len(history['train_loss']) == 2:
            print("\nFit completed and history recorded.")
        else:
            print("\nError: Fit did not run for expected number of epochs.")
            return False
            
        # Cleanup
        checkpoint_file = Path('tests/checkpoints/best_model.pth')
        if checkpoint_file.exists():
            checkpoint_file.unlink()
            checkpoint_file.parent.rmdir()
            print("Cleaned up checkpoints.")

        print("\n--- All Trainer Verification Tests Passed ---")
        return True
    except Exception as e:
        print(f"\n--- Trainer Verification Failed ---")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_trainer()
    sys.exit(0 if success else 1)
