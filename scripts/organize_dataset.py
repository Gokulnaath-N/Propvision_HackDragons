import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

import shutil
import random
import yaml
import json
import argparse
from collections import Counter
from sklearn.model_selection import train_test_split
from tqdm import tqdm
from rich.console import Console
from rich.table import Table
from PIL import Image

from src.utils.logger import get_logger

logger = get_logger("organize_dataset")
console = Console()

# STEP 1 — CLASS NAME MAPPING
CLASS_MAPPING = {
    "Bath_room": "bathroom",
    "Bed_room": "bedroom",
    "Dining_room": "dining_room",
    "Kitchen": "kitchen",
    "Living_room": "hall",
    "Pooja_room": "pooja_room"
}

# STEP 2 — COLLECT ALL IMAGES
def collect_images(source_dir):
    samples = []
    class_counts = Counter()
    source_path = Path(source_dir)
    
    if not source_path.exists():
        logger.error(f"Source directory not found: {source_dir}")
        return samples

    for folder in source_path.iterdir():
        if folder.is_dir() and folder.name in CLASS_MAPPING:
            mapped_class = CLASS_MAPPING[folder.name]
            for file_path in folder.glob("*"):
                if file_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                    samples.append((str(file_path), mapped_class))
                    class_counts[mapped_class] += 1
                    
    for class_name, count in class_counts.items():
        logger.info(f"Class '{class_name}': {count} images found")
        
    return samples

# STEP 3 — VALIDATE IMAGES
def validate_image(image_path) -> bool:
    try:
        # Check file size >= 5KB
        if os.path.getsize(image_path) < 5120:
            return False
            
        # Try to open with PIL
        with Image.open(image_path) as img:
            img.verify()  # verify integrity
            
        # Reopen to get size (verify closes)
        with Image.open(image_path) as img:
            width, height = img.size
            if width < 224 or height < 224:
                return False
                
        return True
    except Exception:
        return False

# STEP 4 — STRATIFIED SPLIT
def split_dataset(samples, val_size=0.15, test_size=0.15):
    paths = [s[0] for s in samples]
    labels = [s[1] for s in samples]
    
    # First split off test set
    paths_tmp, paths_test, labels_tmp, labels_test = train_test_split(
        paths, labels, test_size=test_size, stratify=labels, random_state=42
    )
    
    # Calculate proportion for validation from the remaining
    val_proportion = val_size / (1.0 - test_size)
    paths_train, paths_val, labels_train, labels_val = train_test_split(
        paths_tmp, labels_tmp, test_size=val_proportion, stratify=labels_tmp, random_state=42
    )

    train_samples = list(zip(paths_train, labels_train))
    val_samples = list(zip(paths_val, labels_val))
    test_samples = list(zip(paths_test, labels_test))
    
    return train_samples, val_samples, test_samples

# STEP 5 — COPY TO FINAL FOLDERS
def copy_samples(samples, split_name, dest_base):
    dest_path = Path(dest_base) / split_name
    count = 0
    class_indices = Counter()
    
    for image_path, class_name in tqdm(samples, desc=f"Copying {split_name} samples"):
        class_dir = dest_path / class_name
        class_dir.mkdir(parents=True, exist_ok=True)
        
        index = class_indices[class_name]
        class_indices[class_name] += 1
        
        ext = Path(image_path).suffix
        new_filename = f"{class_name}_{split_name}_{index:05d}{ext}"
        new_filepath = class_dir / new_filename
        
        shutil.copy2(image_path, new_filepath)
        count += 1
        
    return count

# STEP 6 — GENERATE data.yaml
def generate_yaml(class_names, output_path):
    configs_dir = Path("configs")
    configs_dir.mkdir(exist_ok=True)
    
    sorted_names = sorted(class_names)
    
    # Write configs/data.yaml
    data_yaml = {
        "train": "data/processed/train",
        "val": "data/processed/val",
        "test": "data/processed/test",
        "nc": len(sorted_names),
        "names": sorted_names
    }
    
    yaml_path = configs_dir / "data.yaml"
    with open(yaml_path, "w") as f:
        yaml.dump(data_yaml, f, sort_keys=False)
        
    # Write configs/class_labels.json
    labels_json = {i: name for i, name in enumerate(sorted_names)}
    json_path = configs_dir / "class_labels.json"
    with open(json_path, "w") as f:
        json.dump(labels_json, f, indent=4)
        
    logger.info(f"Generated configurations at {yaml_path} and {json_path}")

# STEP 7 — PRINT FINAL REPORT
def print_final_report(train_samples, val_samples, test_samples):
    table = Table(title="Dataset Split Report")
    table.add_column("Class", justify="left", style="cyan", no_wrap=True)
    table.add_column("Train", justify="right", style="green")
    table.add_column("Val", justify="right", style="yellow")
    table.add_column("Test", justify="right", style="red")
    table.add_column("Total", justify="right", style="magenta")
    
    train_counts = Counter([s[1] for s in train_samples])
    val_counts = Counter([s[1] for s in val_samples])
    test_counts = Counter([s[1] for s in test_samples])
    
    classes = sorted(list(set(train_counts.keys()) | set(val_counts.keys()) | set(test_counts.keys())))
    
    total_train = total_val = total_test = total_all = 0
    
    for cls in classes:
        t_c = train_counts[cls]
        v_c = val_counts[cls]
        test_c = test_counts[cls]
        total = t_c + v_c + test_c
        
        total_train += t_c
        total_val += v_c
        total_test += test_c
        total_all += total
        
        table.add_row(cls, str(t_c), str(v_c), str(test_c), str(total))
        
        if total < 100:
            console.print(f"[bold red]WARNING: Class '{cls}' has less than 100 total images ({total}).[/bold red]")
            logger.warning(f"Class '{cls}' has less than 100 total images ({total}).")
            
    table.add_row("TOTAL", str(total_train), str(total_val), str(total_test), str(total_all), style="bold")
    console.print(table)

# STEP 8 — MAIN FUNCTION
def main():
    parser = argparse.ArgumentParser(description="Organize and split dataset")
    parser.add_argument("--source", default="data/raw/roboflow_export/train", help="Source directory")
    parser.add_argument("--dest", default="data/processed", help="Destination base directory")
    args = parser.parse_args()
    
    logger.info("Collecting images...")
    raw_samples = collect_images(args.source)
    if not raw_samples:
        logger.error("No valid images found or source directory missing.")
        return
        
    logger.info("Validating images...")
    valid_samples = []
    skipped = 0
    for sample in tqdm(raw_samples, desc="Validating"):
        if validate_image(sample[0]):
            valid_samples.append(sample)
        else:
            skipped += 1
            
    logger.info(f"Validation complete. Valid: {len(valid_samples)}, Skipped: {skipped}")
    
    if len(valid_samples) == 0:
        logger.error("No valid images remained after validation.")
        return
        
    logger.info("Splitting dataset into stratified sets...")
    train_samples, val_samples, test_samples = split_dataset(valid_samples)
    
    logger.info("Copying samples to destination directories...")
    copy_samples(train_samples, "train", args.dest)
    copy_samples(val_samples, "val", args.dest)
    copy_samples(test_samples, "test", args.dest)
    
    class_names = sorted(list(set([s[1] for s in valid_samples])))
    generate_yaml(class_names, args.dest)
    
    print_final_report(train_samples, val_samples, test_samples)

if __name__ == "__main__":
    main()
