
import sys
import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from pathlib import Path
import numpy as np

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.models.evaluator import ModelEvaluator

class MockModel(nn.Module):
    def __init__(self, num_classes=6):
        super().__init__()
        self.fc = nn.Linear(10, num_classes)
        
    def forward(self, x):
        # Return controlled outputs for predictable testing
        batch_size = x.shape[0]
        # Just return dummy logits
        return torch.randn(batch_size, 6)

class DummyTestDataset(Dataset):
    def __init__(self, size=30, num_classes=6):
        self.size = size
        self.num_classes = num_classes
        # Fixed labels to test distribution
        self.labels = [i % num_classes for i in range(size)]
        
    def __len__(self):
        return self.size
        
    def __getitem__(self, idx):
        return torch.randn(3, 224, 224), self.labels[idx]

def test_evaluator():
    print("--- Starting Evaluator Verification ---")
    try:
        device = torch.device('cpu')
        class_names = ["Living Room", "Bedroom", "Kitchen", "Bathroom", "Hall", "Dining Room"]
        
        # Setup model and data
        model = MockModel()
        test_ds = DummyTestDataset(size=30)
        test_loader = DataLoader(test_ds, batch_size=5)
        
        # Initialize evaluator
        evaluator = ModelEvaluator(model, test_loader, class_names, device)
        print("Evaluator initialized successfully.")
        
        # Run evaluation
        print("\nRunning inference and calculating metrics...")
        metrics = evaluator.evaluate()
        
        # Verify metrics structure
        required_keys = ["overall_accuracy", "macro_f1", "weighted_f1", "per_class_f1", "confusion_matrix", "class_names"]
        for key in required_keys:
            if key not in metrics:
                print(f"Error: Metric key '{key}' missing.")
                return False
        
        print("Metrics structure verified.")
        
        # Print reports
        print("\nTesting console reporting (Rich):")
        evaluator.print_report(metrics)
        
        # Test plots
        plot_path = "tests/reports/confusion_matrix.png"
        evaluator.plot_confusion_matrix(metrics, plot_path)
        if Path(plot_path).exists():
            print(f"Confusion matrix plot generated: {plot_path}")
        else:
            print("Error: Confusion matrix plot not generated.")
            return False
            
        # Test JSON saving
        json_path = "tests/reports/metrics.json"
        evaluator.save_metrics(metrics, json_path)
        if Path(json_path).exists():
            print(f"Metrics JSON saved: {json_path}")
        else:
            print("Error: Metrics JSON not saved.")
            return False
            
        # Cleanup
        # if Path("tests/reports").exists():
        #     for file in Path("tests/reports").iterdir():
        #         file.unlink()
        #     Path("tests/reports").rmdir()
            
        print("\n--- All Evaluator Verification Tests Passed ---")
        return True
    except Exception as e:
        print(f"\n--- Evaluator Verification Failed ---")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_evaluator()
    sys.exit(0 if success else 1)
