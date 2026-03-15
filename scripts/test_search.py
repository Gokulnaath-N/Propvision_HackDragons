
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from src.search.searcher import PropertySearcher
from src.utils.logger import get_logger

def main():
    console = Console()
    logger = get_logger(__name__)
    
    console.print(Panel.fit("Phase 9: Semantic Search API Test", style="bold magenta"))
    
    try:
        # STEP 1: INITIALIZE SEARCHER
        console.print("[yellow]Initializing PropertySearcher...[/yellow]")
        searcher = PropertySearcher()
        console.print("[green]✓ Searcher ready[/green]\n")
        
        # STEP 2: TEST CASE 1 - Natural Language Query
        query1 = "modern kitchen with white cabinets"
        console.print(f"[bold cyan]Test Case 1: Semantic Query[/bold cyan]")
        console.print(f"Query: '{query1}'")
        
        results1 = searcher.search(query1, top_k=5)
        display_results(console, results1)
        
        # STEP 3: TEST CASE 2 - Filtered Semantic Search
        query2 = "comfortable bedroom interior"
        filters2 = {"city": "Chennai", "price_max": 9000000.0}
        console.print(f"\n[bold cyan]Test Case 2: Filtered Semantic Query[/bold cyan]")
        console.print(f"Query: '{query2}'")
        console.print(f"Filters: {filters2}")
        
        results2 = searcher.search(query2, filters=filters2, top_k=5)
        display_results(console, results2)
        
        # STEP 4: TEST CASE 3 - Room Shortcut
        console.print(f"\n[bold cyan]Test Case 3: Room Shortcut Search[/bold cyan]")
        console.print(f"Action: search_by_room('bathroom')")
        
        results3 = searcher.search_by_room("bathroom")
        display_results(console, results3)

        console.print(Panel("Semantic Search Phase 9: ALL TESTS PASSED", style="bold green"))
        
    except Exception as e:
        console.print(f"\n[bold red]Search Test Failed:[/bold red] {e}")
        import traceback
        traceback.print_exc()

def display_results(console, response):
    table = Table(title=f"Search Results (Total: {response['total_found']})")
    table.add_column("Score", style="bold yellow", justify="right")
    table.add_column("Listing ID", style="cyan")
    table.add_column("Room", style="green")
    table.add_column("City", style="white")
    table.add_column("Price", style="magenta", justify="right")
    table.add_column("Grade", style="bold blue")
    
    for res in response["results"]:
        table.add_row(
            f"{res['match_score']:.4f}",
            res["listing_id"],
            res["room_type"],
            res["city"],
            f"₹{res['price']:,.0f}",
            res["quality_grade"]
        )
    
    console.print(table)

if __name__ == "__main__":
    main()
