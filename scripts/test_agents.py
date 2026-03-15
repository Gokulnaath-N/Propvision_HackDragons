import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.agents.orchestrator import search_properties, process_listing
from src.utils.logger import get_logger

logger = get_logger(__name__)

def test_query_pipeline():
    print("\n--- STEP 1: TEST QUERY PIPELINE ---")
    
    queries = [
        "2BHK flat in Chennai under 70 lakhs vastu compliant",
        "modern kitchen with granite counter",
        "spacious bedroom with natural light"
    ]
    
    success = True
    
    for q in queries:
        print(f"\nRunning search: '{q}'")
        try:
            result = search_properties(q)
            
            parsed = result.get("parsed_intent", {})
            location = parsed.get("location")
            bhk = parsed.get("bhk")
            price_max = parsed.get("price_max")
            
            clip_query = parsed.get("clip_search_query")
            total_found = result.get("total_found")
            
            print(f"  Query: {q}")
            print(f"  Parsed: location={location}, bhk={bhk}, price_max={price_max}")
            print(f"  CLIP query: {clip_query}")
            print(f"  Results found: {total_found}")
            
            reranked = result.get("reranked_results", [])
            if reranked:
                top_result = reranked[0]
                listing_id = top_result.get("listing_id", "unknown")
                score = top_result.get("score", 0.0)
                print(f"  Top result: {listing_id}, score={score:.4f}")
            else:
                print("  Top result: None")
                
            time_ms = result.get("search_time_ms")
            print(f"  Time: {time_ms} ms")
            
        except Exception as e:
            print(f"  ERROR: {e}")
            logger.error(f"Search failed: {e}")
            success = False
            
    return success

def test_listing_pipeline():
    print("\n--- STEP 2: TEST LISTING PIPELINE ---")
    
    # Path to test images
    base_dir = Path("data/processed/test")
    
    # Check if we have enough images to test
    if not base_dir.exists():
        print(f"  Skipping: Test directory {base_dir} does not exist.")
        return False
        
    image_paths = []
    
    # Try to grab one from each required category if available
    categories = ["bathroom", "kitchen", "bedroom", "hall", "pooja_room"]
    for cat in categories:
        cat_dir = base_dir / cat
        if cat_dir.exists():
            files = list(cat_dir.glob("*.jpg")) + list(cat_dir.glob("*.jpeg")) + list(cat_dir.glob("*.png"))
            if files:
                image_paths.append(str(files[0]))
                
    # If we couldn't find specific categories, just grab any 5 images from the test directory
    if len(image_paths) < 5:
        all_files = list(base_dir.rglob("*.jpg")) + list(base_dir.rglob("*.jpeg")) + list(base_dir.rglob("*.png"))
        for f in all_files:
            if str(f) not in image_paths:
                image_paths.append(str(f))
            if len(image_paths) >= 5:
                break
                
    if not image_paths:
        print(f"  Skipping: No images found in {base_dir} or its subdirectories.")
        return False
        
    print(f"  Found {len(image_paths)} images to test.")
    
    try:
        result = process_listing(
            listing_id="test_listing_agent_001",
            image_paths=image_paths,
            metadata={
                "city": "Chennai",
                "price": 6500000,
                "bhk": 2,
                "vastu": True,
                "location": "Anna Nagar"
            }
        )
        
        status = result.get("processing_status")
        
        classifications = result.get("room_classifications", [])
        room_types = [c.get("room_type") for c in classifications]
        
        quality = result.get("quality_scores", [])
        grades = [q.get("grade") for q in quality]
        
        print(f"  Processing status: {status}")
        print(f"  Rooms classified: {room_types}")
        print(f"  Quality grades: {grades}")
        print(f"  Hero image: {result.get('hero_image')}")
        print(f"  Overall grade: {result.get('overall_grade')}")
        
        summary = result.get("listing_summary", "")
        print(f"  Summary: {summary}")
        
        actions = result.get("action_items", [])
        print(f"  Action items: {actions}")
        
        print(f"  Processing time: {result.get('processing_time_seconds')}s")
        return True
        
    except Exception as e:
        print(f"  ERROR: {e}")
        logger.error(f"Listing processing failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting LangGraph Agents Pipeline Tests...")
    
    query_success = test_query_pipeline()
    listing_success = test_listing_pipeline()
    
    print("\n--- STEP 3: SUMMARY ---")
    if query_success and listing_success:
        print("Phase 8 LangGraph Agents: ALL TESTS PASSED")
    else:
        print("Some tests failed. Check logs for details.")
