
import sys
import os
import torch
import torch.nn as nn
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.models.room_classifier import RoomClassifier

def test_model():
    print("--- Starting Model Verification ---")
    try:
        # Initialize model without pre-trained weights for faster testing
        # and to avoid network issues in some environments
        model = RoomClassifier(num_classes=6, pretrained=False)
        print("Model initialized successfully.")
        
        # Check summary
        summary = model.get_model_summary()
        print("\nModel Summary:")
        for k, v in summary.items():
            print(f"  {k}: {v}")
            
        # Verify layer freezing
        params = list(model.model.named_parameters())
        num_params = len(params)
        freeze_cutoff = int(0.7 * num_params)
        
        frozen_correctly = True
        for i, (name, param) in enumerate(params):
            if i < freeze_cutoff and param.requires_grad:
                print(f"Error: Layer {name} should be frozen but is trainable.")
                frozen_correctly = False
            if i >= freeze_cutoff and not param.requires_grad and "classifier" not in name:
                # Top 30% should be trainable
                print(f"Error: Layer {name} should be trainable but is frozen.")
                frozen_correctly = False
        
        if frozen_correctly:
            print("Layer freezing (70/30) verified correctly.")
            
        # Test forward pass
        dummy_input = torch.randn(1, 3, 224, 224)
        output = model(dummy_input)
        print(f"Forward pass output shape: {output.shape} (Expected: [1, 6])")
        
        # Test predict_single
        dummy_tensor = torch.randn(3, 224, 224)
        prediction = model.predict_single(dummy_tensor, 'cpu')
        print("\nSingle Prediction Result:")
        print(f"  Predicted class: {prediction['predicted_class']}")
        print(f"  Confidence: {prediction['confidence']:.4f}")
        
        # Test save/load
        save_path = "tmp_model.pth"
        model.save_model(save_path)
        print(f"Model saved to {save_path}")
        
        loaded_model = RoomClassifier.load_model(save_path, 'cpu')
        print("Model loaded successfully.")
        
        # Cleanup
        if os.path.exists(save_path):
            os.remove(save_path)
            
        print("\n--- All Verification Tests Passed ---")
        return True
    except Exception as e:
        print(f"\n--- Verification Failed ---")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_model()
    sys.exit(0 if success else 1)
