
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.data.augmentation import (
    get_train_transforms, 
    get_val_transforms, 
    get_inference_transforms
)

def test_augmentation():
    print("--- Starting Augmentation Verification ---")
    
    try:
        # Check Train Transforms
        train_trans = get_train_transforms(image_size=380)
        print("\nTrain Transforms:")
        print(train_trans)
        assert len(train_trans.transforms) == 8, "Train should have 8 steps"
        
        # Check Val/Test Transforms
        val_trans = get_val_transforms(image_size=380)
        print("\nValidation/Test Transforms:")
        print(val_trans)
        assert len(val_trans.transforms) == 4, "Val should have 4 steps"
        
        # Check Inference Transforms
        inf_trans = get_inference_transforms(image_size=380)
        print("\nInference Transforms:")
        print(inf_trans)
        
        print("\n--- All Augmentation Verification Tests Passed ---")
        return True
    except Exception as e:
        print(f"\n--- Augmentation Verification Failed ---")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_augmentation()
    sys.exit(0 if success else 1)
