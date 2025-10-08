"""
Backend FastAPI MINIMAL - Solo para probar Vercel
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

app = FastAPI(title="Test API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "message": "API Test - Vercel OK",
        "status": "online",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "env_check": {
            "has_database_url": "DATABASE_URL" in os.environ,
            "has_jwt_key": "JWT_SECRET_KEY" in os.environ
        }
    }

# Handler para Vercel
handler = app
