import os
import sys
import time
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure project root is on path for relative imports
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from src.utils.logger import get_logger
from dotenv import load_dotenv

load_dotenv()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler for startup and shutdown events."""
    logger.info("PropVision AI starting up...")
    start = time.time()
    
    # STEP 1 — Create DB tables
    try:
        from api.database import create_tables
        create_tables()
        logger.info("Database tables ready")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
    
    # STEP 2 — Create Qdrant collection
    try:
        from src.search.qdrant_client import QdrantManager
        qdrant = QdrantManager()
        qdrant.create_collection()
        logger.info("Qdrant collection ready")
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant: {e}")
    
    # STEP 3 — Pre-load models into memory
    try:
        from src.models.predictor import RoomPredictor
        app.state.predictor = RoomPredictor()
        logger.info("Room classifier loaded")
    except Exception as e:
        logger.warning(f"Room classifier not loaded: {e}")
        app.state.predictor = None
      
    try:
        from src.vision.clip_embedder import CLIPEmbedder
        app.state.clip = CLIPEmbedder()
        logger.info("CLIP embedder loaded")
    except Exception as e:
        logger.warning(f"CLIP not loaded: {e}")
        app.state.clip = None
    
    elapsed = round(time.time() - start, 2)
    logger.info(f"Startup complete in {elapsed}s")
    logger.info("PropVision AI ready to serve requests")
    
    yield
    
    logger.info("PropVision AI shutting down...")

app = FastAPI(
    title="PropVision AI",
    description="AI-powered property search platform",
    version="0.1.0",
    lifespan=lifespan
)

# CORS MIDDLEWARE
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# MOUNT STATIC FILES
data_enhanced = Path("data/enhanced")
if data_enhanced.exists():
    app.mount("/enhanced", StaticFiles(directory="data/enhanced"), name="enhanced")

data_seeds = Path("data/seeds")
if data_seeds.exists():
    app.mount("/seeds", StaticFiles(directory="data/seeds"), name="seeds")

# INCLUDE ALL ROUTERS
from api.routes.auth import router as auth_router
from api.routes.search import router as search_router
from api.routes.upload import router as upload_router
from api.routes.listings import router as listings_router
from api.routes.status import router as status_router
from api.routes.health import router as health_router
from api.routes.history import router as history_router
from api.routes.listings import properties_router

app.include_router(auth_router)
app.include_router(search_router)
app.include_router(upload_router)
app.include_router(listings_router)
app.include_router(status_router)
app.include_router(health_router)
app.include_router(history_router)
app.include_router(properties_router)

@app.get("/debug/env")
async def debug_env():
    import sys
    import transformers
    torch_available = False
    torch_version = "N/A"
    try:
        import torch
        torch_available = True
        torch_version = torch.__version__
    except Exception as e:
        torch_version = f"Error: {e}"
        
    return {
        "python_version": sys.version,
        "sys_path": sys.path,
        "transformers_version": transformers.__version__,
        "is_torch_available_transformers": transformers.utils.is_torch_available(),
        "torch_available_direct": torch_available,
        "torch_version": torch_version,
        "cwd": os.getcwd()
    }

@app.get("/")
async def root():
    return {
        "name": "PropVision AI",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs"
    }

@app.exception_handler(Exception)
async def global_handler(request, exc):
    logger.error(f"Unhandled error at {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
