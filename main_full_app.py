from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "working", "message": "FastAPI funcionando en Vercel - Version 3 - Fixed"}

@app.get("/health")
def health():
    return {"status": "ok", "service": "tickets-api"}

@app.get("/api/test")
def test():
    return {"test": "success", "platform": "vercel", "version": "3"}

# Handler para Vercel
def handler(event, context):
    return app