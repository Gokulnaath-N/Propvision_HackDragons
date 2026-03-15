from collections import defaultdict
from typing import List, Dict, Optional
from src.search.qdrant_client import QdrantManager
from src.vision.clip_embedder import CLIPEmbedder
from src.utils.logger import get_logger
from src.utils.exceptions import SearchQueryError

class PropertySearcher:
    """
    Execute semantic property search using CLIP text embeddings
    and Qdrant vector similarity. Converts natural language
    queries into visual property matches.
    """
    def __init__(self):
        self.logger = get_logger(__name__)
        self.qdrant = QdrantManager()
        self.clip = CLIPEmbedder()
        self.min_similarity = 0.20
        self.max_results = 20
        self.logger.info("PropertySearcher initialized")

    def search(self, query_text: str, filters: Optional[Dict] = None, top_k: int = 20) -> Dict:
        """
        Main search function. Finds most semantically similar listings
        to a natural language query with optional metadata filtering.
        """
        if not query_text or len(query_text.strip()) < 3:
            raise SearchQueryError("Query too short or empty")
            
        self.logger.info(f"Searching for: '{query_text}' with filters: {filters}")
        
        # STEP 1 — EMBED QUERY TEXT
        query_vector = self.clip.embed_text(query_text)
        
        # STEP 2 — SEARCH QDRANT (get more candidates for grouping)
        # We fetch 50 candidates to ensure we have enough variety after grouping
        raw_results = self.qdrant.search(
            query_vector=query_vector,
            filters=filters or {},
            top_k=50
        )
        self.logger.info(f"Qdrant returned {len(raw_results)} raw results")
        
        # STEP 3 — FILTER BY MINIMUM SIMILARITY
        filtered = [r for r in raw_results if r["score"] >= self.min_similarity]
        self.logger.info(f"After similarity filter (score >= {self.min_similarity}): {len(filtered)} results")
        
        # STEP 4 — GROUP BY LISTING AND KEEP BEST IMAGE (Diversity Control)
        listing_groups = defaultdict(list)
        for result in filtered:
            listing_groups[result["listing_id"]].append(result)
            
        best_per_listing = []
        for listing_id, images in listing_groups.items():
            # Sort images within listing by score descending
            sorted_images = sorted(images, key=lambda x: x["score"], reverse=True)
            # Keep only the best scoring image for this property
            best_per_listing.append(sorted_images[0])
            
        # STEP 5 — SORT FINAL RESULTS AND CLIP
        best_per_listing.sort(key=lambda x: x["score"], reverse=True)
        final_results = best_per_listing[:top_k]
        
        # STEP 6 — FORMAT RESPONSE
        return {
            "query": query_text,
            "filters_applied": filters,
            "total_found": len(best_per_listing),
            "results": [
                {
                    "listing_id": r["listing_id"],
                    "match_score": float(round(r["score"], 4)),
                    "room_type": r["room_type"],
                    "image_path": r["image_path"],
                    "quality_grade": r["quality_grade"],
                    "city": r["city"],
                    "price": float(r["price"]),
                    "bhk": int(r["bhk"]),
                    "vastu": bool(r["vastu"]),
                    "payload": r["payload"]
                }
                for r in final_results
            ]
        }

    def search_by_room(self, room_type: str, filters: Optional[Dict] = None) -> Dict:
        """
        Find listings that have a specific room type using room-specific templates.
        """
        queries = {
            "hall": "spacious living room hall interior with sofa and natural light",
            "kitchen": "modern kitchen with cabinets and clean surfaces",
            "bedroom": "comfortable bedroom with big bed and interior design",
            "bathroom": "clean modern bathroom with tiles and fixtures",
            "pooja_room": "traditional Indian pooja room prayer mandir",
            "dining_room": "dining room with table and chairs area",
            "balcony": "open balcony with view and seating",
            "exterior": "property exterior frontage building entrance"
        }
        
        query = queries.get(room_type.lower(), f"{room_type} interior")
        
        # Ensure room_type filter is applied if not already
        search_filters = filters.copy() if filters else {}
        if "room_type" not in search_filters:
            search_filters["room_type"] = room_type.lower()
            
        return self.search(query, search_filters)

    def test_search(self) -> bool:
        """
        Quick health check for search capabilities.
        """
        try:
            results = self.search("modern property", top_k=1)
            return len(results["results"]) >= 0 # Returns true if call succeeds
        except Exception as e:
            self.logger.error(f"Search health check failed: {e}")
            return False
