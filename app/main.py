import os
import hashlib
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import time
from pathlib import Path

load_dotenv()

# Create logs directory if it doesn't exist
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/requests.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="PromptProof", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate process time
    process_time = time.time() - start_time
    
    # Log response
    logger.info(
        f"Response: {request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Duration: {process_time:.3f}s"
    )
    
    # Add custom headers
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./receipts.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Receipt(Base):
    __tablename__ = "receipts"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(String, index=True)
    model = Column(String)
    prompt = Column(Text)
    response = Column(Text)
    hash = Column(String, unique=True, index=True)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class GenerateRequest(BaseModel):
    prompt: str


class GenerateResponse(BaseModel):
    id: int
    timestamp: str
    model: str
    prompt: str
    response: str
    hash: str


@app.get("/")
async def root():
    return {"message": "PromptProof API", "frontend": "/static/index.html"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest, db: Session = Depends(get_db)):
    try:
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        model = "gpt-4o-mini"
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": request.prompt}
            ]
        )
        
        # Generate receipt
        timestamp = datetime.utcnow().isoformat() + "Z"
        response = completion.choices[0].message.content
        
        # Create SHA256 hash
        hash_input = timestamp + model + request.prompt + response
        hash_value = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
        
        # Save to database
        db_receipt = Receipt(
            timestamp=timestamp,
            model=model,
            prompt=request.prompt,
            response=response,
            hash=hash_value
        )
        db.add(db_receipt)
        db.commit()
        db.refresh(db_receipt)
        
        return GenerateResponse(
            id=db_receipt.id,
            timestamp=timestamp,
            model=model,
            prompt=request.prompt,
            response=response,
            hash=hash_value
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")


@app.get("/receipts/{id}", response_model=GenerateResponse)
async def get_receipt(id: int, db: Session = Depends(get_db)):
    receipt = db.query(Receipt).filter(Receipt.id == id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    return GenerateResponse(
        id=receipt.id,
        timestamp=receipt.timestamp,
        model=receipt.model,
        prompt=receipt.prompt,
        response=receipt.response,
        hash=receipt.hash
    )