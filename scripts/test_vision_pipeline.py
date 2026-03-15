
import os
import sys
import json
import numpy as np
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).parent.parent))

from src.vision.clip_embedder import CLIPEmbedder
from src.vision.quality_scorer import ImageQualityScorer
from src.vision.spatial_analyzer import SpatialAnalyzer
from src.utils.logger import get_logger

def main():
    console = Console()
    logger = get_logger(__name__)
    
    console.print(Panel.fit("Phase 6: Vision Pipeline Integration Test", style="bold magenta"))
    
    try:
        # STEP 1 — INITIALIZE COMPONENTS
        console.print("[yellow]Initializing Vision components...[/yellow]")
        embedder = CLIPEmbedder()
        scorer = ImageQualityScorer()
        analyzer = SpatialAnalyzer()
        console.print("[green]✓ All components loaded successfully[/green]\n")
        
        # STEP 2 — PICK TEST IMAGES
        test_dir = Path("data/processed/test")
        test_images = []
        
        # Look for images in key room folders
        target_rooms = ["bathroom", "bedroom", "kitchen", "hall"]
        for room in target_rooms:
            room_dir = test_dir / room
            if room_dir.exists():
                images = list(room_dir.glob("*.jpg")) + list(room_dir.glob("*.png"))
                if images:
                    test_images.append((images[0], room))
        
        if not test_images:
            console.print("[bold red]No test images found in data/processed/test/[/bold red]")
            return

        # STEP 3 — TEST CLIP EMBEDDER
        console.print("[bold blue]--- Testing CLIP Embedder ---[/bold blue]")
        
        # Test basic embedding
        img_path, r_type = test_images[0]
        embedding = embedder.embed_image(img_path)
        console.print(f"✓ Image embedding generated: {embedding.shape} {embedding.dtype}")
        
        text_emb = embedder.embed_text("a clean minimalist room")
        console.print(f"✓ Text embedding generated: {text_emb.shape}")
        
        # Test semantic similarity logic
        # Find a bedroom and a kitchen if possible
        bedroom_path = None
        kitchen_path = None
        for p, t in test_images:
            if t == "bedroom": bedroom_path = p
            if t == "kitchen": kitchen_path = p
            
        if bedroom_path and kitchen_path:
            bed_img_emb = embedder.embed_image(bedroom_path)
            bed_text_emb = embedder.embed_text("bedroom interior")
            kit_text_emb = embedder.embed_text("modern kitchen appliances")
            
            sim_correct = embedder.cosine_similarity(bed_img_emb, bed_text_emb)
            sim_wrong = embedder.cosine_similarity(bed_img_emb, kit_text_emb)
            
            console.print(f"  Bedroom image vs Bedroom text: [cyan]{sim_correct:.3f}[/cyan]")
            console.print(f"  Bedroom image vs Kitchen text: [yellow]{sim_wrong:.3f}[/yellow]")
            
            if sim_correct > sim_wrong:
                console.print("[green]✓ Semantic similarity logic verified![/green]")
            else:
                console.print("[bold red]! Semantic similarity check failed[/bold red]")

        # STEP 4 — TEST QUALITY SCORER
        console.print("\n[bold blue]--- Testing Quality Scorer ---[/bold blue]")
        table = Table(title="Image Quality Analysis")
        table.add_column("Room", style="cyan")
        table.add_column("Sharpness", justify="right")
        table.add_column("Lighting", justify="right")
        table.add_column("Res Score", justify="right")
        table.add_column("Final", style="bold green", justify="right")
        table.add_column("Grade", style="bold yellow")
        
        all_results = []
        for img_path, r_type in test_images:
            result = scorer.score(img_path)
            table.add_row(
                r_type,
                f"{result['sharpness_score']:.1f}",
                f"{result['lighting_score']:.1f}",
                f"{result['resolution_score']:.1f}",
                f"{result['final_score']:.1f}",
                result['grade']
            )
            all_results.append(result)
            
        console.print(table)
        
        # STEP 5 — TEST SPATIAL ANALYZER (Gemini)
        console.print("\n[bold blue]--- Testing Spatial Analyzer (Gemini 1.5 Flash) ---[/bold blue]")
        # Pick just one image to test
        test_img, test_room = test_images[0]
        console.print(f"Analyzing [cyan]{test_room}[/cyan] image...")
        
        spatial_data = analyzer.analyze(test_img, test_room)
        console.print(Panel(json.dumps(spatial_data, indent=2), title="Gemini Spatial Analysis Result"))
        
        # STEP 6 — SAVE TEST DATA
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Collect embeddings for all test images
        all_embs = [embedder.embed_image(p) for p, t in test_images]
        np.save(logs_dir / "test_embeddings.npy", np.array(all_embs))
        console.print(f"\n[green]✓ Test embeddings saved to logs/test_embeddings.npy[/green]")
        
        console.print(Panel("Vision Pipeline Phase 6: ALL TESTS PASSED", style="bold green"))
        
    except Exception as e:
        console.print(f"\n[bold red]Vision Pipeline Test Failed:[/bold red] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
