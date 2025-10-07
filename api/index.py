"""
Backend API para GrupLomi - Versión con Proxy PostgreSQL
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List
import jwt
import os
import requests
import json

# Configuración
POSTGRES_PROXY_URL = os.getenv("POSTGRES_PROXY_URL", "http://185.194.59.40:3001")
PROXY_API_KEY = os.getenv("PROXY_API_KEY", "GrupLomi2024ProxySecureKey_XyZ789")
SECRET_KEY = os.getenv("SECRET_KEY", "GrupLomi2024SecretKeyProduccion")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# Inicializar FastAPI
app = FastAPI(
    title="GrupLomi Gastos API",
    description="API para gestión de gastos de empresa",
    version="3.0.0"
)

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tickets.gruplomi.com",
        "https://tickets-alpha-pink.vercel.app",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== MODELOS ====================

class UserLogin(BaseModel):
    email: str
    password: str

class GastoCreate(BaseModel):
    tipo_gasto: str
    descripcion: str
    obra: Optional[str] = None
    importe: float
    fecha_gasto: str
    kilometros: Optional[float] = None
    precio_km: Optional[float] = None

class UserCreate(BaseModel):
    email: str
    password: str
    nombre: str
    apellidos: str
    role: str = "empleado"
    departamento: Optional[str] = None

# ==================== UTILIDADES ====================

security = HTTPBearer()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

def get_current_user(token_data = Depends(verify_token)):
    return {
        "id": token_data.get("user_id"),
        "email": token_data.get("email"),
        "role": token_data.get("role")
    }

# ==================== FUNCIONES PROXY ====================

def call_proxy(endpoint: str, method: str = "GET", data: dict = None):
    """Llamar al proxy PostgreSQL"""
    url = f"{POSTGRES_PROXY_URL}/api{endpoint}"
    headers = {
        "X-API-Key": PROXY_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=data)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except requests.RequestException as e:
        print(f"Error llamando al proxy: {e}")
        raise HTTPException(status_code=503, detail="Error de conexión con la base de datos")

# ==================== ENDPOINTS ====================

@app.get("/")
def read_root():
    return {
        "message": "API de Gastos GrupLomi v3.0",
        "status": "online",
        "database": "postgresql-proxy",
        "proxy_url": POSTGRES_PROXY_URL
    }

@app.get("/health")
def health_check():
    # Verificar salud del proxy
    try:
        response = requests.get(f"{POSTGRES_PROXY_URL}/health")
        proxy_status = "connected" if response.status_code == 200 else "error"
    except:
        proxy_status = "disconnected"
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "3.0.0",
        "proxy_status": proxy_status
    }

@app.post("/auth/login")
def login(user_login: UserLogin):
    """Login usando el proxy"""
    try:
        # Llamar al proxy para autenticar
        result = call_proxy("/auth/login", "POST", {
            "email": user_login.email,
            "password": user_login.password
        })
        
        if result.get("success"):
            user = result.get("user")
            
            # Crear token JWT
            access_token = create_access_token({
                "user_id": user["id"],
                "email": user["email"],
                "role": user["role"]
            })
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": user
            }
        else:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en login: {e}")
        raise HTTPException(status_code=500, detail="Error del servidor")

@app.get("/auth/me")
def get_me(current_user = Depends(get_current_user)):
    return current_user

@app.get("/gastos")
def get_gastos(current_user = Depends(get_current_user)):
    """Obtener gastos a través del proxy"""
    return call_proxy("/gastos", "GET", {
        "user_id": current_user["id"],
        "role": current_user["role"]
    })

@app.post("/gastos")
def create_gasto(gasto: GastoCreate, current_user = Depends(get_current_user)):
    """Crear gasto a través del proxy"""
    data = gasto.dict()
    data["creado_por"] = current_user["id"]
    return call_proxy("/gastos", "POST", data)

@app.get("/usuarios")
def get_usuarios(current_user = Depends(get_current_user)):
    """Obtener usuarios a través del proxy"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador")
    return call_proxy("/usuarios", "GET")

@app.post("/usuarios")
def create_usuario(user: UserCreate, current_user = Depends(get_current_user)):
    """Crear usuario a través del proxy"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador")
    return call_proxy("/usuarios", "POST", user.dict())

@app.put("/gastos/{gasto_id}")
def update_gasto(gasto_id: int, updates: dict, current_user = Depends(get_current_user)):
    """Actualizar gasto"""
    # Por ahora implementación básica
    return {"message": "Actualización en desarrollo"}

@app.delete("/gastos/{gasto_id}")
def delete_gasto(gasto_id: int, current_user = Depends(get_current_user)):
    """Eliminar gasto"""
    # Por ahora implementación básica
    return {"message": "Eliminación en desarrollo"}

@app.get("/config/admin")
def get_admin_config(current_user = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador")
    
    return {
        "message": "Configuración de administrador",
        "user_role": current_user["role"],
        "permissions": ["all"]
    }

@app.get("/config/sistema")
def get_system_config():
    return {
        "empresa_nombre": "GrupLomi",
        "version": "3.0.0",
        "proxy_enabled": True
    }

# Handler para Vercel
handler = app
