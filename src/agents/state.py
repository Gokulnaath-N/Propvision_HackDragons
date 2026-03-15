"""
src/agents/state.py
-------------------
TypedDict state objects that flow through LangGraph pipelines.

Two independent state types:
  - ListingState  : broker image-upload processing pipeline
  - QueryState    : user natural-language search pipeline

All fields are Optional where downstream nodes must handle
None gracefully so a partial failure in one stage does not
crash the entire graph.
"""

from typing import TypedDict, Optional, List, Dict, Any


# ---------------------------------------------------------------------------
# ListingState
# ---------------------------------------------------------------------------

class ListingState(TypedDict):
    """
    State object for the broker image-upload pipeline.

    Flows through nodes:
        enhance → classify → score → embed → analyze → synthesize → index
    """

    # ── Inputs ──────────────────────────────────────────────────────────────
    listing_id: str
    raw_image_paths: List[str]

    # Metadata supplied by broker at upload time.
    # Expected keys: city, price, bhk, vastu, location
    metadata: Dict[str, Any]

    # ── Enhancement node outputs ─────────────────────────────────────────
    enhanced_image_paths: List[str]   # Paths to super-resolved images
    enhancement_failed: List[str]     # Paths that could not be enhanced

    # ── Classifier node outputs ──────────────────────────────────────────
    # Each dict: { image_path, room_type, confidence }
    room_classifications: List[Dict]

    # ── Quality-scoring node outputs ─────────────────────────────────────
    # Each dict: { image_path, grade, final_score, sharpness }
    quality_scores: List[Dict]

    # ── CLIP-embedding node outputs ──────────────────────────────────────
    # Each dict: { image_path, embedding }  — embedding is List[float] (512-d)
    clip_embeddings: List[Dict]

    # ── Spatial-analysis node outputs ────────────────────────────────────
    # Each dict: { image_path, room_type, condition, natural_light,
    #              vastu_signals, key_features }
    spatial_analyses: List[Dict]

    # ── Synthesis node outputs ───────────────────────────────────────────
    hero_image: Optional[str]         # Best image path chosen for the listing
    gallery_order: List[str]          # Ordered list of image paths for display
    overall_grade: Optional[str]      # e.g. "A", "B+", "C"
    listing_summary: Optional[str]    # Human-readable narrative summary
    action_items: List[str]           # Suggested improvements for the broker

    # ── Indexing node outputs ────────────────────────────────────────────
    indexed_count: int                # Number of vectors successfully upserted

    # ── Pipeline bookkeeping ─────────────────────────────────────────────
    # Valid values: "pending" | "enhancing" | "classifying" | "scoring" |
    #               "embedding" | "analyzing" | "synthesizing" |
    #               "indexing" | "complete" | "failed"
    processing_status: str

    error: Optional[str]                    # Last-seen error message, if any
    processing_time_seconds: Optional[float]  # Wall-clock time for the run


# ---------------------------------------------------------------------------
# QueryState
# ---------------------------------------------------------------------------

class QueryState(TypedDict):
    """
    State object for the user search-query pipeline.

    Flows through nodes:
        parse_intent → embed_query → build_filters → search → rerank → explain
    """

    # ── Inputs ──────────────────────────────────────────────────────────────
    raw_query: str                    # Raw natural-language query from the user

    # ── Intent-parsing node outputs ──────────────────────────────────────
    # Expected keys: location, bhk, price_max, price_min,
    #                vastu, room_features, clip_search_query
    parsed_intent: Dict[str, Any]

    # ── CLIP-embedding node outputs ──────────────────────────────────────
    # 512-dim embedding derived from parsed_intent["clip_search_query"]
    clip_query_vector: Optional[List[float]]

    # ── Filter-building node outputs ─────────────────────────────────────
    filters: Dict[str, Any]           # Structured Qdrant filter payload

    # ── Search node outputs ──────────────────────────────────────────────
    raw_results: List[Dict]           # Direct Qdrant hits before reranking

    # ── Reranking node outputs ───────────────────────────────────────────
    reranked_results: List[Dict]      # Final sorted result list

    # ── Explanation node outputs ─────────────────────────────────────────
    # Maps listing_id → plain-English explanation of why it matched
    match_explanations: Dict[str, str]

    # ── Telemetry ────────────────────────────────────────────────────────
    total_found: int                  # Total candidates before reranking
    search_time_ms: Optional[float]   # End-to-end search latency in ms

    # ── Conversational context ────────────────────────────────────────────
    # Each dict: { role: "user" | "assistant", content: str }
    conversation_history: List[Dict]

    # ── Error bookkeeping ────────────────────────────────────────────────
    error: Optional[str]
