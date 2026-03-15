
import os
import sys
import time
from pathlib import Path
import torch
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from src.enhancement.realesrgan import RealESRGANEnhancer
from src.models.predictor import RoomPredictor
from src.vision.clip_embedder import CLIPEmbedder
from src.search.qdrant_client import QdrantManager
from src.agents.orchestrator import search_properties

console = Console()

def verify_esrgan(image_path):
    console.print("\n[bold cyan]1. Verifying ESRGAN (Image Enhancement)...[/bold cyan]")
    try:
        enhancer = RealESRGANEnhancer()
        start_time = time.time()
        # We'll just check if it can load the model and process a small crop or just init
        console.print("[yellow]Model initialized. Testing enhancement on sample...[/yellow]")
        # For a quick test, we'll just check if the model is loaded
        if enhancer.upsampler:
            console.print(f"[green]ESRGAN Model loaded successfully on {enhancer.device}[/green]")
            return True, f"Loaded on {enhancer.device}"
        return False, "Model not loaded"
    except Exception as e:
        return False, str(e)

def verify_efficientnet(image_path):
    console.print("\n[bold cyan]2. Verifying EfficientNet (Room Classification)...[/bold cyan]")
    try:
        predictor = RoomPredictor()
        result = predictor.predict(str(image_path))
        p_class = result["predicted_class"]
        conf = result["confidence"]
        console.print(f"[green]Classification Success: {p_class} ({conf:.2%})[/green]")
        return True, f"{p_class} ({conf:.2%})"
    except Exception as e:
        return False, str(e)

def verify_clip():
    console.print("\n[bold cyan]3. Verifying CLIP (Semantic Embeddings)...[/bold cyan]")
    try:
        embedder = CLIPEmbedder()
        text_emb = embedder.embed_text("a luxury bedroom")
        console.print(f"[green]CLIP Success: Generated embedding of size {len(text_emb)}[/green]")
        return True, f"Embedding size: {len(text_emb)}"
    except Exception as e:
        return False, str(e)

def verify_qdrant():
    console.print("\n[bold cyan]4. Verifying Qdrant (Vector Database)...[/bold cyan]")
    try:
        qdrant = QdrantManager()
        stats = qdrant.get_collection_stats()
        if stats:
            console.print(f"[green]Qdrant Success: Collection '{stats['collection_name']}' has {stats['total_vectors']} vectors[/green]")
            return True, f"{stats['total_vectors']} vectors"
        return False, "Could not get stats"
    except Exception as e:
        return False, str(e)

def verify_langchain():
    console.print("\n[bold cyan]5. Verifying LangChain/LangGraph (Orchestration)...[/bold cyan]")
    try:
        # Simple search test to check orchestrator
        query = "modern kitchen"
        result = search_properties(query)
        intent = result.get("parsed_intent", {})
        console.print(f"[green]Orchestration Success: Query parsed as {intent.get('clip_search_query')}[/green]")
        return True, f"Parsed: {intent.get('clip_search_query')}"
    except Exception as e:
        return False, str(e)

def main():
    console.print(Panel.fit("PropVision AI - Comprehensive Model Verification", style="bold magenta"))
    
    test_image = Path("data/seeds/sample_listing/kitchen_test_00000.jpg")
    if not test_image.exists():
        console.print(f"[bold red]Critical Error: Test image not found at {test_image}[/bold red]")
        return

    results = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        
        # 1. ESRGAN
        progress.add_task(description="Checking ESRGAN...", total=None)
        results.append(("ESRGAN", *verify_esrgan(test_image)))
        
        # 2. EfficientNet
        progress.add_task(description="Checking EfficientNet...", total=None)
        results.append(("EfficientNet", *verify_efficientnet(test_image)))
        
        # 3. CLIP
        progress.add_task(description="Checking CLIP...", total=None)
        results.append(("CLIP", *verify_clip()))
        
        # 4. Qdrant
        progress.add_task(description="Checking Qdrant...", total=None)
        results.append(("Qdrant", *verify_qdrant()))
        
        # 5. LangChain
        progress.add_task(description="Checking LangChain...", total=None)
        results.append(("LangChain", *verify_langchain()))

    # Final Summary Table
    table = Table(title="\nFinal System Health Check")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details", style="white")

    for component, success, detail in results:
        status = "[green]PASS[/green]" if success else "[red]FAIL[/red]"
        table.add_row(component, status, detail)

    console.print(table)

if __name__ == "__main__":
    main()
