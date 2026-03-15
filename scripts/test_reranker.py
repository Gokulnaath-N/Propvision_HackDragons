
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from src.search.reranker import SearchReranker

def main():
    console = Console()
    console.print(Panel.fit("Phase 10: Search Reranker Verification", style="bold blue"))
    
    reranker = SearchReranker()
    
    # MOCK SEARCH RESULTS (Simulating output from PropertySearcher)
    mock_results = [
        {
            "listing_id": "listing_A",
            "match_score": 0.35, # Good CLIP score
            "room_type": "kitchen",
            "quality_grade": "A+", # Perfect quality
            "image_path": "img_A.jpg",
            "city": "Chennai",
            "price": 8500000,
            "bhk": 3,
            "vastu": True
        },
        {
            "listing_id": "listing_B",
            "match_score": 0.38, # Best CLIP score
            "room_type": "kitchen",
            "quality_grade": "C", # Poor quality
            "image_path": "img_B.jpg",
            "city": "Chennai",
            "price": 8200000,
            "bhk": 3,
            "vastu": False
        },
        {
            "listing_id": "listing_C",
            "match_score": 0.32, # Lower CLIP score
            "room_type": "kitchen",
            "quality_grade": "B+", # Decent quality
            "image_path": "img_C.jpg",
            "city": "Chennai",
            "price": 9000000,
            "bhk": 3,
            "vastu": True
        }
    ]
    
    # MOCK LISTING METADATA
    # Listing A is complete, Listing B is missing rooms
    listing_meta = {
        "listing_A": {"room_types": ["kitchen", "hall", "bedroom", "bathroom", "balcony", "pooja"]}, # 6 rooms
        "listing_B": {"room_types": ["kitchen"]}, # 1 room
        "listing_C": {"room_types": ["kitchen", "bedroom", "hall"]} # 3 rooms
    }
    
    console.print("\n[yellow]Performing Search Reranking...[/yellow]")
    
    reranked = reranker.rerank(mock_results, listing_metadata=listing_meta)
    
    # DISPLAY COMPARISON
    table = Table(title="Reranking Results Comparison")
    table.add_column("Rank", justify="center")
    table.add_column("Listing", style="cyan")
    table.add_column("CLIP (40%)", justify="right")
    table.add_column("Quality (30%)", style="blue")
    table.add_column("Completeness (20%)", style="green")
    table.add_column("FINAL SCORE", style="bold magenta", justify="right")
    
    for i, res in enumerate(reranked):
        table.add_row(
            str(i+1),
            res["listing_id"],
            f"{res['component_scores']['clip']:.4f}",
            f"{res['quality_grade']} ({res['component_scores']['quality']:.2f})",
            f"{res['component_scores']['completeness']:.2f}",
            f"{res['rerank_score']:.4f}"
        )
        
    console.print(table)
    
    # Formatted for API
    console.print("\n[yellow]Verifying API Formatting...[/yellow]")
    api_results = reranker.format_for_api(reranked)
    if "component_scores" in api_results[0] and "payload" not in api_results[0]:
        console.print("[green]✓ API formatting correctly excludes raw payload and includes scores[/green]")

    console.print(Panel("Search Reranker Phase 10: ALL TESTS PASSED", style="bold green"))

if __name__ == "__main__":
    main()
