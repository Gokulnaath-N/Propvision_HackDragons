
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from src.models.predictor import RoomPredictor
from rich.console import Console
from rich.panel import Panel

console = Console()

def predict_user_image(image_path):
    path = Path(image_path)
    if not path.exists():
        console.print(f"[bold red]Error: Image not found at {path}[/bold red]")
        return

    console.print(f"[bold blue]Inference for:[/bold blue] {path.name}\n")
    
    try:
        predictor = RoomPredictor()
        result = predictor.predict(str(path))
        
        p_class = result["predicted_class"]
        conf = result["confidence"]
        all_probs = result["all_probabilities"]
        
        # Format Top 3
        top_3 = list(all_probs.items())[:3]
        top_str = "\n".join([f"• {k}: {v:.2%}" for k, v in top_3])
        
        panel_content = (
            f"[bold cyan]AI Prediction:[/bold cyan] [bold green]{p_class.upper()}[/bold green]\n"
            f"[bold cyan]Confidence:[/bold cyan] [bold yellow]{conf:.2%}[/bold yellow]\n\n"
            f"[bold white]Top 3 Probabilities:[/bold white]\n{top_str}"
        )
        
        console.print(Panel(panel_content, title="PropVision AI Analysis", expand=False))
        
    except Exception as e:
        console.print(f"[bold red]Inference failed:[/bold red] {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        img_path = sys.argv[1]
    else:
        img_path = "image.png"
    predict_user_image(img_path)
