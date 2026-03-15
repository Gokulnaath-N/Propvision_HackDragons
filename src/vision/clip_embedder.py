import torch
import numpy as np
from PIL import Image
from pathlib import Path
from transformers import CLIPProcessor, CLIPModel
from tqdm import tqdm
from src.utils.logger import get_logger
from src.utils.gpu_utils import get_device, clear_gpu_cache
from src.utils.exceptions import EmbeddingError

logger = get_logger(__name__)

class CLIPEmbedder:
    """
    Generate 512-dimensional semantic embeddings for images
    and text using CLIP. Core of the semantic search system.
    Both image and text embed into the same vector space
    enabling natural language property search.
    """
    def __init__(self):
        self.device = get_device()
        self.model_name = "openai/clip-vit-base-patch32"
        self.embedding_dim = 512
        self.batch_size = 32
        self.model = None
        self.processor = None
        self._load_model()

    def _load_model(self):
        """
        Load the CLIP model and processor from HuggingFace.
        """
        try:
            logger.info(f"Loading CLIP model: {self.model_name}...")
            
            self.processor = CLIPProcessor.from_pretrained(self.model_name, use_fast=False)
            self.model = CLIPModel.from_pretrained(self.model_name)
            self.model = self.model.to(self.device)
            self.model.eval()
            
            logger.info(f"CLIP loaded on {self.device}")
            logger.info(f"Embedding dimension: {self.embedding_dim}")
            
        except Exception as e:
            msg = f"Failed to load CLIP: {e}"
            logger.error(msg)
            raise EmbeddingError(msg)

    def embed_image(self, image_input) -> np.ndarray:
        """
        Convert single image to 512-dim normalized vector.
        Accepts: str (path), Path object, PIL.Image, or np.ndarray (RGB).
        """
        try:
            # Handle multiple input types
            if isinstance(image_input, (str, Path)):
                pil_image = Image.open(image_input).convert("RGB")
            elif isinstance(image_input, Image.Image):
                pil_image = image_input.convert("RGB")
            elif isinstance(image_input, np.ndarray):
                pil_image = Image.fromarray(image_input).convert("RGB")
            else:
                raise ValueError(f"Unsupported image input type: {type(image_input)}")

            # Process through CLIP
            inputs = self.processor(
                images=pil_image,
                return_tensors="pt",
                padding=True
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model.get_image_features(**inputs)
                # Handle cases where model might return a dict/object
                if hasattr(outputs, "image_embeds"):
                    image_features = outputs.image_embeds
                elif hasattr(outputs, "pooler_output"):
                    image_features = outputs.pooler_output
                else:
                    image_features = outputs
            
            # Normalize to unit vector
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            # Convert to numpy
            embedding = image_features.cpu().numpy().flatten()
            return embedding
            
        except Exception as e:
            msg = f"Image embedding failed: {e}"
            logger.error(msg)
            raise EmbeddingError(msg)

    def embed_text(self, text: str) -> np.ndarray:
        """
        Convert text query to 512-dim vector in the same space as images.
        """
        try:
            inputs = self.processor(
                text=[text],
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=77
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model.get_text_features(**inputs)
                # Handle cases where model might return a dict/object
                if hasattr(outputs, "text_embeds"):
                    text_features = outputs.text_embeds
                elif hasattr(outputs, "pooler_output"):
                    text_features = outputs.pooler_output
                else:
                    text_features = outputs
            
            # Normalize to unit vector
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            # Convert to numpy
            embedding = text_features.cpu().numpy().flatten()
            return embedding
            
        except Exception as e:
            msg = f"Text embedding failed: {e}"
            logger.error(msg)
            raise EmbeddingError(msg)

    def embed_images_batch(self, image_paths, desc="Embedding Images"):
        """
        Embed multiple images efficiently in batches.
        """
        all_embeddings = []
        batch_count = 0
        
        # Process in chunks
        for i in tqdm(range(0, len(image_paths), self.batch_size), desc=desc):
            batch_paths = image_paths[i : i + self.batch_size]
            batch_images = []
            
            for path in batch_paths:
                try:
                    img = Image.open(path).convert("RGB")
                    batch_images.append(img)
                except Exception as e:
                    logger.warning(f"Failed to load {path}: {e}")
                    # Skip or add placeholder? Skipping is safer for indexing.
                    continue
            
            if not batch_images:
                continue
                
            try:
                inputs = self.processor(
                    images=batch_images,
                    return_tensors="pt",
                    padding=True
                ).to(self.device)
                
                with torch.no_grad():
                    outputs = self.model.get_image_features(**inputs)
                    # Handle cases where model might return a dict/object
                    if hasattr(outputs, "image_embeds"):
                        features = outputs.image_embeds
                    elif hasattr(outputs, "pooler_output"):
                        features = outputs.pooler_output
                    else:
                        features = outputs
                
                # Normalize batch
                features = features / features.norm(dim=-1, keepdim=True)
                
                # Convert to numpy and collect
                batch_embeddings = features.cpu().numpy()
                all_embeddings.extend(batch_embeddings)
                
                # Periodic memory management
                batch_count += 1
                if batch_count % 5 == 0:
                    clear_gpu_cache()
                    
            except Exception as e:
                logger.error(f"Batch embedding failed at index {i}: {e}")
                
        logger.info(f"Successfully embedded {len(all_embeddings)}/{len(image_paths)} images")
        return all_embeddings

    def cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two normalized vectors.
        Since both are unit vectors, this is just the dot product.
        Value is between -1 and 1 (1 = identical).
        """
        # Ensure single dimension
        e1 = emb1.flatten()
        e2 = emb2.flatten()
        return float(np.dot(e1, e2))

    def get_top_k_similar(self, query_emb: np.ndarray, candidate_embs: list, k=5) -> list:
        """
        Rank candidate embeddings by similarity to query embedding.
        Returns list of (index, similarity_score) tuples sorted by score decending.
        """
        similarities = []
        for i, cand_emb in enumerate(candidate_embs):
            score = self.cosine_similarity(query_emb, cand_emb)
            similarities.append((i, score))
            
        # Sort by score descending
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:k]
