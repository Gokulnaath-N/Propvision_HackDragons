import os
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from tqdm import tqdm
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from src.pipeline.image_pipeline import PropertyPipeline
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DemoSeeder:
    """
    Pre-process all demo listings for a hackathon demo.
    Runs the complete pipeline on the data/seeds/ folder.
    Ensures semantic search vector matching works on real data before presentations.
    """

    def __init__(self):
        self.console = Console()
        self.seeds_dir = Path("data/seeds")
        self.pipeline = PropertyPipeline()

    def create_sample_seeds(self):
        """
        Create structured demo listings from existing unstructured test images
        dynamically. Creates 5 fake demo listings (from Chennai to Hyderabad).
        """
        import shutil
        import random

        listings = [
            {
                "listing_id": "listing_chennai_001",
                "city": "Chennai",
                "location": "Anna Nagar",
                "price": 6500000,
                "bhk": 2,
                "vastu": True,
                "rooms_needed": ["bathroom", "bedroom", "kitchen", "hall"]
            },
            {
                "listing_id": "listing_chennai_002",
                "city": "Chennai",
                "location": "Velachery",
                "price": 8500000,
                "bhk": 3,
                "vastu": False,
                "rooms_needed": ["bathroom", "bedroom", "kitchen", "dining_room"]
            },
            {
                "listing_id": "listing_bangalore_001",
                "city": "Bangalore",
                "location": "Whitefield",
                "price": 9500000,
                "bhk": 3,
                "vastu": True,
                "rooms_needed": ["bathroom", "bedroom", "kitchen", "pooja_room"]
            },
            {
                "listing_id": "listing_mumbai_001",
                "city": "Mumbai",
                "location": "Andheri",
                "price": 12500000,
                "bhk": 2,
                "vastu": False,
                "rooms_needed": ["bathroom", "bedroom", "kitchen", "hall"]
            },
            {
                "listing_id": "listing_hyderabad_001",
                "city": "Hyderabad",
                "location": "Gachibowli",
                "price": 7500000,
                "bhk": 2,
                "vastu": True,
                "rooms_needed": ["bathroom", "bedroom", "kitchen", "dining_room"]
            }
        ]

        for listing in listings:
            listing_id = listing["listing_id"]
            listing_dir = self.seeds_dir / listing_id
            listing_dir.mkdir(parents=True, exist_ok=True)
            
            for room_needed in listing["rooms_needed"]:
                source_dir = Path(f"data/processed/test/{room_needed}")
                
                if source_dir.exists() and source_dir.is_dir():
                    images = list(source_dir.glob("*.jpg")) + list(source_dir.glob("*.jpeg")) + list(source_dir.glob("*.png"))
                    
                    if images:
                        # Grab up to 2 random images for this room type
                        num_to_copy = min(2, len(images))
                        selected_images = random.sample(images, num_to_copy)
                        
                        for img_path in selected_images:
                            dest_path = listing_dir / img_path.name
                            if not dest_path.exists():
                                shutil.copy2(img_path, dest_path)

            # Dump standard property pricing layout info into JSON for the Agents
            metadata_file = listing_dir / "metadata.json"
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "city": listing["city"],
                        "location": listing["location"],
                        "price": listing["price"],
                        "bhk": listing["bhk"],
                        "vastu": listing["vastu"]
                    }, 
                    f, 
                    indent=4
                )
            
            logger.info(f"Created seed dummy property: {listing_id}")

    def seed_all(self) -> dict:
        """
        Locates dynamically generated seeds and subjects them to rigorous pipeline filtering 
        into Qdrant. Returns Rich metrics dashboard for presentation contexts.
        """
        self.console.print(Panel(
            "[bold blue]PropVision AI[/bold blue] - Demo Data Seeder",
            expand=False
        ))

        # Check if seeder workspace exists/populated yet
        if not self.seeds_dir.exists() or not list(self.seeds_dir.iterdir()):
            logger.info("No seeds found, creating sample Indian real estate seeds...")
            self.create_sample_seeds()

        listing_dirs = [d for d in self.seeds_dir.iterdir() if d.is_dir()]

        if not listing_dirs:
            logger.error("No listing folders found in data/seeds/ even after generation step.")
            return {"error": "No listings to seed"}

        logger.info(f"Found {len(listing_dirs)} listings to process")

        results = []
        total_vectors = 0

        for listing_dir in tqdm(listing_dirs, desc="Seeding properties into DB"):
            listing_id = listing_dir.name
            
            image_paths = []
            for ext in ('*.jpg', '*.jpeg', '*.png', '*.webp'):
                image_paths.extend([str(p) for p in listing_dir.rglob(ext)])
                
            if not image_paths:
                logger.warning(f"No images found for {listing_id}. Skipping.")
                continue
                
            metadata_file = listing_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
            else:
                metadata = {
                    "city": "Chennai",
                    "price": 7000000,
                    "bhk": 2,
                    "vastu": False,
                    "location": "Unknown"
                }

            try:
                # Orchestrate execution
                result = self.pipeline.run(
                    listing_id=listing_id,
                    raw_image_paths=image_paths,
                    metadata=metadata
                )
                
                results.append({
                    "listing_id": listing_id,
                    "status": "success",
                    "grade": result.get("overall_grade", "C"),
                    "vectors": result.get("indexed_vectors", 0),
                    "time": result.get("processing_time_seconds", 0)
                })
                total_vectors += result.get("indexed_vectors", 0)
                
            except Exception as e:
                logger.error(f"Failed to seed {listing_id}: {e}")
                results.append({
                    "listing_id": listing_id,
                    "status": "failed",
                    "grade": "N/A",
                    "vectors": 0,
                    "time": 0,
                    "error": str(e)
                })

        # Render presentation metrics using `rich` terminal graphics
        table = Table(title="Seeding Results")
        table.add_column("Listing ID", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Grade", justify="center", style="magenta")
        table.add_column("Vectors", justify="right", style="green")
        table.add_column("Time (s)", justify="right")

        for row in results:
            status_color = "green" if row["status"] == "success" else "red"
            table.add_row(
                row["listing_id"],
                f"[{status_color}]{row['status'].upper()}[/{status_color}]",
                row["grade"],
                str(row["vectors"]),
                f"{row['time']:.2f}"
            )

        self.console.print(table)
        
        successful_count = sum(1 for r in results if r["status"] == "success")
        
        self.console.print(Panel(
            f"[bold green]Seeding complete![/bold green]\n"
            f"Listings successfully processed: {successful_count}/{len(listing_dirs)}\n"
            f"Total multimodal visual vectors pushed to Qdrant: {total_vectors}",
            expand=False
        ))

        return {
            "total_listings": len(listing_dirs),
            "successful": successful_count,
            "total_vectors": total_vectors,
            "results": results
        }


if __name__ == "__main__":
    seeder = DemoSeeder()
    seeder.seed_all()
