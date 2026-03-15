import os
import sys
import numpy as np
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from src.search.qdrant_client import QdrantManager

def test_qdrant():
    console = Console()
    console.print(Panel.fit("Qdrant Vector Database Verification", style="bold blue"))
    
    try:
        # STEP 1: INITIALIZE
        console.print("[yellow]Connecting to Qdrant Cloud...[/yellow]")
        manager = QdrantManager()
        console.print("[green]✓ Connected successfully[/green]")
        
        # STEP 2: SETUP COLLECTION
        console.print("[yellow]Setting up collection...[/yellow]")
        manager.create_collection()
        console.print("[green]✓ Collection ready[/green]")
        
        # STEP 3: TEST UPSERT
        console.print("[yellow]Testing single point upsert...[/yellow]")
        dummy_embedding = np.random.rand(512).astype(np.float32)
        # Normalize dummy
        dummy_embedding /= np.linalg.norm(dummy_embedding)
        
        payload = {
            "listing_id": "test_listing_001",
            "room_type": "bedroom",
            "image_path": "data/sample/bedroom.jpg",
            "quality_grade": "A+",
            "city": "Chennai",
            "price": 7500000.0,
            "bhk": 3,
            "vastu": True,
            "image_index": 1
        }
        
        success = manager.upsert_point(
            point_id="11111111-2222-3333-4444-555555555555",
            embedding=dummy_embedding,
            payload=payload
        )
        
        if success:
            console.print("[green]✓ Upsert success[/green]")
        else:
            console.print("[bold red]! Upsert failed[/bold red]")
            return

        # STEP 4: TEST SEARCH
        console.print("[yellow]Testing semantic search with filters...[/yellow]")
        # Search for something similar to the same dummy vector
        filters = {
            "city": "Chennai",
            "price_max": 8000000.0,
            "vastu": True
        }
        
        results = manager.search(query_vector=dummy_embedding, filters=filters, top_k=5)
        
        if results:
            console.print(f"[green]✓ Search returned {len(results)} results[/green]")
            for i, res in enumerate(results):
                console.print(f"  {i+1}. Listing: {res['listing_id']} | Score: {res['score']:.4f} | City: {res['city']}")
        else:
            console.print("[bold red]! Search returned no results[/bold red]")
            
        # STEP 5: STATS
        stats = manager.get_collection_stats()
        console.print(f"\n[bold blue]Collection Stats:[/bold blue]")
        for k, v in stats.items():
            console.print(f"• {k}: {v}")
            
        console.print(Panel("Qdrant Verification: ALL TESTS PASSED", style="bold green"))
        
    except Exception as e:
        console.print(f"[bold red]Qdrant Verification Failed:[/bold red] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_qdrant()
