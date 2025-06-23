from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import bcrypt
import jwt
from geojson import Point, Feature, FeatureCollection

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
SECRET_KEY = "your-secret-key-here"

# User Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    username: str
    role: str  # "municipality", "directorate", "ministry"
    city: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    email: str
    username: str
    password: str
    role: str
    city: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

# Infrastructure Models
class InfrastructureItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str  # "electricity", "water", "sewage", "telecommunications", "roads", "public_facilities"
    subtype: Optional[str] = None
    coordinates: List[float]  # [longitude, latitude]
    status: str  # "operational", "damaged", "under_maintenance", "needs_repair"
    condition: str  # "excellent", "good", "fair", "poor", "critical"
    installation_date: Optional[datetime] = None
    last_maintenance: Optional[datetime] = None
    description: Optional[str] = None
    city: str
    district: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class InfrastructureCreate(BaseModel):
    name: str
    type: str
    subtype: Optional[str] = None
    coordinates: List[float]
    status: str
    condition: str
    installation_date: Optional[datetime] = None
    last_maintenance: Optional[datetime] = None
    description: Optional[str] = None
    city: str
    district: Optional[str] = None

class InfrastructureUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    condition: Optional[str] = None
    last_maintenance: Optional[datetime] = None
    description: Optional[str] = None

# Auth Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str) -> str:
    payload = {"user_id": user_id, "exp": datetime.utcnow().timestamp() + 86400}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return User(**user)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Auth Routes
@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Create user
    user_dict = user_data.dict()
    user_dict.pop("password")
    user_obj = User(**user_dict)
    
    # Store user with hashed password
    user_with_password = user_obj.dict()
    user_with_password["password"] = hashed_password
    
    await db.users.insert_one(user_with_password)
    return user_obj

@api_router.post("/auth/login")
async def login(login_data: UserLogin):
    user = await db.users.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"])
    user_obj = User(**user)
    return {"token": token, "user": user_obj}

# Infrastructure Routes
@api_router.get("/infrastructure", response_model=List[InfrastructureItem])
async def get_infrastructure(
    type: Optional[str] = None,
    city: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    query = {}
    
    # Role-based filtering
    if current_user.role == "municipality" and current_user.city:
        query["city"] = current_user.city
    elif city:
        query["city"] = city
    
    if type:
        query["type"] = type
    if status:
        query["status"] = status
    
    items = await db.infrastructure.find(query).to_list(1000)
    return [InfrastructureItem(**item) for item in items]

@api_router.post("/infrastructure", response_model=InfrastructureItem)
async def create_infrastructure(
    item_data: InfrastructureCreate,
    current_user: User = Depends(get_current_user)
):
    # Role-based validation
    if current_user.role == "municipality" and current_user.city:
        if item_data.city != current_user.city:
            raise HTTPException(status_code=403, detail="Can only create infrastructure in your city")
    
    item_dict = item_data.dict()
    item_dict["created_by"] = current_user.id
    item_obj = InfrastructureItem(**item_dict)
    
    await db.infrastructure.insert_one(item_obj.dict())
    return item_obj

@api_router.put("/infrastructure/{item_id}", response_model=InfrastructureItem)
async def update_infrastructure(
    item_id: str,
    update_data: InfrastructureUpdate,
    current_user: User = Depends(get_current_user)
):
    item = await db.infrastructure.find_one({"id": item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Infrastructure item not found")
    
    # Role-based validation
    if current_user.role == "municipality" and current_user.city:
        if item["city"] != current_user.city:
            raise HTTPException(status_code=403, detail="Can only update infrastructure in your city")
    
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    update_dict["updated_at"] = datetime.utcnow()
    
    await db.infrastructure.update_one({"id": item_id}, {"$set": update_dict})
    
    updated_item = await db.infrastructure.find_one({"id": item_id})
    return InfrastructureItem(**updated_item)

@api_router.delete("/infrastructure/{item_id}")
async def delete_infrastructure(
    item_id: str,
    current_user: User = Depends(get_current_user)
):
    item = await db.infrastructure.find_one({"id": item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Infrastructure item not found")
    
    # Role-based validation
    if current_user.role == "municipality":
        if current_user.city and item["city"] != current_user.city:
            raise HTTPException(status_code=403, detail="Can only delete infrastructure in your city")
    
    await db.infrastructure.delete_one({"id": item_id})
    return {"message": "Infrastructure item deleted successfully"}

# GeoJSON endpoint for map visualization
@api_router.get("/infrastructure/geojson")
async def get_infrastructure_geojson(
    type: Optional[str] = None,
    city: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    query = {}
    
    # Role-based filtering
    if current_user.role == "municipality" and current_user.city:
        query["city"] = current_user.city
    elif city:
        query["city"] = city
    
    if type:
        query["type"] = type
    if status:
        query["status"] = status
    
    items = await db.infrastructure.find(query).to_list(1000)
    
    features = []
    for item in items:
        point = Point(item["coordinates"])
        properties = {
            "id": item["id"],
            "name": item["name"],
            "type": item["type"],
            "subtype": item.get("subtype"),
            "status": item["status"],
            "condition": item["condition"],
            "city": item["city"],
            "district": item.get("district"),
            "description": item.get("description")
        }
        feature = Feature(geometry=point, properties=properties)
        features.append(feature)
    
    return FeatureCollection(features)

# Analytics Routes
@api_router.get("/analytics/overview")
async def get_analytics_overview(current_user: User = Depends(get_current_user)):
    query = {}
    if current_user.role == "municipality" and current_user.city:
        query["city"] = current_user.city
    
    # Get total counts by type
    pipeline = [
        {"$match": query},
        {"$group": {"_id": "$type", "count": {"$sum": 1}}}
    ]
    
    type_counts = await db.infrastructure.aggregate(pipeline).to_list(None)
    
    # Get status counts
    status_pipeline = [
        {"$match": query},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    
    status_counts = await db.infrastructure.aggregate(status_pipeline).to_list(None)
    
    # Get condition counts
    condition_pipeline = [
        {"$match": query},
        {"$group": {"_id": "$condition", "count": {"$sum": 1}}}
    ]
    
    condition_counts = await db.infrastructure.aggregate(condition_pipeline).to_list(None)
    
    return {
        "type_distribution": {item["_id"]: item["count"] for item in type_counts},
        "status_distribution": {item["_id"]: item["count"] for item in status_counts},
        "condition_distribution": {item["_id"]: item["count"] for item in condition_counts}
    }

# Cities endpoint
@api_router.get("/cities")
async def get_cities():
    cities = await db.infrastructure.distinct("city")
    return cities

# Test endpoint
@api_router.get("/")
async def root():
    return {"message": "Syrian Infrastructure GIS API"}

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