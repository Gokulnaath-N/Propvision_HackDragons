import torch
from src.utils.logger import get_logger

logger = get_logger("gpu_utils")

def get_device() -> torch.device:
    """Returns the available torch device and logs GPU info."""
    if torch.cuda.is_available():
        device = torch.device("cuda")
        logger.info(f"CUDA is available. Using GPU: {torch.cuda.get_device_name(0)}")
    else:
        device = torch.device("cpu")
        logger.warning("No GPU found. Falling back to CPU.")
    return device


def get_gpu_info() -> dict:
    """Returns a dictionary containing GPU information or CPU fallback info."""
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        total_vram_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
        
        # Calculate free memory: Total minus currently allocated memory
        allocated = torch.cuda.memory_allocated(0)
        free_vram_gb = round((torch.cuda.get_device_properties(0).total_memory - allocated) / (1024**3), 2)
        
        return {
            "gpu_name": gpu_name,
            "total_vram_gb": total_vram_gb,
            "free_vram_gb": free_vram_gb,
            "cuda_version": torch.version.cuda,
            "pytorch_version": torch.__version__
        }
    else:
        return {"cpu_only": True}


def clear_gpu_cache() -> None:
    """Clears PyTorch CUDA cache."""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        logger.info("GPU cache cleared")


def set_optimal_settings() -> None:
    """Applies optimal PyTorch settings for RTX 4050."""
    if torch.cuda.is_available():
        torch.backends.cudnn.benchmark = True
        torch.backends.cuda.matmul.allow_tf32 = True
        logger.info("Optimal GPU settings applied for RTX 4050")

# --- Execute on Import ---
set_optimal_settings()
gpu_info = get_gpu_info()
print("--- GPU Info Summary ---")
for key, value in gpu_info.items():
    print(f"{key}: {value}")
print("------------------------")
