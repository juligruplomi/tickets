from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Aplicación minimalista para probar Vercel
app = FastAPI(title="Test API")

# CORS básico
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "API Test Working", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}

# Para Vercel
if __name__ != "__main__":
    # En Vercel, esto será importado como módulo
    pass
