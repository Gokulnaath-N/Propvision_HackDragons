
import sys
import numpy as np
from pathlib import Path
from PIL import Image

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.vision.clip_embedder import CLIPEmbedder
from src.utils.logger import get_logger

logger = get_logger("verify_clip")

def test_clip():
    print("--- Starting CLIP Embedder Verification ---")
    
    try:
        embedder = CLIPEmbedder()
        
        # 1. Test Text Embedding
        print("\nTesting Text Embedding...")
        text_emb = embedder.embed_text("A modern kitchen with marble island")
        print(f"Text Embedding Shape: {text_emb.shape}")
        assert text_emb.shape == (512,), "Text embedding shape mismatch"
        # Check normalization (norm should be ~1.0)
        norm = np.linalg.norm(text_emb)
        print(f"Norm (Normalized): {norm:.4f}")
        assert 0.99 <= norm <= 1.01, f"Text embedding not normalized: {norm}"
        
        # 2. Test Image Embedding
        print("\nTesting Image Embedding...")
        # Pick a random image from dataset if available
        test_img_dir = Path("data/processed/test")
        sample_images = list(test_img_dir.glob("**/*.jpg"))
        
        if sample_images:
            img_path = sample_images[0]
            print(f"Using sample image: {img_path}")
            img_emb = embedder.embed_image(img_path)
            print(f"Image Embedding Shape: {img_emb.shape}")
            assert img_emb.shape == (512,), "Image embedding shape mismatch"
            norm = np.linalg.norm(img_emb)
            print(f"Norm (Normalized): {norm:.4f}")
            assert 0.99 <= norm <= 1.01, f"Image embedding not normalized: {norm}"
        else:
            print("No sample images found, skipping image embedding check.")
            
        # 3. Test Semantic Similarity
        # Text: "kitchen" vs Images from kitchen/bathroom
        print("\nTesting Semantic Similarity Logic...")
        kitchen_dir = test_img_dir / "kitchen"
        bathroom_dir = test_img_dir / "bathroom"
        
        kitchen_files = list(kitchen_dir.glob("*.jpg"))[:2]
        bathroom_files = list(bathroom_dir.glob("*.jpg"))[:2]
        
        if kitchen_files and bathroom_files:
            query = "A photo of a kitchen with cabinets"
            query_emb = embedder.embed_text(query)
            
            k_emb = embedder.embed_image(kitchen_files[0])
            b_emb = embedder.embed_image(bathroom_files[0])
            
            k_sim = embedder.cosine_similarity(query_emb, k_emb)
            b_sim = embedder.cosine_similarity(query_emb, b_emb)
            
            print(f"Query: '{query}'")
            print(f"Similarity to Kitchen Image: {k_sim:.4f}")
            print(f"Similarity to Bathroom Image: {b_sim:.4f}")
            
            assert k_sim > b_sim, f"Semantic search failed: kitchen should be more similar to '{query}' than bathroom"
            print("Semantic similarity check PASSED!")
        else:
            print("Skipping semantic check (missing class folders)")

        # 4. Test Batch Processing
        if len(sample_images) >= 5:
            print("\nTesting Batch Embedding...")
            batch_paths = sample_images[:5]
            batch_embs = embedder.embed_images_batch(batch_paths)
            print(f"Batch Embeddings Shape: {np.array(batch_embs).shape}")
            assert len(batch_embs) == 5
            
        print("\n--- CLIP Embedder Verification SUCCESS ---")
        return True
        
    except Exception as e:
        print(f"\n--- CLIP Embedder Verification FAILED ---")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_clip()
    sys.exit(0 if success else 1)
