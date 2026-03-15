
import sys
import os
import torch
import cv2
import numpy as np
from pathlib import Path
from PIL import Image

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.enhancement.realesrgan import RealESRGANEnhancer

def create_test_image(path):
    # Create a small 100x100 valid RGB image
    img_data = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    cv2.imwrite(str(path), img_data)

def test_realesrgan():
    print("--- Starting Real-ESRGAN Verification ---")
    
    test_img = Path("tests/esr_test_in.jpg")
    create_test_image(test_img)
    
    try:
        # 1. Initialize Enhancer
        print("Initializing Real-ESRGAN Enhancer...")
        enhancer = RealESRGANEnhancer()
        print(f"Enhancer Info: {enhancer.get_info()}")
        
        # 2. Test Single Enhancement
        print(f"\nEnhancing {test_img}...")
        enhanced_pil = enhancer.enhance(test_img)
        
        # 3. Check Dimensions
        w, h = enhanced_pil.size
        print(f"Original Shape: 100x100")
        print(f"Enhanced Shape: {w}x{h}")
        
        # Should be 4x upscale (100 * 4 = 400)
        assert w == 400 and h == 400, f"Expected 400x400, got {w}x{h}"
        print("\nVerification Results: Correct 4x upscaling detected.")
        
        # 4. Test Batch Enhancement
        print("\nTesting batch enhancement...")
        results = enhancer.enhance_batch([test_img, test_img])
        assert len(results) == 2, "Batch size mismatch"
        assert all(isinstance(r, Image.Image) for r in results), "Batch results should be PIL Images"
        
        print("\n--- All Real-ESRGAN Verification Tests Passed ---")
        return True
    except Exception as e:
        print(f"\n--- Real-ESRGAN Verification Failed ---")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if test_img.exists():
            os.remove(test_img)

if __name__ == "__main__":
    success = test_realesrgan()
    sys.exit(0 if success else 1)
