from fastapi import FastAPI

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

# Esta es la función que Vercel llamará
def handler(request):
    return app