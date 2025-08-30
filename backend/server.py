from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime, timedelta
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
import jwt
from enum import Enum


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create the main app without a prefix
app = FastAPI(title="Sender API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class PlatformType(str, Enum):
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"

class SubscriptionPlan(str, Enum):
    FREE_TRIAL = "free_trial"
    BASIC = "basic"
    PROFESSIONAL = "professional" 
    ENTERPRISE = "enterprise"

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

# Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    hashed_password: str
    subscription_plan: SubscriptionPlan = SubscriptionPlan.FREE_TRIAL
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class MessagingAccount(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    platform: PlatformType
    display_name: str
    session_data: Dict[str, Any] = {}
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MessageTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    content: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Recipient(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    platform: PlatformType
    contact_info: str  # phone number for WhatsApp, username for Telegram
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class BroadcastJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    account_id: str
    platform: PlatformType
    template_ids: List[str]
    recipient_ids: List[str]
    status: JobStatus = JobStatus.PENDING
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_recipients: int = 0
    successful_sends: int = 0
    failed_sends: int = 0
    logs: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    subscription_plan: SubscriptionPlan
    is_admin: bool

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"id": user_id})
    if user is None:
        raise credentials_exception
    return User(**user)

# Auth endpoints
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password
    )
    
    await db.users.insert_one(new_user.dict())
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.id}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    user = await db.users.find_one({"email": user_credentials.email})
    if not user or not verify_password(user_credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["id"]}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse(**current_user.dict())

# Dashboard endpoint
@api_router.get("/dashboard")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    # Get active accounts count
    active_accounts = await db.messaging_accounts.count_documents({
        "user_id": current_user.id,
        "is_active": True
    })
    
    # Get messages sent today
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    messages_today = await db.broadcast_jobs.aggregate([
        {
            "$match": {
                "user_id": current_user.id,
                "started_at": {"$gte": today}
            }
        },
        {
            "$group": {
                "_id": None,
                "total_successful": {"$sum": "$successful_sends"},
                "total_failed": {"$sum": "$failed_sends"}
            }
        }
    ]).to_list(1)
    
    messages_stats = messages_today[0] if messages_today else {"total_successful": 0, "total_failed": 0}
    
    # Get active jobs
    active_jobs = await db.broadcast_jobs.count_documents({
        "user_id": current_user.id,
        "status": {"$in": [JobStatus.PENDING, JobStatus.RUNNING]}
    })
    
    # Get recent jobs
    recent_jobs = await db.broadcast_jobs.find({
        "user_id": current_user.id
    }).sort("created_at", -1).limit(10).to_list(10)
    
    return {
        "active_accounts": active_accounts,
        "messages_today": {
            "successful": messages_stats["total_successful"],
            "failed": messages_stats["total_failed"]
        },
        "active_jobs": active_jobs,
        "recent_jobs": [BroadcastJob(**job) for job in recent_jobs]
    }

# Basic CRUD endpoints for accounts
@api_router.get("/accounts", response_model=List[MessagingAccount])
async def get_accounts(current_user: User = Depends(get_current_user)):
    accounts = await db.messaging_accounts.find({"user_id": current_user.id}).to_list(100)
    return [MessagingAccount(**account) for account in accounts]

@api_router.post("/accounts", response_model=MessagingAccount)
async def create_account(account_data: dict, current_user: User = Depends(get_current_user)):
    new_account = MessagingAccount(
        user_id=current_user.id,
        platform=account_data["platform"],
        display_name=account_data["display_name"],
        session_data=account_data.get("session_data", {})
    )
    
    await db.messaging_accounts.insert_one(new_account.dict())
    return new_account

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()