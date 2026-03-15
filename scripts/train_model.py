import torch
import yaml
import json
import argparse
import time
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from src.utils.gpu_utils import get_device, set_optimal_settings, get_gpu_info
from src.utils.logger import get_logger
from src.data.dataloader import get_dataloaders
from src.models.room_classifier import RoomClassifier
from src.models.trainer import RoomClassifierTrainer
from src.models.evaluator import ModelEvaluator

logger = get_logger(__name__)
console = Console()

def main(config_path="configs/model_config.yaml"):
    # STEP 1 — STARTUP
    console.print(Panel.fit("PropVision AI - Model Training Pipeline", style="bold blue"))
    
    logger.info(f"Loading configuration from {config_path}")
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        return

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    # Set up GPU
    set_optimal_settings()
    device = get_device()
    gpu_info = get_gpu_info()
    
    if "cpu_only" in gpu_info:
        console.print("[yellow]Running on CPU only.[/]")
    else:
        console.print(f"[green]Using GPU:[/] {gpu_info.get('gpu_name')} "
                      f"({gpu_info.get('total_vram_gb')} GB VRAM)")

    # STEP 2 — DATA
    console.print("[bold cyan]Step 2: Loading dataset...[/]")
    try:
        train_loader, val_loader, test_loader = get_dataloaders(config_path)
        
        train_size = len(train_loader.dataset)
        val_size = len(val_loader.dataset)
        test_size = len(test_loader.dataset)
        
        class_names = train_loader.dataset.get_class_names()
        num_classes = len(class_names)
        
        console.print(f"  Train: {train_size} | Val: {val_size} | Test: {test_size}")
        console.print(f"  Classes found ({num_classes}): {', '.join(class_names)}")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return

    # STEP 3 — MODEL
    console.print("[bold cyan]Step 3: Creating EfficientNet-B4 model...[/]")
    model_config = config.get("model", {})
    model = RoomClassifier(
        num_classes=num_classes,
        dropout=model_config.get("dropout", 0.3),
        pretrained=model_config.get("pretrained", True)
    )
    model = model.to(device)
    
    summary = model.get_model_summary()
    console.print(f"  Total parameters: {summary['total_parameters']:,}")
    console.print(f"  Trainable parameters: {summary['trainable_parameters']:,}")
    console.print(f"  Model Size: {summary['model_size_mb']:.2f} MB")

    # STEP 4 — TRAINING
    console.print("[bold cyan]Step 4: Starting training...[/]")
    # Estimate time for RTX 4050 based on prompt hint
    console.print("[italic white]Estimated time: ~2-3 hours on RTX 4050[/]")
    
    training_config = config.get("training", {})
    # Inject relevant top-level or nested config for trainer
    trainer_config = {**training_config, **config.get("paths", {})}
    
    trainer = RoomClassifierTrainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        config=trainer_config,
        device=device
    )
    
    start_time = time.time()
    history = trainer.fit()
    elapsed = (time.time() - start_time) / 60
    
    console.print(f"[bold green]Training complete in {elapsed:.2f} minutes.[/]")

    # STEP 5 — EVALUATION
    console.print("[bold cyan]Step 5: Evaluating on test set...[/]")
    
    # Load best saved model for evaluation
    best_model_path = config.get("paths", {}).get("best_model_path", "models/room_classifier/best_model.pth")
    try:
        model = RoomClassifier.load_model(best_model_path, device)
    except Exception as e:
        logger.warning(f"Could not load best model from {best_model_path} for eval, using current state: {e}")

    evaluator = ModelEvaluator(model, test_loader, class_names, device)
    metrics = evaluator.evaluate()
    evaluator.print_report(metrics)
    
    # Save artifacts
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    evaluator.plot_confusion_matrix(metrics, logs_dir / "confusion_matrix.png")
    evaluator.save_metrics(metrics, logs_dir / "test_metrics.json")

    # STEP 6 — SAVE CLASS LABELS
    console.print("[bold cyan]Step 6: Saving class labels...[/]")
    class_labels_path = Path(config.get("paths", {}).get("class_labels_path", "models/room_classifier/class_labels.json"))
    class_labels_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create id_to_name map
    label_map = {str(i): name for i, name in enumerate(class_names)}
    with open(class_labels_path, "w") as f:
        json.dump(label_map, f, indent=4)
    logger.info(f"Class labels saved to {class_labels_path}")

    # STEP 7 — FINAL SUMMARY
    best_val_acc = max(history.get('val_acc', [0]))
    test_acc = metrics.get('overall_accuracy', 0) * 100
    macro_f1 = metrics.get('macro_f1', 0)
    
    final_info = (
        f"Best Val Accuracy: [bold green]{best_val_acc:.2f}%[/]\n"
        f"Test Set Accuracy: [bold green]{test_acc:.2f}%[/]\n"
        f"Macro F1 Score: [bold green]{macro_f1:.4f}[/]\n\n"
        f"Model saved to: {best_model_path}\n"
        f"Training duration: {elapsed:.2f} minutes\n\n"
        "[bold cyan]Ready for next phase: Image Enhancement Pipeline[/]"
    )
    
    console.print(Panel(final_info, title="Training Process Summary", border_style="green"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PropVision AI Model Training")
    parser.add_argument("--config", type=str, default="configs/model_config.yaml", help="Path to config file")
    args = parser.parse_args()
    
    main(args.config)
