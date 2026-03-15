
import sys
import os
import torch
import cv2
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.pipeline.enhancement import PropertyImageEnhancer

def create_test_image(path):
    # Create a small 64x64 valid RGB image (low res)
    img_data = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
    cv2.imwrite(str(path), img_data)

def test_enhancement():
    print("--- Starting Enhancement Verification ---")
    
    # We need to set PYTHONPATH for the subprocess or the current process
    # But since we added them to sys.path in enhancement.py, it should work.
    
    test_img = Path("tests/enhance_test_in.jpg")
    out_img = Path("tests/enhance_test_out.jpg")
    create_test_image(test_img)
    
    try:
        # 1. Initialize Enhancer
        print("Initializing Enhancer (this may take a moment to load weights)...")
        enhancer = PropertyImageEnhancer(use_gpu=torch.cuda.is_available())
        print("Enhancer initialized successfully.")
        
        # 2. Test Single Enhancement
        print(f"\nEnhancing {test_img}...")
        restored = enhancer.enhance_image(test_img, out_img)
        
        # 3. Check Results
        if out_img.exists():
            final_img = cv2.imread(str(out_img))
            print(f"Original Shape: 64x64")
            print(f"Enhanced Shape: {final_img.shape[0]}x{final_img.shape[1]}")
            
            # Should be 4x upscale (64 * 4 = 256)
            assert final_img.shape[0] == 256, f"Expected 256 height, got {final_img.shape[0]}"
            print("\nVerification Results: Correct 4x upscaling detected.")
        else:
            print("\nVerification Failed: Output image was not created.")
            return False
            
        print("\n--- All Enhancement Verification Tests Passed ---")
        return True
    except Exception as e:
        print(f"\n--- Enhancement Verification Failed ---")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if test_img.exists():
            os.remove(test_img)
        if out_img.exists():
            # Keep the output for the user to see if they want, or remove it.
            # I'll remove it to keep the tests clean.
            os.remove(out_img)

if __name__ == "__main__":
    # Ensure PYTHONPATH is correct for the internal imports in enhancement.py
    # Though enhancement.py handles it, having it in the env is safer.
    success = test_enhancement()
    sys.exit(0 if success else 1)
