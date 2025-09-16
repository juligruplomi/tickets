import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Importar routers
from routers import auth, profile, roles, usuarios, tickets, config
from models.db import create_db_and_tables
from models.role import ensure_base_roles
from models.user import create_usuario
from models.site_config import init_default_config
from utils.limiter import limiter
from slowapi import SlowApi
from slowapi.middleware import SlowAPIMiddleware

# Cargar variables de entorno
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicialización al arrancar
    print("🚀 Iniciando sistema de gestión de gastos...")
    create_db_and_tables()
    ensure_base_roles()
    init_default_config()
    
    # Crear super admin si no existe
    superadmin_email = os.getenv("SEED_SUPERADMIN_EMAIL", "admin@gruplomi.com")
    superadmin_password = os.getenv("SEED_SUPERADMIN_PASSWORD", "AdminSecure123!")
    
    try:
        create_usuario(
            email=superadmin_email,
            password=superadmin_password,
            rol="admin",
            first_name="Super",
            last_name="Admin",
            employee_code="ADMIN001"
        )
        print(f"✅ Super admin creado: {superadmin_email}")
    except Exception as e:
        print(f"ℹ️ Super admin ya existe: {e}")
    
    print("✅ Sistema inicializado correctamente")
    yield
    print("🔴 Cerrando sistema...")

# Crear app FastAPI
app = FastAPI(
    title="Sistema de Gestión de Gastos - Grup Lomi",
    description="API para gestión de tickets de gastos con RBAC",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://tickets.gruplomi.com").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Servir archivos estáticos (uploads)
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Incluir routers
app.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
app.include_router(profile.router, tags=["Perfil"])
app.include_router(roles.router, tags=["Roles"])
app.include_router(usuarios.router, prefix="/users", tags=["Usuarios"])
app.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])
app.include_router(config.router, prefix="/config", tags=["Configuración"])

@app.get("/")
async def root():
    return {
        "message": "Sistema de Gestión de Gastos - Grup Lomi",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected", "service": "gestion-gastos"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", "4443"))
    ssl_keyfile = os.getenv("SSL_KEYFILE")
    ssl_certfile = os.getenv("SSL_CERTFILE")
    
    if ssl_keyfile and ssl_certfile:
        print(f"🔒 Iniciando con SSL en puerto {port}")
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=port,
            ssl_key