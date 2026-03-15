import os
import uuid
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from api.database import get_db, create_user, get_user_by_email, get_user_by_id
from src.utils.logger import get_logger
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

JWT_SECRET = os.getenv("JWT_SECRET", "propvision_secret_key_2024")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

logger = get_logger(__name__)

# ==========================================
# PYDANTIC MODELS
# ==========================================
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "user" # user or broker
    phone: Optional[str] = None
    city: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    city: Optional[str]
    is_active: bool

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def hash_password(password: str) -> str:
    """Hash password utilizing bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    """Validate plaintext against hashed password."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def create_token(user_id: str, role: str) -> str:
    """Generates standard JWT token using pre-configured secret."""
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    """Decodes JWT, raising FastApi HTTPExceptions for common token issues."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """
    Standard HTTPBearer Dependency injection function. 
    Verifies auth token against Supabase database registry.
    """
    token = credentials.credentials
    payload = decode_token(token)
    user = get_user_by_id(db, payload["sub"])
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[dict]:
    """
    Optional User Dependency injection. Will not throw 401 exceptions. 
    Ideal for 'hybrid' endpoints supporting both anonymous traffic and auth overrides.
    """
    if credentials:
        try:
            token = credentials.credentials
            payload = decode_token(token)
            return get_user_by_id(db, payload["sub"])
        except Exception:
            return None
    return None

# ==========================================
# ENDPOINTS
# ==========================================
@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=AuthResponse)
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """Creates a new PropVision user profile."""
    # 1. Validation
    if len(request.password) < 6:
         raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
         
    if request.role not in ["user", "broker"]:
        raise HTTPException(status_code=400, detail="Role must be 'user' or 'broker'")
        
    existing = get_user_by_email(db, request.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Database transaction
    password_hash = hash_password(request.password)
    user = create_user(
        db, 
        email=request.email, 
        password_hash=password_hash, 
        full_name=request.full_name, 
        role=request.role
    )

    # 3. Issue Token
    token = create_token(user.id, user.role)

    logger.info(f"New user signed up: {request.email} ({request.role})")

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "city": user.city
        }
    }

@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticates existing user and dispenses JWT."""
    user = get_user_by_email(db, request.email)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    
    token = create_token(user.id, user.role)
    
    logger.info(f"User logged in: {request.email}")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "city": user.city
        }
    }

@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    """Returns the profile schema for the currently authenticated user."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "city": current_user.city,
        "is_active": current_user.is_active
    }

@router.post("/logout")
async def logout():
    """Client-defined operation, simply drops token client side, return 200 OK."""
    return {"message": "Logged out successfully"}
