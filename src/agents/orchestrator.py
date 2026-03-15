import time
from langgraph.graph import StateGraph, END
from src.agents.state import ListingState, QueryState
from src.agents.classifier_agent import ClassifierAgent
from src.agents.quality_agent import QualityAgent
from src.agents.spatial_agent import SpatialAgent
from src.agents.synthesis_agent import SynthesisAgent
from src.agents.query_agent import QueryAgent
from src.agents.search_agent import SearchAgent
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Singleton agent instances at module level
_classifier_agent = None
_quality_agent = None
_spatial_agent = None
_synthesis_agent = None
_query_agent = None
_search_agent = None

def get_classifier_agent() -> ClassifierAgent:
    global _classifier_agent
    if _classifier_agent is None:
        _classifier_agent = ClassifierAgent()
    return _classifier_agent

def get_quality_agent() -> QualityAgent:
    global _quality_agent
    if _quality_agent is None:
        _quality_agent = QualityAgent()
    return _quality_agent

def get_spatial_agent() -> SpatialAgent:
    global _spatial_agent
    if _spatial_agent is None:
        _spatial_agent = SpatialAgent()
    return _spatial_agent

def get_synthesis_agent() -> SynthesisAgent:
    global _synthesis_agent
    if _synthesis_agent is None:
        _synthesis_agent = SynthesisAgent()
    return _synthesis_agent

def get_query_agent() -> QueryAgent:
    global _query_agent
    if _query_agent is None:
        _query_agent = QueryAgent()
    return _query_agent

def get_search_agent(clip_embedder=None) -> SearchAgent:
    global _search_agent
    if _search_agent is None:
        _search_agent = SearchAgent(clip_embedder=clip_embedder)
    elif clip_embedder is not None:
        # Update existing agent with the provided embedder if needed
        _search_agent.clip = clip_embedder
    return _search_agent


# LISTING PROCESSING GRAPH

def build_listing_graph():
    """Builds and compiles the broker upload pipeline."""
    workflow = StateGraph(ListingState)
    
    # Add nodes
    workflow.add_node("classify_rooms", lambda s: get_classifier_agent().classify_rooms(s))
    workflow.add_node("score_quality", lambda s: get_quality_agent().score_images(s))
    workflow.add_node("analyze_spatial", lambda s: get_spatial_agent().analyze_images(s))
    workflow.add_node("embed_images", lambda s: get_classifier_agent().embed_images(s))
    workflow.add_node("synthesize", lambda s: get_synthesis_agent().synthesize_listing(s))
    
    # Set entry point
    workflow.set_entry_point("classify_rooms")
    
    # Add edges in order
    workflow.add_edge("classify_rooms", "score_quality")
    workflow.add_edge("score_quality", "analyze_spatial")
    workflow.add_edge("analyze_spatial", "embed_images")
    workflow.add_edge("embed_images", "synthesize")
    workflow.add_edge("synthesize", END)
    
    return workflow.compile()


# SEARCH GRAPH

def build_search_graph():
    """Builds and compiles the user search pipeline."""
    workflow = StateGraph(QueryState)
    
    def generate_explanations_node(state: QueryState) -> QueryState:
        explanations = get_synthesis_agent().generate_batch_explanations(
            state.get("reranked_results", []),
            state.get("parsed_intent", {})
        )
        state["match_explanations"] = explanations
        return state

    # Add nodes
    workflow.add_node("parse_query", lambda s: get_query_agent().parse_query(s))
    workflow.add_node("execute_search", lambda s: get_search_agent().search(s))
    workflow.add_node("generate_explanations", generate_explanations_node)
    
    # Set entry point
    workflow.set_entry_point("parse_query")
    
    # Add edges
    workflow.add_edge("parse_query", "execute_search")
    workflow.add_edge("execute_search", "generate_explanations")
    workflow.add_edge("generate_explanations", END)
    
    return workflow.compile()


# Compiled graph singletons
_listing_graph = None
_search_graph = None

def get_listing_graph():
    global _listing_graph
    if _listing_graph is None:
        _listing_graph = build_listing_graph()
    return _listing_graph

def get_search_graph():
    global _search_graph
    if _search_graph is None:
        _search_graph = build_search_graph()
    return _search_graph


# PUBLIC FUNCTIONS

def process_listing(listing_id: str, image_paths: list, metadata: dict) -> ListingState:
    """
    Run full listing pipeline for a broker upload.
    Initializes a new ListingState and passes it through the LangGraph workflow.
    """
    initial_state = ListingState(
        listing_id=listing_id,
        raw_image_paths=[str(p) for p in image_paths],
        metadata=metadata,
        enhanced_image_paths=[],
        enhancement_failed=[],
        room_classifications=[],
        quality_scores=[],
        clip_embeddings=[],
        spatial_analyses=[],
        hero_image=None,
        gallery_order=[],
        overall_grade=None,
        listing_summary=None,
        action_items=[],
        indexed_count=0,
        processing_status="pending",
        error=None,
        processing_time_seconds=None
    )
    
    start = time.time()
    graph = get_listing_graph()
    
    # Process through the compiled graph
    final_state = graph.invoke(initial_state)
    
    final_state["processing_time_seconds"] = round(time.time() - start, 2)
    
    logger.info(
        f"Listing {listing_id} processed in {final_state['processing_time_seconds']}s"
    )
    
    return final_state

def search_properties(query: str, filters: dict = None, history: list = None, clip_embedder = None) -> QueryState:
    """
    Run full search pipeline for a user searching for properties.
    Initializes a new QueryState and passes it through the LangGraph workflow.
    """
    initial_state = QueryState(
        raw_query=query,
        parsed_intent={},
        clip_query_vector=None,
        filters=filters or {},
        raw_results=[],
        reranked_results=[],
        match_explanations={},
        total_found=0,
        search_time_ms=None,
        conversation_history=history or [],
        error=None
    )
    
    start = time.time()
    
    # Ensure the search agent has the correct embedder
    if clip_embedder:
        get_search_agent(clip_embedder)
        
    graph = get_search_graph()
    
    # Process through the compiled graph
    final_state = graph.invoke(initial_state)
    
    # Calculate execution time in ms
    final_state["search_time_ms"] = round((time.time() - start) * 1000, 2)
    
    return final_state
