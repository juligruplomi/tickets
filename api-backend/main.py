import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar solo los routers que existen
try:
    from routers.auth import router as auth_router
    auth_available = True
except ImportError:
    auth_available = False
    print("⚠️  Router auth no encontrado")

try:
    from routers.tickets import router as tickets_router
    tickets_available = True
except ImportError:
    tickets_available = False
    print("⚠️  Router tickets no encontrado")

try:
    from routers.usuarios import router as usuarios_router
    usuarios_available = True
except ImportError:
    usuarios_available = False
    print("⚠️  Router usuarios no encontrado")

try:
    from routers.config import router as config_router
    config_available = True
except ImportError:
    config_available = False
    print("⚠️  Router config no encontrado")

from models.db import engine, Base

# Crear tablas al iniciar la aplicación
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Iniciando servidor...")
    print("📊 Verificando conexión a base de datos...")
    
    try:
        # Crear tablas si no existen
        Base.metadata.create_all(bind=engine)
        print("✅ Base de datos conectada correctamente")
    except Exception as e:
        print(f"❌ Error conectando a base de datos: {e}")
        raise
    
    yield
    
    # Shutdown
    print("🔄 Cerrando servidor...")

# Crear aplicación FastAPI
app = FastAPI(
    title="Sistema de Tickets - GrupLomi",
    description="API para gestión de gastos y tickets empresariales",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configurar CORS para desarrollo y producción
cors_origins = [
    "http://localhost:3000",
    "https://tickets-alpha-pink.vercel.app",
    "https://*.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "message": "Sistema de Tickets - GrupLomi funcionando correctamente",
        "version": "1.0.0"
    }

# Incluir routers que existen
if auth_available:
    app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
    
if tickets_available:
    app.include_router(tickets_router, prefix="/api/tickets", tags=["Tickets"])
    
if usuarios_available:
    app.include_router(usuarios_router, prefix="/api/usuarios", tags=["Usuarios"])
    
if config_available:
    app.include_router(config_router, prefix="/api/config", tags=["Configuration"])

# Ruta principal
@app.get("/")
async def root():
    return {
        "message": "🎫 Sistema de Tickets - GrupLomi",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
        "available_routers": {
            "auth": auth_available,
            "tickets": tickets_available,
            "usuarios": usuarios_available,
            "config": config_available
        }
    }

if __name__ == "__main__":
    print("=" * 50)
    print("🏢 SISTEMA DE TICKETS - GRUPLOMI")
    print("=" * 50)
    print("🌐 Documentación: http://localhost:8000/docs")
    print("❤️  Health Check: http://localhost:8000/health")
    print("🚀 Iniciando servidor...")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

app = app