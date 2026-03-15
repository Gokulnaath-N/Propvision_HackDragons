import os
import uuid
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, String, Integer,
    Float, Boolean, DateTime, Text, JSON,
    ForeignKey
)
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from src.utils.logger import get_logger

load_dotenv()

Base = declarative_base()
logger = get_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./propvision.db")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(String, default="user") # "user" or "broker"
    phone = Column(String, nullable=True)
    city = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Listing(Base):
    __tablename__ = "listings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    broker_id = Column(String, ForeignKey("users.id"))
    city = Column(String, index=True)
    location = Column(String)
    price = Column(Float)
    bhk = Column(Integer)
    vastu_compliant = Column(Boolean, default=False)
    
    hero_image_path = Column(String, nullable=True)
    gallery_paths = Column(JSON, nullable=True)
    overall_grade = Column(String, nullable=True)
    listing_summary = Column(Text, nullable=True)
    room_classifications = Column(JSON, nullable=True)
    spatial_analyses = Column(JSON, nullable=True)
    action_items = Column(JSON, nullable=True)
    
    status = Column(String, default="pending") # "pending","processing","complete","failed"
    indexed_in_qdrant = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SearchHistory(Base):
    __tablename__ = "search_history"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=True) # null for anonymous
    query = Column(String)
    parsed_intent = Column(JSON)
    results_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

def get_db():
    """
    Yields database session.
    Used as FastAPI dependency.
    Closes session after request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all tables in the Supabase PostgreSQL database."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

def get_user_by_email(db, email):
    """Retrieve user by email."""
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db, user_id):
    """Retrieve user by ID."""
    return db.query(User).filter(User.id == user_id).first()

def create_user(db, email, password_hash, full_name, role="user") -> User:
    """Create a new user."""
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        password_hash=password_hash,
        full_name=full_name,
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def save_listing(db, listing_data: dict) -> Listing:
    """Save a new property listing."""
    if "id" not in listing_data:
        listing_data["id"] = str(uuid.uuid4())
        
    listing = Listing(**listing_data)
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing
