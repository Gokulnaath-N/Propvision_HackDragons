import numpy as np
from src.agents.state import QueryState
from src.vision.clip_embedder import CLIPEmbedder
from src.search.searcher import PropertySearcher
from src.search.reranker import SearchReranker
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SearchAgent:
    """
    LangGraph node that executes semantic search using CLIP text embeddings 
    and Qdrant vector database search.
    """

    def __init__(self, clip_embedder=None):
        self.clip = clip_embedder or CLIPEmbedder()
        self.searcher = PropertySearcher()
        self.reranker = SearchReranker()
        logger.info("SearchAgent initialized")

    def search(self, state: QueryState) -> QueryState:
        """
        Embeds the descriptive query explicitly built by Gemini, and executes a 
        filtered vector similarity search across Qdrant property listings.
        """
        parsed = state.get("parsed_intent", {})
        filters = state.get("filters", {})

        # Use explicitly constructed visual query from Gemini, fallback to raw input
        clip_query = parsed.get("clip_search_query") or state.get("raw_query", "")

        # Embed query text
        try:
            query_vector = self.clip.embed_text(clip_query)
            state["clip_query_vector"] = query_vector.tolist()
        except Exception as e:
            logger.error(f"Failed to embed query text '{clip_query}': {e}")
            state["error"] = "Failed to embed search query."
            state["raw_results"] = []
            state["reranked_results"] = []
            state["total_found"] = 0
            return state

        # Search Qdrant DB
        try:
            results = self.searcher.search(
                query_text=clip_query,
                filters=filters,
                top_k=20
            )
            state["raw_results"] = results.get("results", [])
            state["total_found"] = results.get("total_found", 0)

        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            state["error"] = "Database search failed."
            state["raw_results"] = []
            state["total_found"] = 0

        # Run custom ranking heuristic script
        if state["raw_results"]:
            try:
                reranked = self.reranker.rerank(state["raw_results"])
                state["reranked_results"] = reranked
            except Exception as e:
                logger.warning(f"Reranking failed: {e}")
                # Fallback to pure Qdrant vector cosine order
                state["reranked_results"] = state["raw_results"]
        else:
            state["reranked_results"] = []

        logger.info(
            f"Search complete: {state.get('total_found', 0)} "
            f"results found for vector query '{clip_query}'."
        )
        
        return state
