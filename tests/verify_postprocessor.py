
import sys
import os
import numpy as np
from pathlib import Path
from PIL import Image
import shutil

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.enhancement.postprocessor import ImagePostprocessor

def create_raw_enhanced_image(path):
    # Create a base image (e.g. 500x500)
    img_data = np.random.randint(50, 200, (500, 500, 3), dtype=np.uint8)
    
    # Add artificial black borders (5 pixels)
    img_data[0:5, :, :] = 0
    img_data[-5:, :, :] = 0
    img_data[:, 0:5, :] = 0
    img_data[:, -5:, :] = 0
    
    img = Image.fromarray(img_data)
    img.save(path)
    return img

def test_postprocessor():
    print("--- Starting Post-Processor Verification ---")
    
    test_img_path = Path("tests/post_test_in.png")
    enhanced_pil = create_raw_enhanced_image(test_img_path)
    
    listing_id = "test_listing_123"
    image_idx = 5
    
    output_base = Path("data/enhanced")
    if output_base.exists():
        shutil.rmtree(output_base)
        
    try:
        postprocessor = ImagePostprocessor()
        
        # Run Post-processing
        print(f"Post-processing image for {listing_id}...")
        results = postprocessor.postprocess(enhanced_pil, listing_id, image_idx)
        
        # 1. Verify existence of all 3 files
        print("\nVerifying output files:")
        for key in ["hero", "gallery", "thumbnail"]:
            path = Path(results[key])
            print(f" - {key}: {path.name} (exists: {path.exists()})")
            assert path.exists(), f"{key} file missing"
            
            # Check dimensions
            with Image.open(path) as img:
                w, h = img.size
                print(f"   Resolution: {w}x{h}")
                if key == "hero":
                    assert (w, h) == (1920, 1080), "Hero size mismatch"
                elif key == "gallery":
                    assert (w, h) == (1280, 720), "Gallery size mismatch"
                elif key == "thumbnail":
                    assert (w, h) == (400, 300), "Thumbnail size mismatch"
                    
            # Check format
            assert path.suffix == ".webp", "Should be WebP format"

        # 2. Verify Smart Crop (internal check)
        cropped = postprocessor._remove_black_borders(enhanced_pil)
        # Original was 500x500. Borders were 5 pixels + 5 pixels padding = 10 pixels total per side?
        # Let's check logic: rmin=5 + pad(5) = 10, rmax=500-5 - pad(5) = 490.
        # So width/height should be ~480.
        print(f"\nCropped size: {cropped.width}x{cropped.height} (Original: 500x500)")
        assert cropped.width < 500 and cropped.height < 500, "Smart crop didn't shrink image"
        
        # 3. Check Metadata
        assert results["listing_id"] == listing_id
        assert results["image_idx"] == image_idx
        assert results["hero_size_kb"] > 0
        
        print("\n--- All Post-Processor Verification Tests Passed ---")
        return True
    except Exception as e:
        print(f"\n--- Post-Processor Verification Failed ---")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if test_img_path.exists():
            os.remove(test_img_path)
        if output_base.exists():
             shutil.rmtree(output_base)

if __name__ == "__main__":
    success = test_postprocessor()
    sys.exit(0 if success else 1)
