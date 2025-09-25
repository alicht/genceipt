import os
import hashlib
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

load_dotenv()

app = FastAPI(title="PromptProof", version="1.0.0")

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