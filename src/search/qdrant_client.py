import os
import uuid
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, Range, MatchValue,
    HnswConfigDiff, OptimizersConfigDiff,
    PayloadSchemaType
)
from dotenv import load_dotenv
from src.utils.logger import get_logger
from src.utils.exceptions import QdrantConnectionError

load_dotenv()

class QdrantManager:
    """
    Manage Qdrant vector database connection, collection
    setup, and core operations. Stores CLIP embeddings of
    all property images with metadata for filtered search.
    """
    COLLECTION_NAME = "propvision_images"
    VECTOR_SIZE = 512
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.client = None
        self._connect()

    def _connect(self):
        """
        Initialize connection to Qdrant Cloud.
        """
        try:
            url = os.getenv("QDRANT_URL")
            api_key = os.getenv("QDRANT_API_KEY")
            
            if not url or not api_key:
                raise ValueError("QDRANT_URL or QDRANT_API_KEY not found in .env")
                
            self.client = QdrantClient(
                url=url,
                api_key=api_key,
                timeout=30
            )
            
            # Verify connection
            self.client.get_collections()
            
            self.logger.info("Connected to Qdrant Cloud successfully")
            self.logger.info(f"Collection name: {self.COLLECTION_NAME}")
            
        except Exception as e:
            msg = f"Qdrant connection failed: {e}"
            self.logger.error(msg)
            raise QdrantConnectionError(msg)

    def create_collection(self):
        """
        Create collection if it does not exist and setup payload indexing.
        """
        try:
            existing = self.client.get_collections()
            names = [c.name for c in existing.collections]
            
            if self.COLLECTION_NAME in names:
                self.logger.info("Collection already exists, skipping creation")
                return
            
            self.logger.info(f"Creating collection: {self.COLLECTION_NAME}")
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE
                ),
                hnsw_config=HnswConfigDiff(
                    m=16,
                    ef_construct=100,
                    full_scan_threshold=10000
                )
            )
            
            # CREATE PAYLOAD INDEXES for fast filtering
            payload_indexes = {
                "listing_id": PayloadSchemaType.KEYWORD,
                "room_type": PayloadSchemaType.KEYWORD,
                "city": PayloadSchemaType.KEYWORD,
                "quality_grade": PayloadSchemaType.KEYWORD,
                "bhk": PayloadSchemaType.INTEGER,
                "price": PayloadSchemaType.FLOAT,
                "vastu": PayloadSchemaType.BOOL
            }
            
            for field_name, schema_type in payload_indexes.items():
                self.logger.info(f"Creating payload index for: {field_name}")
                self.client.create_payload_index(
                    collection_name=self.COLLECTION_NAME,
                    field_name=field_name,
                    field_schema=schema_type
                )
            
            self.logger.info("Collection created with all payload indexes")
            
        except Exception as e:
            self.logger.error(f"Failed to setup collection: {e}")
            raise

    def upsert_point(self, point_id, embedding, payload) -> bool:
        """
        Store single embedding with metadata.
        """
        try:
            # Ensure embedding is a list
            vector = embedding.tolist() if hasattr(embedding, "tolist") else list(embedding)
            
            self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=[
                    PointStruct(
                        id=str(point_id),
                        vector=vector,
                        payload=payload
                    )
                ]
            )
            return True
        except Exception as e:
            self.logger.error(f"Point upsert failed: {e}")
            return False

    def upsert_batch(self, points_data: List[Dict]) -> Dict:
        """
        Store multiple embeddings efficiently.
        points_data is list of dicts with: id, embedding, payload
        """
        try:
            point_structs = []
            for item in points_data:
                vector = item["embedding"].tolist() if hasattr(item["embedding"], "tolist") else list(item["embedding"])
                point_structs.append(
                    PointStruct(
                        id=str(item["id"]),
                        vector=vector,
                        payload=item["payload"]
                    )
                )
            
            self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=point_structs,
                wait=True
            )
            
            self.logger.info(f"Upserted {len(point_structs)} points")
            return {"success_count": len(point_structs), "failed_count": 0}
            
        except Exception as e:
            self.logger.error(f"Batch upsert failed: {e}")
            return {"success_count": 0, "failed_count": len(points_data)}

    def search(self, query_vector, filters: Optional[Dict] = None, top_k: int = 20) -> List[Dict]:
        """
        Find most similar images to query vector.
        """
        # BUILD QDRANT FILTER
        conditions = []
        if filters:
            if filters.get("city"):
                conditions.append(FieldCondition(key="city", match=MatchValue(value=filters["city"])))
            if filters.get("bhk"):
                conditions.append(FieldCondition(key="bhk", match=MatchValue(value=filters["bhk"])))
            if filters.get("price_max"):
                conditions.append(FieldCondition(key="price", range=Range(lte=filters["price_max"])))
            if filters.get("price_min"):
                conditions.append(FieldCondition(key="price", range=Range(gte=filters["price_min"])))
            if filters.get("vastu") is not None:
                conditions.append(FieldCondition(key="vastu", match=MatchValue(value=filters["vastu"])))
            if filters.get("quality_grade"):
                conditions.append(FieldCondition(key="quality_grade", match=MatchValue(value=filters["quality_grade"])))
        
        qdrant_filter = Filter(must=conditions) if conditions else None
        
        # EXECUTE SEARCH
        vector = query_vector.tolist() if hasattr(query_vector, "tolist") else list(query_vector)
        results = self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=vector,
            query_filter=qdrant_filter,
            limit=top_k,
            with_payload=True,
            with_vectors=False
        ).points
        
        formatted_results = []
        for res in results:
            formatted_results.append({
                "id": res.id,
                "score": res.score,
                "listing_id": res.payload.get("listing_id"),
                "room_type": res.payload.get("room_type"),
                "image_path": res.payload.get("image_path"),
                "quality_grade": res.payload.get("quality_grade"),
                "city": res.payload.get("city"),
                "price": res.payload.get("price"),
                "bhk": res.payload.get("bhk"),
                "vastu": res.payload.get("vastu"),
                "payload": res.payload
            })
            
        return formatted_results

    def delete_listing(self, listing_id: str) -> bool:
        """
        Delete all vectors for a listing.
        """
        try:
            self.client.delete(
                collection_name=self.COLLECTION_NAME,
                points_selector=Filter(
                    must=[FieldCondition(
                        key="listing_id",
                        match=MatchValue(value=listing_id)
                    )]
                )
            )
            self.logger.info(f"Deleted all vectors for listing {listing_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete listing {listing_id}: {e}")
            return False

    def get_collection_stats(self) -> Dict:
        """
        Get collection stats.
        """
        try:
            info = self.client.get_collection(self.COLLECTION_NAME)
            return {
                "total_vectors": info.points_count,
                "collection_name": self.COLLECTION_NAME,
                "vector_size": self.VECTOR_SIZE,
                "status": str(info.status)
            }
        except Exception as e:
            self.logger.error(f"Failed to get collection stats: {e}")
            return {}
