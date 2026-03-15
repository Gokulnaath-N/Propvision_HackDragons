import sys
import os

sys.path.append(os.path.abspath("."))

print("="*50)
print("PROPVISION AI - FULL HEALTH CHECK")
print("="*50)

# 1. Utils
try:
    from src.utils.logger import get_logger
    from src.utils.exceptions import PropVisionError
    from src.utils.gpu_utils import get_device
    from src.utils.image_utils import load_image
    print("UTILS              OK")
except Exception as e:
    print(f"UTILS              FAIL - {e}")

# 2. Data Pipeline
try:
    from src.data.dataset import RoomDataset
    from src.data.augmentation import get_train_transforms
    from src.data.dataloader import get_dataloaders
    print("DATA PIPELINE      OK")
except Exception as e:
    print(f"DATA PIPELINE      FAIL - {e}")

# 3. Model
try:
    from src.models.room_classifier import RoomClassifier
    from src.models.predictor import RoomPredictor
    predictor = RoomPredictor()
    print("ROOM CLASSIFIER    OK")
except Exception as e:
    print(f"ROOM CLASSIFIER    FAIL - {e}")

# 4. Enhancement
try:
    from src.enhancement.preprocessor import ImagePreprocessor
    from src.enhancement.realesrgan import RealESRGANEnhancer
    from src.enhancement.postprocessor import ImagePostprocessor
    from src.enhancement.quality_gate import QualityGate
    print("ENHANCEMENT        OK")
except Exception as e:
    print(f"ENHANCEMENT        FAIL - {e}")

# 5. Vision
try:
    from src.vision.clip_embedder import CLIPEmbedder
    from src.vision.quality_scorer import ImageQualityScorer
    from src.vision.spatial_analyzer import SpatialAnalyzer
    print("VISION PIPELINE    OK")
except Exception as e:
    print(f"VISION PIPELINE    FAIL - {e}")

# 6. Search
try:
    from src.search.qdrant_client import QdrantManager
    from src.search.indexer import ListingIndexer
    from src.search.searcher import PropertySearcher
    from src.search.reranker import SearchReranker
    qdrant = QdrantManager()
    stats = qdrant.get_collection_stats()
    print(f"SEARCH + QDRANT    OK - {stats['total_vectors']} vectors")
except Exception as e:
    print(f"SEARCH + QDRANT    FAIL - {e}")

# 7. GPU
try:
    import torch
    print(f"GPU                OK - {torch.cuda.get_device_name(0)}")
    print(f"CUDA               OK - {torch.cuda.is_available()}")
except Exception as e:
    print(f"GPU                FAIL - {e}")

# 8. Docker Services
try:
    import redis
    r = redis.from_url("redis://localhost:6379")
    r.ping()
    print("REDIS              OK")
except Exception as e:
    print(f"REDIS              FAIL - {e}")

try:
    import psycopg2
    from dotenv import load_dotenv
    import os
    load_dotenv()
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    conn.close()
    print("POSTGRESQL         OK")
except Exception as e:
    print(f"POSTGRESQL         FAIL - {e}")

# 9. API Keys
try:
    from dotenv import load_dotenv
    import os
    load_dotenv()
    keys = {
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "QDRANT_URL": os.getenv("QDRANT_URL"),
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
    }

    for k, v in keys.items():
        status = "OK" if v else "MISSING"
        print(f"{k:<20} {status}")

except Exception as e:
    print(f"API KEYS           FAIL - {e}")

print("="*50)
print("HEALTH CHECK COMPLETE")
print("="*50)