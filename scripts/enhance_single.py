
import sys
import os
from pathlib import Path
import cv2

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from src.enhancement.realesrgan import RealESRGANEnhancer
from src.enhancement.postprocessor import ImagePostprocessor
from rich.console import Console

console = Console()

def enhance_user_image(image_path):
    path = Path(image_path)
    if not path.exists():
        console.print(f"[bold red]Error: Image not found at {path}[/bold red]")
        return

    console.print(f"[bold blue]Enhancing:[/bold blue] {path.name}")
    
    try:
        # Initialize components
        enhancer = RealESRGANEnhancer()
        postprocessor = ImagePostprocessor()
        
        # Run enhancement
        console.print("[yellow]Running Real-ESRGAN (4x Upscale)...[/yellow]")
        enhanced_image = enhancer.enhance(str(path))
        
        # Save results
        # We'll save it to a dedicated 'results' folder for easy viewing
        results_dir = Path("data/user_results")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Use postprocessor to generate standard variants (hero, gallery, thumb)
        output_paths = postprocessor.postprocess(enhanced_image, "user_kitchen", 1)
        
        console.print(f"\n[bold green]Enhancement Successful![/bold green]")
        console.print(f"Results saved in: [cyan]{postprocessor.output_base / 'user_kitchen'}[/cyan]")
        for key in ["hero", "gallery", "thumbnail"]:
            if key in output_paths:
                p = output_paths[key]
                console.print(f"• {key.capitalize()}: {Path(p).name}")
            
    except Exception as e:
        console.print(f"[bold red]Enhancement failed:[/bold red] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        img_path = sys.argv[1]
    else:
        img_path = "image.png"
    enhance_user_image(img_path)
