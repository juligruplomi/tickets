"""
Backend API para Sistema de Gastos GrupLomi - Versión Producción
==================================================================
"""
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List
import jwt
import hashlib
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

# Configuración
SECRET_KEY = os.getenv("SECRET_KEY", "GrupLomi2024SecretKeyProduccion")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# Configuración de base de datos
# Para usar el proxy en tu servidor:
# DATABASE_PROXY_URL = "http://185.194.59.40:3001"
# DATABASE_API_KEY = "GrupLomi2024SecureProxyKey"

# Para usar una BD en la nube (Supabase, Neon, etc):
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Inicializar FastAPI
app = FastAPI(
    title="GrupLomi Gastos API",
    description="API para gestión de gastos de empresa",
    version="2.0.0"
)

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tickets.gruplomi.com",
        "https://tickets-frontend-juligruplomi.vercel.app",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== CONEXIÓN BD ====================

@contextmanager
def get_db_connection():
    """Context manager para conexiones a la base de datos"""
    conn = None
    try:
        if DATABASE_URL:
            # Conexión directa a PostgreSQL (si tienes BD en la nube)
            conn = psycopg2.connect(DATABASE_URL)
        else:
            # Por ahora usar diccionario en memoria si no hay BD configurada
            class FakeConn:
                def cursor(self):
                    return FakeCursor()
                def commit(self):
                    pass
                def rollback(self):
                    pass
                def close(self):
                    pass
            
            conn = FakeConn()
        
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

# Base de datos temporal en memoria (mientras configuramos PostgreSQL)
users_db = {}
gastos_db = {}
next_gasto_id = 1

# ==================== MODELOS ====================

class UserLogin(BaseModel):
    email: str
    password: str

class UserCreate(BaseModel):
    email: str
    password: str
    nombre: str
    apellidos: str
    role: str = "empleado"
    departamento: Optional[str] = None
    telefono: Optional[str] = None

class GastoCreate(BaseModel):
    tipo_gasto: str
    descripcion: str
    obra: Optional[str] = None
    importe: float
    fecha_gasto: str
    kilometros: Optional[float] = None
    precio_km: Optional[float] = None
    archivos_adjuntos: Optional[List[str]] = None

# ==================== UTILIDADES ====================

security = HTTPBearer()

def hash_password(password: str) -> str:
    """Hash de contraseña con salt"""
    salt = "GrupLomi2024"
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar contraseña"""
    return hash_password(plain_password) == hashed_password

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
    user_id = token_data.get("user_id")
    
    # Por ahora usar memoria, luego conectar con BD
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

# ==================== INICIALIZACIÓN ====================

@app.on_event("startup")
async def startup_event():
    """Inicializar sistema al arrancar"""
    global users_db, next_gasto_id
    
    print("🚀 Iniciando servidor...")
    
    # NO crear usuarios de prueba en producción
    # Los usuarios se deben crear desde la BD real
    
    if DATABASE_URL:
        # Si hay BD configurada, verificar conexión
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                print("✅ Conexión a base de datos establecida")
        except Exception as e:
            print(f"⚠️ No se pudo conectar a la BD: {e}")
            print("   Usando almacenamiento en memoria temporal")
    else:
        print("⚠️ No hay base de datos configurada")
        print("   Configure DATABASE_URL en las variables de entorno de Vercel")
    
    print("✅ Servidor listo")

# ==================== ENDPOINTS ====================

@app.get("/")
def read_root():
    return {
        "message": "API de Gastos GrupLomi v2.0",
        "status": "online",
        "security": "enabled",
        "database": "configured" if DATABASE_URL else "memory"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "database": "connected" if DATABASE_URL else "memory"
    }

@app.post("/auth/login")
def login(user_login: UserLogin):
    """Login - Solo funcionará con usuarios reales de la BD"""
    
    if DATABASE_URL:
        # Consultar BD real
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute(
                    "SELECT * FROM usuarios WHERE email = %s AND activo = true",
                    (user_login.email,)
                )
                user = cursor.fetchone()
                
                if not user or not verify_password(user_login.password, user['password_hash']):
                    raise HTTPException(status_code=401, detail="Credenciales incorrectas")
                
                access_token = create_access_token({
                    "user_id": user['id'],
                    "email": user['email'],
                    "role": user['role']
                })
                
                return {
                    "access_token": access_token,
                    "token_type": "bearer",
                    "user": {
                        "id": user['id'],
                        "email": user['email'],
                        "nombre": user['nombre'],
                        "apellidos": user['apellidos'],
                        "role": user['role'],
                        "departamento": user['departamento']
                    }
                }
        except Exception as e:
            print(f"Error en login: {e}")
            raise HTTPException(status_code=500, detail="Error del servidor")
    else:
        # Sin BD configurada
        raise HTTPException(
            status_code=503, 
            detail="Sistema en mantenimiento. Por favor, contacte al administrador."
        )

@app.get("/auth/me")
def get_me(current_user = Depends(get_current_user)):
    return {
        "id": current_user.get("id"),
        "email": current_user.get("email"),
        "nombre": current_user.get("nombre"),
        "role": current_user.get("role")
    }

@app.get("/gastos")
def get_gastos(current_user = Depends(get_current_user)):
    """Obtener gastos del usuario"""
    
    if DATABASE_URL:
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                if current_user['role'] == 'empleado':
                    cursor.execute(
                        "SELECT * FROM gastos WHERE creado_por = %s ORDER BY fecha_creacion DESC",
                        (current_user['id'],)
                    )
                else:
                    cursor.execute("SELECT * FROM gastos ORDER BY fecha_creacion DESC")
                
                gastos = cursor.fetchall()
                return gastos
        except Exception as e:
            print(f"Error obteniendo gastos: {e}")
            return []
    else:
        return []

@app.post("/gastos")
def create_gasto(gasto: GastoCreate, current_user = Depends(get_current_user)):
    """Crear nuevo gasto"""
    
    if DATABASE_URL:
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                # Calcular importe para combustible
                if gasto.tipo_gasto == "gasolina" and gasto.kilometros and gasto.precio_km:
                    importe_calculado = gasto.kilometros * gasto.precio_km
                else:
                    importe_calculado = gasto.importe
                
                cursor.execute("""
                    INSERT INTO gastos (
                        tipo_gasto, descripcion, obra, importe, fecha_gasto,
                        estado, creado_por, kilometros, precio_km, archivos_adjuntos
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    gasto.tipo_gasto, gasto.descripcion, gasto.obra,
                    importe_calculado, gasto.fecha_gasto, 'pendiente',
                    current_user['id'], gasto.kilometros, gasto.precio_km,
                    json.dumps(gasto.archivos_adjuntos) if gasto.archivos_adjuntos else None
                ))
                
                nuevo_gasto = cursor.fetchone()
                return nuevo_gasto
        except Exception as e:
            print(f"Error creando gasto: {e}")
            raise HTTPException(status_code=500, detail="Error al crear el gasto")
    else:
        raise HTTPException(status_code=503, detail="Sistema en mantenimiento")

@app.get("/usuarios")
def get_usuarios(current_user = Depends(get_current_user)):
    """Obtener usuarios (solo admin)"""
    
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador")
    
    if DATABASE_URL:
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("SELECT id, email, nombre, apellidos, role, departamento, activo FROM usuarios")
                usuarios = cursor.fetchall()
                return usuarios
        except Exception as e:
            print(f"Error obteniendo usuarios: {e}")
            return []
    else:
        return []

@app.post("/usuarios")
def create_usuario(user: UserCreate, current_user = Depends(get_current_user)):
    """Crear usuario (solo admin)"""
    
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador")
    
    if DATABASE_URL:
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                # Verificar si existe
                cursor.execute("SELECT id FROM usuarios WHERE email = %s", (user.email,))
                if cursor.fetchone():
                    raise HTTPException(status_code=400, detail="Email ya registrado")
                
                # Crear usuario
                cursor.execute("""
                    INSERT INTO usuarios (
                        email, password_hash, nombre, apellidos, role, departamento, telefono
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, email, nombre, apellidos, role, departamento
                """, (
                    user.email, hash_password(user.password), user.nombre,
                    user.apellidos, user.role, user.departamento, user.telefono
                ))
                
                nuevo_usuario = cursor.fetchone()
                return nuevo_usuario
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error creando usuario: {e}")
            raise HTTPException(status_code=500, detail="Error al crear el usuario")
    else:
        raise HTTPException(status_code=503, detail="Sistema en mantenimiento")

@app.get("/config/admin")
def get_admin_config(current_user = Depends(get_current_user)):
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador")
    
    return {
        "message": "Configuración de administrador",
        "user_role": current_user.get('role'),
        "permissions": ["all"]
    }

@app.get("/config/sistema")
def get_system_config():
    return {
        "empresa_nombre": "GrupLomi",
        "empresa_cif": "B12345678",
        "version": "2.0.0",
        "secure_mode": True
    }

# Handler para Vercel
handler = app
