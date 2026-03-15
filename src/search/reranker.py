from src.utils.logger import get_logger

class SearchReranker:
    """
    Re-rank search results combining CLIP similarity score
    with image quality grade and listing completeness.
    Produces final ranked list for display to user.
    """
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # RERANKING WEIGHTS
        self.weights = {
            "clip_similarity": 0.40,
            "quality_grade":   0.30,
            "completeness":    0.20,
            "user_signals":    0.10
        }
        
        # GRADE TO SCORE MAPPING
        self.grade_scores = {
            "A+": 1.00,
            "A":  0.85,
            "B+": 0.70,
            "B":  0.55,
            "C":  0.35,
            "D":  0.10
        }
        
        self.logger.info("SearchReranker initialized")

    def rerank(self, search_results: list, listing_metadata: dict = None) -> list:
        """
        Rerank a list of search results using a multi-signal weighted sum.
        """
        if not search_results:
            return []
            
        self.logger.info(f"Reranking {len(search_results)} results...")
        
        for result in search_results:
            # 1. CLIP SCORE (already normalized 0-1)
            clip_score = result.get("match_score", 0.0)
            
            # 2. QUALITY SCORE
            grade = result.get("quality_grade", "C")
            quality_score = self.grade_scores.get(grade, 0.35)
            
            # 3. COMPLETENESS SCORE
            # Represents how many different room types the listing provides
            completeness_score = 0.5 # Default neutral
            if listing_metadata and result["listing_id"] in listing_metadata:
                rooms = listing_metadata[result["listing_id"]].get("room_types", [])
                unique_rooms = set(rooms)
                # Normalize by expected total room types (roughly 6 key rooms)
                completeness = len(unique_rooms) / 6.0
                completeness_score = min(1.0, completeness)
            
            # 4. USER SIGNALS SCORE (Placeholder for future data)
            user_signals_score = 0.5
            
            # CALCULATE FINAL WEIGHTED SCORE
            final_score = (
                clip_score        * self.weights["clip_similarity"] +
                quality_score     * self.weights["quality_grade"]   +
                completeness_score * self.weights["completeness"]   +
                user_signals_score * self.weights["user_signals"]
            )
            
            result["rerank_score"] = float(round(final_score, 4))
            result["component_scores"] = {
                "clip": float(clip_score),
                "quality": float(quality_score),
                "completeness": float(completeness_score),
                "user_signals": float(user_signals_score)
            }
            
        # Sort results by rerank_score descending
        sorted_results = sorted(search_results, key=lambda x: x["rerank_score"], reverse=True)
        return sorted_results

    def format_for_api(self, reranked_results: list) -> list:
        """
        Format results for a client API response, removing internal payloads.
        """
        api_results = []
        for r in reranked_results:
            api_results.append({
                "listing_id": r.get("listing_id"),
                "match_score": r.get("match_score"),
                "rerank_score": r.get("rerank_score"),
                "room_type": r.get("room_type"),
                "image_path": r.get("image_path"),
                "quality_grade": r.get("quality_grade"),
                "city": r.get("city"),
                "price": r.get("price"),
                "bhk": r.get("bhk"),
                "vastu": r.get("vastu"),
                "component_scores": r.get("component_scores")
            })
        return api_results
