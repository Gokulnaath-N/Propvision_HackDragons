import os
import sys
import random
import time
import torch
import cv2
import numpy as np
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from PIL import Image, ImageDraw, ImageFont
from rich.console import Console
from rich.table import Table
from rich.live import Live

from src.enhancement.preprocessor import ImagePreprocessor
from src.enhancement.realesrgan import RealESRGANEnhancer
from src.enhancement.postprocessor import ImagePostprocessor
from src.enhancement.quality_gate import QualityGate
from src.utils.logger import get_logger
from src.utils.gpu_utils import get_device

logger = get_logger(__name__)
console = Console()

def get_random_test_images(base_dir, categories=["bathroom", "kitchen", "bedroom"]):
    """Pick one random image from each category."""
    base_path = Path(base_dir)
    selected = []
    
    for cat in categories:
        cat_dir = base_path / cat
        if not cat_dir.exists():
            logger.warning(f"Category directory {cat_dir} does not exist.")
            continue
            
        images = list(cat_dir.glob("*.jpg")) + list(cat_dir.glob("*.png")) + list(cat_dir.glob("*.jpeg"))
        if not images:
            logger.warning(f"No images found in {cat_dir}")
            continue
            
        selected.append((cat, random.choice(images)))
        
    return selected

def create_comparison(original_path, hero_path, output_path, title="Comparison"):
    """Create a side-by-side image comparison."""
    orig = Image.open(original_path).convert("RGB")
    hero = Image.open(hero_path).convert("RGB")
    
    # Resize original to match hero height for comparison
    h = hero.height
    w = int(orig.width * (h / orig.height))
    orig_resized = orig.resize((w, h), Image.LANCZOS)
    
    # Combined width
    combined_w = w + hero.width + 10
    combined = Image.new("RGB", (combined_w, h + 60), (30, 30, 30))
    
    # Paste images
    combined.paste(orig_resized, (0, 0))
    combined.paste(hero, (w + 10, 0))
    
    # Add Text (Simple)
    draw = ImageDraw.Draw(combined)
    draw.text((10, h + 20), f"BEFORE: {orig.width}x{orig.height}", fill=(255, 255, 255))
    draw.text((w + 20, h + 20), f"AFTER (AI ENHANCED): {hero.width}x{hero.height}", fill=(0, 255, 0))
    draw.text((combined_w // 2 - 50, h + 40), title.upper(), fill=(255, 255, 0))
    
    combined.save(output_path)
    return combined

def run_test():
    console.print("[bold blue]🚀 Starting End-to-End Enhancement Pipeline Test[/bold blue]\n")
    
    # Initialize Pipeline
    console.print("Initializing components...")
    preprocessor = ImagePreprocessor()
    enhancer = RealESRGANEnhancer()
    postprocessor = ImagePostprocessor()
    gate = QualityGate()
    
    test_data_dir = "data/processed/test"
    test_images = get_random_test_images(test_data_dir)
    
    if not test_images:
        console.print("[bold red]Error: No test images found in data/processed/test/[/bold red]")
        return
    
    table = Table(title="Enhancement Pipeline Results")
    table.add_column("Category", style="cyan")
    table.add_column("Input Size", style="magenta")
    table.add_column("Output Size", style="magenta")
    table.add_column("Sharpness", style="green")
    table.add_column("Time (s)", style="yellow")
    table.add_column("Grade", style="bold")
    
    results_list = []
    comparisons = []
    failed_count = 0
    
    for idx, (cat, img_path) in enumerate(test_images):
        console.print(f"Testing [bold cyan]{cat}[/bold cyan]: {img_path.name}")
        start_time = time.time()
        
        try:
            # 1. Preprocess
            pre_pil = preprocessor.preprocess_to_pil(img_path)
            orig_size = f"{pre_pil.width}x{pre_pil.height}"
            
            # 2. Enhance
            enhanced_pil = enhancer.enhance(pre_pil)
            
            # 3. Postprocess
            listing_id = f"test_listing_{cat}"
            paths = postprocessor.postprocess(enhanced_pil, listing_id, idx)
            
            # 4. Quality Gate
            res = gate.check(paths["hero"])
            
            duration = time.time() - start_time
            
            # Table Data
            grade_style = "green" if res["passed"] else "red"
            table.add_row(
                cat,
                orig_size,
                f"{res['resolution'][0]}x{res['resolution'][1]}",
                f"{res['sharpness_score']:.1f}",
                f"{duration:.2f}",
                f"[{grade_style}]{res['grade']}[/{grade_style}]"
            )
            
            if not res["passed"]:
                failed_count += 1
                
            # Create comparison for logs
            comp_path = Path(f"logs/comp_{cat}.jpg")
            comp_path.parent.mkdir(parents=True, exist_ok=True)
            comparison_img = create_comparison(img_path, paths["hero"], comp_path, title=f"Property: {cat}")
            comparisons.append(comparison_img)
            
        except Exception as e:
            console.print(f"[bold red]Failed to process {cat}: {e}[/bold red]")
            table.add_row(cat, "ERROR", "-", "-", "-", "[red]FAIL[/red]")
            failed_count += 1

    # Final side-by-side montage
    if comparisons:
        # Stack vertical
        total_h = sum(c.height for c in comparisons)
        max_w = max(c.width for c in comparisons)
        montage = Image.new("RGB", (max_w, total_h), (50, 50, 50))
        y_off = 0
        for c in comparisons:
            montage.paste(c, (0, y_off))
            y_off += c.height
        
        montage_path = Path("logs/enhancement_test.jpg")
        montage.save(montage_path)
        console.print(f"\n[bold green]Final comparison saved to {montage_path}[/bold green]")

    console.print("\n")
    console.print(table)
    
    if failed_count == 0:
        console.print("\n[bold green]✅ Enhancement pipeline test PASSED[/bold green]")
    else:
        console.print(f"\n[bold yellow]⚠️ WARNING: {failed_count} images failed quality gate[/bold yellow]")

if __name__ == "__main__":
    # Ensure correct PYTHONPATH for internal imports
    run_test()
