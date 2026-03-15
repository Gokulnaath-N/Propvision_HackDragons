
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from src.models.predictor import RoomPredictor
from rich.console import Console
from rich.table import Table

console = Console()

def verify_classifier():
    console.print("[bold blue]Verifying Room Classifier (EfficientNet-B4)[/bold blue]\n")
    
    # Initialize Predictor
    # Defaults: 
    # model_path='models/checkpoints/best_model.pth'
    # labels_path='models/room_classifier/class_labels.json'
    predictor = RoomPredictor()
    
    # Sample images to check
    test_cases = [
        ("kitchen", "data/processed/train/kitchen/kitchen_train_00000.jpg"),
        ("hall", "data/processed/train/hall/hall_train_00000.jpg"),
        ("bedroom", "data/processed/train/bedroom/bedroom_train_00000.jpg")
    ]
    
    table = Table(title="Classifier Verification Results")
    table.add_column("Actual Class", style="cyan")
    table.add_column("Predicted Class", style="magenta")
    table.add_column("Confidence", style="green")
    table.add_column("Status", style="bold")
    
    for actual, img_path in test_cases:
        path = Path(img_path)
        if not path.exists():
            # Try to find any image in that directory if the specific one doesn't exist
            cat_dir = Path("data/processed/train") / actual
            if cat_dir.exists():
                images = list(cat_dir.glob("*.jpg"))
                if images:
                    path = images[0]
                else:
                    console.print(f"[red]No images found in {cat_dir}[/red]")
                    continue
            else:
                console.print(f"[red]Directory {cat_dir} not found[/red]")
                continue
                
        try:
            result = predictor.predict(str(path))
            
            p_class = result["predicted_class"]
            conf = result["confidence"]
            
            status = "[green]MATCH[/green]" if p_class.lower() == actual.lower() else "[red]MISMATCH[/red]"
            
            table.add_row(
                actual,
                p_class,
                f"{conf:.2%}",
                status
            )
        except Exception as e:
            console.print(f"[red]Error predicting {path}: {e}[/red]")
            
    console.print(table)
    console.print("\n[bold green]Verification complete![/bold green]")

if __name__ == "__main__":
    verify_classifier()
