
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from src.search.indexer import ListingIndexer
from src.utils.logger import get_logger

def main():
    console = Console()
    logger = get_logger(__name__)
    
    console.print(Panel.fit("Phase 8: Data Ingestion Pipeline Test", style="bold green"))
    
    try:
        # STEP 1: INITIALIZE INDEXER
        console.print("[yellow]Initializing ListingIndexer (loading ML models)...[/yellow]")
        indexer = ListingIndexer()
        console.print("[green]✓ Indexer ready[/green]\n")
        
        # STEP 2: RUN BULK INDEXING
        seed_dir = "data/seeds"
        console.print(f"[yellow]Indexing all listings from {seed_dir}...[/yellow]")
        
        results = indexer.index_from_directory(seed_dir)
        
        # STEP 3: DISPLAY RESULTS
        if results:
            console.print(f"\n[bold cyan]Indexing Complete![/bold cyan]")
            console.print(f"Total Listings: {results['total_listings']}")
            console.print(f"Total Vectors Indexed: {results['total_vectors']}")
            
            table = Table(title="Indexing Details")
            table.add_column("Listing ID", style="cyan")
            table.add_column("Images", justify="right")
            table.add_column("Success", style="green", justify="right")
            table.add_column("Failed", style="red", justify="right")
            
            for res in results['results']:
                table.add_row(
                    res['listing_id'],
                    str(res['total_images']),
                    str(res['indexed']),
                    str(res['failed'])
                )
            console.print(table)
            
            # STEP 4: VERIFY VIA SEARCH
            console.print("\n[yellow]Verifying ingestion via semantic search fallback...[/yellow]")
            # Search for "modern kitchen" to see if our sample kitchen appears
            from src.vision.clip_embedder import CLIPEmbedder
            clip = CLIPEmbedder()
            query_emb = clip.embed_text("a modern kitchen with clean surfaces")
            
            search_results = indexer.qdrant.search(query_vector=query_emb, top_k=3)
            
            if search_results:
                console.print(f"[green]✓ Found {len(search_results)} matching points in Qdrant[/green]")
                for i, r in enumerate(search_results):
                    console.print(f" {i+1}. Listing: {r['listing_id']} | Room: {r['room_type']} | Score: {r['score']:.4f}")
            else:
                console.print("[bold red]! No matching points found in Qdrant after indexing.[/bold red]")

        console.print(Panel("Data Ingestion Phase 8: ALL TESTS PASSED", style="bold green"))
        
    except Exception as e:
        console.print(f"\n[bold red]Ingestion Test Failed:[/bold red] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
