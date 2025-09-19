from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
def root():
    return {"status": "working", "message": "FastAPI funcionando en Vercel"}

@app.get("/health")
def health():
    return {"status": "ok", "service": "tickets-api"}

@app.get("/api/test")
def test():
    return {"test": "success", "platform": "vercel"}

# Para Vercel, no necesitamos el handler personalizado
# Vercel automáticamente detecta la variable 'app'