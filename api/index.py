"""
Backend FastAPI para Sistema de Gastos GrupLomi - Versión con Proxy HTTP
=========================================================================
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List
import jwt
import bcrypt
import os
import requests

# Configuración
PROXY_URL = os.getenv("PROXY_URL", "http://185.194.59.40:3001")
PROXY_API_KEY = os.getenv("PROXY_API_KEY", "GrupLomi2024ProxySecureKey_XyZ789")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "GrupLomi_JWT_Secret_Key_2024_Very_Secure_Hash")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# Inicializar FastAPI
app = FastAPI(
    title="GrupLomi Gastos API",
    description="API para gestión de gastos de empresa - Proxy HTTP",
    version="2.0.0"
)

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tickets.gruplomi.com",
        "https://tickets-frontend-git-main-juligruplomis-projects.vercel.app",
        "https://tickets-frontend-hwbjgiiwx-juligruplomis-projects.vercel.app",
        "http://localhost:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== UTILIDADES BD ====================

def db_query(text: str, params: list = None):
    """Ejecutar query a través del proxy HTTP"""
    try:
        # Convertir %s a $1, $2, $3... para PostgreSQL
        if params:
            for i in range(len(params)):
                text = text.replace('%s', f'${i+1}', 1)
        
        response = requests.post(
            f"{PROXY_URL}/query",
            json={"text": text, "params": params or []},
            headers={"x-api-key": PROXY_API_KEY},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return data.get("rows", [])
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ==================== MODELOS PYDANTIC ====================

class UserLogin(BaseModel):
    email: str
    password: str

class UserCreate(BaseModel):
    email: str
    password: str
    nombre: str
    apellidos: Optional[str] = None
    role: str = "empleado"
    departamento: Optional[str] = None
    telefono: Optional[str] = None
    supervisor_id: Optional[int] = None

class UserResponse(BaseModel):
    id: int
    email: str
    nombre: str
    apellidos: Optional[str]
    role: str
    departamento: Optional[str]
    telefono: Optional[str]
    activo: bool

class GastoCreate(BaseModel):
    tipo_gasto: str
    descripcion: str
    obra: Optional[str] = None
    importe: float
    fecha_gasto: str
    kilometros: Optional[float] = None
    precio_km: Optional[float] = None
    archivos_adjuntos: Optional[str] = None

class GastoUpdate(BaseModel):
    estado: Optional[str] = None
    comentarios: Optional[str] = None
    supervisor_asignado: Optional[int] = None

class GastoResponse(BaseModel):
    id: int
    tipo_gasto: str
    descripcion: str
    obra: Optional[str]
    importe: float
    fecha_gasto: str
    estado: str
    creado_por: int
    supervisor_asignado: Optional[int]
    fecha_creacion: datetime
    kilometros: Optional[float]
    precio_km: Optional[float]
    comentarios: Optional[str]

# ==================== UTILIDADES AUTH ====================

security = HTTPBearer()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

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
    rows = db_query("SELECT * FROM usuarios WHERE id = %s", [token_data["user_id"]])
    if not rows:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return rows[0]

def check_admin(current_user = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador")
    return current_user

# ==================== ENDPOINTS ====================

@app.get("/")
def read_root():
    return {
        "message": "API de Gastos GrupLomi v2.0 - Proxy HTTP",
        "status": "online",
        "version": "2.0.0"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/debug/db")
def debug_database():
    """Endpoint de diagnóstico"""
    try:
        rows = db_query("SELECT COUNT(*) as count FROM usuarios")
        return {
            "status": "success",
            "proxy_url": PROXY_URL,
            "connection": "OK",
            "users_count": rows[0]["count"]
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "proxy_url": PROXY_URL
        }

# === AUTENTICACIÓN ===

@app.post("/auth/login")
def login(user_login: UserLogin):
    try:
        rows = db_query("SELECT * FROM usuarios WHERE email = %s", [user_login.email])
        
        if not rows:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        
        user = rows[0]
        
        if not verify_password(user_login.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        
        if not user["activo"]:
            raise HTTPException(status_code=401, detail="Usuario desactivado")
        
        access_token = create_access_token({
            "user_id": user["id"],
            "email": user["email"],
            "role": user["role"]
        })
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "email": user["email"],
                "nombre": user["nombre"],
                "apellidos": user.get("apellidos"),
                "role": user["role"],
                "departamento": user.get("departamento")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/auth/me")
def get_me(current_user = Depends(get_current_user)):
    return UserResponse(**current_user)

# === USUARIOS ===

@app.get("/usuarios", response_model=List[UserResponse])
def get_usuarios(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(check_admin)
):
    rows = db_query("SELECT * FROM usuarios LIMIT %s OFFSET %s", [limit, skip])
    return [UserResponse(**row) for row in rows]

@app.post("/usuarios", response_model=UserResponse)
def create_usuario(
    user: UserCreate,
    current_user = Depends(check_admin)
):
    # Verificar si existe
    existing = db_query("SELECT id FROM usuarios WHERE email = %s", [user.email])
    if existing:
        raise HTTPException(status_code=400, detail="Email ya registrado")
    
    # Crear usuario
    password_hash = hash_password(user.password)
    rows = db_query("""
        INSERT INTO usuarios (email, password_hash, nombre, apellidos, role, departamento, telefono, activo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, true)
        RETURNING *
    """, [user.email, password_hash, user.nombre, user.apellidos, user.role, user.departamento, user.telefono])
    
    return UserResponse(**rows[0])

# === GASTOS ===

@app.get("/gastos", response_model=List[GastoResponse])
def get_gastos(
    skip: int = 0,
    limit: int = 100,
    estado: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    # Construir query según rol
    if current_user["role"] == "empleado":
        where_clause = "WHERE creado_por = %s"
        params = [current_user["id"]]
    elif current_user["role"] == "supervisor":
        where_clause = "WHERE (creado_por = %s OR supervisor_asignado = %s)"
        params = [current_user["id"], current_user["id"]]
    else:
        where_clause = ""
        params = []
    
    # Añadir filtro de estado
    if estado:
        if where_clause:
            where_clause += " AND estado = %s"
        else:
            where_clause = "WHERE estado = %s"
        params.append(estado)
    
    # Añadir limit y offset
    params.extend([limit, skip])
    
    query = f"SELECT * FROM gastos {where_clause} ORDER BY fecha_creacion DESC LIMIT %s OFFSET %s"
    rows = db_query(query, params)
    
    return [GastoResponse(**row) for row in rows]

@app.post("/gastos", response_model=GastoResponse)
def create_gasto(
    gasto: GastoCreate,
    current_user = Depends(get_current_user)
):
    # Obtener supervisor del usuario
    user_data = db_query("SELECT supervisor_id FROM usuarios WHERE id = %s", [current_user["id"]])
    supervisor_id = user_data[0].get("supervisor_id") if user_data else None
    
    # Crear gasto
    rows = db_query("""
        INSERT INTO gastos (
            tipo_gasto, descripcion, obra, importe, fecha_gasto,
            creado_por, supervisor_asignado, kilometros, precio_km, archivos_adjuntos
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *
    """, [
        gasto.tipo_gasto, gasto.descripcion, gasto.obra, gasto.importe, gasto.fecha_gasto,
        current_user["id"], supervisor_id, gasto.kilometros, gasto.precio_km, gasto.archivos_adjuntos
    ])
    
    return GastoResponse(**rows[0])

@app.put("/gastos/{gasto_id}")
def update_gasto(
    gasto_id: int,
    updates: GastoUpdate,
    current_user = Depends(get_current_user)
):
    # Verificar que existe
    gasto_rows = db_query("SELECT * FROM gastos WHERE id = %s", [gasto_id])
    if not gasto_rows:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    
    gasto = gasto_rows[0]
    
    # Verificar permisos
    if current_user["role"] == "empleado" and gasto["creado_por"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    # Construir UPDATE
    set_parts = []
    params = []
    
    if updates.estado and current_user["role"] in ["supervisor", "admin", "contabilidad"]:
        set_parts.append("estado = %s")
        params.append(updates.estado)
        
        if updates.estado == "aprobado":
            set_parts.append("fecha_aprobacion = CURRENT_TIMESTAMP")
            set_parts.append("aprobado_por = %s")
            params.append(current_user["id"])
    
    if updates.comentarios:
        set_parts.append("comentarios = %s")
        params.append(updates.comentarios)
    
    if updates.supervisor_asignado and current_user["role"] == "admin":
        set_parts.append("supervisor_asignado = %s")
        params.append(updates.supervisor_asignado)
    
    if not set_parts:
        return GastoResponse(**gasto)
    
    params.append(gasto_id)
    query = f"UPDATE gastos SET {', '.join(set_parts)} WHERE id = %s RETURNING *"
    
    rows = db_query(query, params)
    return GastoResponse(**rows[0])

@app.delete("/gastos/{gasto_id}")
def delete_gasto(
    gasto_id: int,
    current_user = Depends(get_current_user)
):
    # Verificar que existe
    gasto_rows = db_query("SELECT * FROM gastos WHERE id = %s", [gasto_id])
    if not gasto_rows:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    
    gasto = gasto_rows[0]
    
    # Verificar permisos
    if current_user["role"] != "admin" and gasto["creado_por"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    if gasto["estado"] != "pendiente":
        raise HTTPException(status_code=400, detail="Solo se pueden eliminar gastos pendientes")
    
    db_query("DELETE FROM gastos WHERE id = %s", [gasto_id])
    return {"message": "Gasto eliminado correctamente"}

# === CONFIGURACIÓN ===

@app.get("/config")
def get_config():
    """Configuración pública (sin autenticación)"""
    config_data = {
        "empresa_nombre": "GrupLomi",
        "version": "2.0.0",
        "logo_url": None,
        "permite_registro": False,
        "modo_oscuro": False,
        "color_primario": "#1976d2",
        "color_secundario": "#dc004e",
        "moneda": "EUR",
        "precio_km_default": 0.19,
        "tipos_gasto": [
            "Transporte",
            "Alimentación",
            "Hospedaje",
            "Material",
            "Combustible",
            "Kilómetros",
            "Otro"
        ],
        "roles": [
            {"value": "empleado", "label": "Empleado"},
            {"value": "supervisor", "label": "Supervisor"},
            {"value": "contabilidad", "label": "Contabilidad"},
            {"value": "admin", "label": "Administrador"}
        ]
    }
    # Devolver en ambos formatos para compatibilidad
    return {
        **config_data,  # Campos directamente
        "config": config_data  # También anidado
    }

@app.get("/config/sistema")
def get_system_config():
    return {
        "empresa_nombre": "GrupLomi",
        "version": "2.0.0",
        "proxy_enabled": True
    }

# === ESTADÍSTICAS Y DASHBOARD ===

@app.get("/stats/dashboard")
def get_dashboard_stats(current_user = Depends(get_current_user)):
    """Estadísticas para el dashboard"""
    try:
        # Total de gastos según rol
        if current_user["role"] == "empleado":
            where_clause = "WHERE creado_por = %s"
            params = [current_user["id"]]
        elif current_user["role"] == "supervisor":
            where_clause = "WHERE (creado_por = %s OR supervisor_asignado = %s)"
            params = [current_user["id"], current_user["id"]]
        else:
            where_clause = ""
            params = []
        
        # Convertir %s a $1, $2...
        query_where = where_clause
        for i in range(len(params)):
            query_where = query_where.replace('%s', f'${i+1}', 1)
        
        # Total de gastos
        total_query = f"SELECT COUNT(*) as total FROM gastos {query_where}"
        total_result = db_query(total_query, params)
        total_gastos = total_result[0]["total"] if total_result else 0
        
        # Gastos por estado
        estados_query = f"SELECT estado, COUNT(*) as count FROM gastos {query_where} GROUP BY estado"
        estados_result = db_query(estados_query, params)
        
        gastos_por_estado = {}
        for row in estados_result:
            gastos_por_estado[row["estado"]] = row["count"]
        
        # Total importe
        importe_query = f"SELECT COALESCE(SUM(importe), 0) as total FROM gastos {query_where}"
        importe_result = db_query(importe_query, params)
        total_importe = float(importe_result[0]["total"]) if importe_result else 0
        
        return {
            "total_gastos": total_gastos,
            "gastos_pendientes": gastos_por_estado.get("pendiente", 0),
            "gastos_aprobados": gastos_por_estado.get("aprobado", 0),
            "gastos_rechazados": gastos_por_estado.get("rechazado", 0),
            "total_importe": total_importe,
            "gastos_por_estado": gastos_por_estado
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

# NOTA: Vercel detecta FastAPI automáticamente
# NO usar: handler = app (causa crash)
