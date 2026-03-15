
import sys
import os
import cv2
import numpy as np
from pathlib import Path
from PIL import Image

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.enhancement.preprocessor import ImagePreprocessor

def create_complex_test_image(path):
    # 1. Create a dark base image (mean brightness ~40)
    img = np.full((300, 400, 3), 40, dtype=np.uint8)
    
    # 2. Add high-contrast tilted line (e.g. 5 degrees)
    # y = tan(5deg) * x + offset
    angle = 5.0
    rad = np.radians(angle)
    center = (200, 150)
    
    # Draw a dominant "wall line"
    x1, y1 = 50, int(150 + (50 - 200) * np.tan(rad))
    x2, y2 = 350, int(150 + (350 - 200) * np.tan(rad))
    cv2.line(img, (x1, y1), (x2, y2), (200, 200, 200), 2)
    
    # 3. Add noise (Gaussian noise)
    noise = np.random.normal(0, 15, img.shape).astype(np.float32)
    img = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    
    cv2.imwrite(str(path), img)
    return angle

def test_preprocessor():
    print("--- Starting Preprocessor Verification ---")
    
    test_img_path = Path("tests/prep_test_in.jpg")
    expected_tilt = create_complex_test_image(test_img_path)
    
    try:
        preprocessor = ImagePreprocessor()
        
        # Initial check
        original_img = cv2.imread(str(test_img_path))
        orig_mean = np.mean(original_img)
        print(f"Original Mean Brightness: {orig_mean:.2f}")
        
        # Run Preprocessing
        print("\nRunning Preprocessing...")
        preprocessed_img = preprocessor.preprocess(test_img_path)
        
        # 1. Check Brightness Improvement
        new_mean = np.mean(preprocessed_img)
        print(f"Enhanced Mean Brightness: {new_mean:.2f}")
        assert new_mean > orig_mean, "Brightness should have increased"
        
        # 2. Check Tilt Correction
        # We can run detection again on the result
        remaining_tilt = preprocessor._detect_tilt(preprocessed_img)
        print(f"Detected tilt after correction: {remaining_tilt:.2f} degrees")
        assert abs(remaining_tilt) < 3.0, "Tilt should be within threshold after correction"
        
        # 3. Check PIL conversion
        pil_img = preprocessor.preprocess_to_pil(test_img_path)
        assert isinstance(pil_img, Image.Image), "Conversion to PIL failed"
        assert pil_img.size == (400, 300), "Image dimensions changed unexpectedly"
        
        print("\n--- All Preprocessor Verification Tests Passed ---")
        return True
    except Exception as e:
        print(f"\n--- Preprocessor Verification Failed ---")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if test_img_path.exists():
            os.remove(test_img_path)

if __name__ == "__main__":
    success = test_preprocessor()
    sys.exit(0 if success else 1)
