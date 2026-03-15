
import sys
import os
import cv2
import numpy as np
from pathlib import Path
from PIL import Image

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.enhancement.quality_gate import QualityGate

def create_test_images():
    base_dir = Path("tests/quality_test_data")
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. High Quality Image (Sharp, 1920x1080, Brightness ~128)
    hq_img = np.full((1080, 1920, 3), 128, dtype=np.uint8)
    # Add many sharp lines
    for i in range(0, 1920, 50):
        cv2.line(hq_img, (i, 0), (i, 1080), (255, 255, 255), 2)
    hq_path = base_dir / "hq.jpg"
    cv2.imwrite(str(hq_path), hq_img)
    
    # 2. Blurry Image (Low sharpness)
    blur_img = cv2.GaussianBlur(hq_img, (51, 51), 0)
    blur_path = base_dir / "blur.jpg"
    cv2.imwrite(str(blur_path), blur_img)
    
    # 3. Small Image (Low resolution)
    small_img = np.full((300, 400, 3), 128, dtype=np.uint8)
    small_path = base_dir / "small.jpg"
    cv2.imwrite(str(small_path), small_img)
    
    # 4. Dark Image (Low brightness)
    dark_img = np.full((1080, 1920, 3), 10, dtype=np.uint8)
    dark_path = base_dir / "dark.jpg"
    cv2.imwrite(str(dark_path), dark_img)
    
    return {
        "hq": hq_path,
        "blur": blur_path,
        "small": small_path,
        "dark": dark_path
    }

def test_quality_gate():
    print("--- Starting Quality Gate Verification ---")
    
    paths = create_test_images()
    gate = QualityGate()
    
    try:
        # TEST 1: HQ Image
        print("\nTesting High Quality Image...")
        res_hq = gate.check(paths["hq"])
        print(f"Result: {res_hq['grade']} (Sharpness: {res_hq['sharpness_score']})")
        assert res_hq["passed"] is True, "HQ image should have passed"
        
        # TEST 2: Blurry Image
        print("\nTesting Blurry Image...")
        res_blur = gate.check(paths["blur"])
        print(f"Result: {res_blur['grade']} (Sharpness: {res_blur['sharpness_score']})")
        print(f"Failures: {res_blur['failures']}")
        assert res_blur["passed"] is False, "Blurry image should have failed"
        assert any("blur" in f.lower() for f in res_blur["failures"])
        
        # TEST 3: Small Image
        print("\nTesting Small Image...")
        res_small = gate.check(paths["small"])
        print(f"Result: {res_small['grade']} (Resolution: {res_small['resolution']})")
        assert res_small["passed"] is False, "Small image should have failed"
        assert any("small" in f.lower() for f in res_small["failures"])
        
        # TEST 4: Dark Image
        print("\nTesting Dark Image...")
        res_dark = gate.check(paths["dark"])
        print(f"Result: {res_dark['grade']} (Brightness: {res_dark['brightness_score']})")
        assert res_dark["passed"] is False, "Dark image should have failed"
        assert any("dark" in f.lower() for f in res_dark["failures"])
        
        # TEST 5: Batch Processing
        print("\nTesting Batch Check...")
        batch_res = gate.check_batch(list(paths.values()))
        print(f"Batch Summary: {batch_res['passed']}/{batch_res['total']} passed")
        assert batch_res["total"] == 4
        assert batch_res["passed"] == 1
        
        print("\n--- All Quality Gate Verification Tests Passed ---")
        return True
    except Exception as e:
        print(f"\n--- Quality Gate Verification Failed ---")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        import shutil
        if Path("tests/quality_test_data").exists():
            shutil.rmtree("tests/quality_test_data")

if __name__ == "__main__":
    success = test_quality_gate()
    sys.exit(0 if success else 1)
