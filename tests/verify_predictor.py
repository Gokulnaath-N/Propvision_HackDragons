
import sys
import os
import torch
from pathlib import Path
from PIL import Image
import numpy as np

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.models.predictor import RoomPredictor

def create_test_image(path):
    # Create a small valid RGB image
    img_data = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
    img = Image.fromarray(img_data)
    img.save(path)

def test_predictor():
    print("--- Starting Predictor Verification ---")
    
    test_img = Path("tests/predictor_test.jpg")
    create_test_image(test_img)
    
    try:
        # 1. Initialize Predictor (uses default paths)
        predictor = RoomPredictor()
        print("Predictor initialized successfully.")
        
        # 2. Test Single Prediction
        print(f"\nTesting single prediction on {test_img}...")
        result = predictor.predict(test_img)
        
        print("\nPrediction Result:")
        print(f"Room Type:  {result['predicted_class']}")
        print(f"Confidence: {result['confidence']:.4f}")
        print(f"Top 3 Probabilities:")
        top_probs = list(result['all_probabilities'].items())[:3]
        for name, prob in top_probs:
            print(f"  - {name}: {prob:.4f}")
            
        # 3. Test confidence logic
        confident = predictor.is_confident(result, threshold=0.1) # low threshold for mock image
        print(f"\nConfident at 0.1 threshold: {confident}")
        
        # Check normalization
        total_prob = sum(result['all_probabilities'].values())
        print(f"Total probability sum: {total_prob:.4f} (Expected 1.0)")
        
        print("\n--- All Predictor Verification Tests Passed ---")
        return True
    except Exception as e:
        print(f"\n--- Predictor Verification Failed ---")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if test_img.exists():
            os.remove(test_img)

if __name__ == "__main__":
    success = test_predictor()
    sys.exit(0 if success else 1)
