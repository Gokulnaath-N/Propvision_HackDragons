import torch
from src.utils.logger import get_logger

logger = get_logger(__name__)

def get_device() -> torch.device:
    """
    Returns cuda if available else cpu.
    Prints GPU name when cuda is found.
    """
    if torch.cuda.is_available():
        device = torch.device("cuda")
        logger.info(f"CUDA is available. Using GPU: {torch.cuda.get_device_name(0)}")
        return device
    else:
        logger.warning("CUDA is not available. Using CPU.")
        return torch.device("cpu")

def get_gpu_info() -> dict:
    """
    Returns info about the GPU: gpu_name, total_vram_gb, free_vram_gb, cuda_version.
    Returns cpu_only:True if no GPU is found.
    """
    if not torch.cuda.is_available():
        return {"cpu_only": True}
    
    device_id = torch.cuda.current_device()
    gpu_name = torch.cuda.get_device_name(device_id)
    
    # torch.cuda.mem_get_info returns (free(bytes), total(bytes))
    free_vram, total_vram = torch.cuda.mem_get_info(device_id)
    
    return {
        "gpu_name": gpu_name,
        "total_vram_gb": round(total_vram / (1024 ** 3), 2),
        "free_vram_gb": round(free_vram / (1024 ** 3), 2),
        "cuda_version": torch.version.cuda
    }

def clear_gpu_cache():
    """
    Calls torch.cuda.empty_cache() and logs memory cleared.
    """
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        logger.info("GPU cache successfully cleared.")
    else:
        logger.debug("clear_gpu_cache called but CUDA is not available.")

def set_optimal_settings():
    """
    Sets maximum performance settings for RTX series GPUs.
    """
    if torch.cuda.is_available():
        torch.backends.cudnn.benchmark = True
        torch.backends.cuda.matmul.allow_tf32 = True
        logger.info("Optimal GPU settings applied (cudnn.benchmark=True, allow_tf32=True).")
    else:
        logger.debug("set_optimal_settings called but CUDA is not available.")

# Print summary upon import
_info = get_gpu_info()
if _info.get("cpu_only"):
    print("GPU Utils Initialized: Operating in CPU-only mode.")
else:
    print(f"GPU Utils Initialized: Found {_info['gpu_name']} with {_info['total_vram_gb']}GB total VRAM (CUDA {_info['cuda_version']})")
