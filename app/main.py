import os
import hashlib
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="PromptProof", version="1.0.0")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class GenerateRequest(BaseModel):
    prompt: str


class GenerateResponse(BaseModel):
    timestamp: str
    model: str
    prompt: str
    response: str
    hash: str


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
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
        
        return GenerateResponse(
            timestamp=timestamp,
            model=model,
            prompt=request.prompt,
            response=response,
            hash=hash_value
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")