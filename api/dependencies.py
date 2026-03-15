"""
FastAPI shared dependencies — injected via Depends() in route handlers.
Lazy-loaded singletons to avoid heavy model loading at import time.
"""
from functools import lru_cache
from src.search.searcher import PropertySearcher
from src.search.indexer import ListingIndexer
from src.search.reranker import SearchReranker
from src.vision.quality_scorer import ImageQualityScorer


@lru_cache(maxsize=1)
def get_searcher() -> PropertySearcher:
    """Singleton PropertySearcher — loaded once at first request."""
    return PropertySearcher()


@lru_cache(maxsize=1)
def get_indexer() -> ListingIndexer:
    """Singleton ListingIndexer — loaded once at first request."""
    return ListingIndexer()


@lru_cache(maxsize=1)
def get_reranker() -> SearchReranker:
    """Singleton SearchReranker."""
    return SearchReranker()


@lru_cache(maxsize=1)
def get_quality_scorer() -> ImageQualityScorer:
    """Singleton ImageQualityScorer."""
    return ImageQualityScorer()
