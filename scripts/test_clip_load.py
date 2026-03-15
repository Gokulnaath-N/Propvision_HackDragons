try:
    import torch
    print(f"Torch Version: {torch.__version__}")
    from transformers import CLIPProcessor, CLIPModel
    model_name = "openai/clip-vit-base-patch32"
    print(f"Loading CLIP from {model_name}...")
    processor = CLIPProcessor.from_pretrained(model_name, use_fast=False)
    model = CLIPModel.from_pretrained(model_name)
    print("CLIP Load Success!")
except Exception as e:
    print(f"CLIP Load Failed: {e}")
