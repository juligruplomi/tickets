"""
Backend FastAPI para Sistema de Gastos GrupLomi - Versión Completa con Proxy HTTP
==================================================================================
"""
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import jwt
import bcrypt
import os
import requests
import io
import csv

# Configuración
PROXY_URL = os.getenv("PROXY_URL", "http://185.194.59.40:3001")
PROXY_API_KEY = os.getenv("PROXY_API_KEY", "GrupLomi2024ProxySecureKey_XyZ789")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "GrupLomi_JWT_Secret_Key_2024_Very_Secure_Hash")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# Inicializar FastAPI
app = FastAPI(
    title="GrupLomi Gastos API",
    description="API completa para gestión de gastos de empresa",
    version="3.0.0"
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
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    nombre: str
    apellidos: Optional[str] = None
    role: str = "empleado"
    departamento: Optional[str] = None
    telefono: Optional[str] = None
    activo: bool = True

class UserUpdate(BaseModel):
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    role: Optional[str] = None
    departamento: Optional[str] = None
    telefono: Optional[str] = None
    activo: Optional[bool] = None
    password: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    nombre: str
    apellidos: Optional[str]
    role: str
    departamento: Optional[str]
    telefono: Optional[str]
    activo: bool
    fecha_creacion: datetime

class GastoCreate(BaseModel):
    tipo_gasto: str
    descripcion: str
    obra: Optional[str] = None
    importe: float
    fecha_gasto: str
    kilometros: Optional[float] = None
    precio_km: Optional[float] = None

class GastoUpdate(BaseModel):
    tipo_gasto: Optional[str] = None
    descripcion: Optional[str] = None
    obra: Optional[str] = None
    importe: Optional[float] = None
    fecha_gasto: Optional[str] = None
    estado: Optional[str] = None
    comentarios: Optional[str] = None
    supervisor_asignado: Optional[int] = None
    kilometros: Optional[float] = None
    precio_km: Optional[float] = None

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

class ConfigGastos(BaseModel):
    categorias: List[str]
    limite_aprobacion_supervisor: float
    requiere_justificante: bool
    campos_obligatorios: List[str]

class ConfigNotificaciones(BaseModel):
    email_enabled: bool
    notificar_nuevo_gasto: bool
    notificar_aprobacion: bool
    notificar_rechazo: bool

class ConfigSMTP(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_from: str

class RolePermissions(BaseModel):
    ver_gastos: bool
    crear_gastos: bool
    editar_gastos: bool
    eliminar_gastos: bool
    aprobar_gastos: bool
    ver_usuarios: bool
    crear_usuarios: bool
    editar_usuarios: bool
    eliminar_usuarios: bool
    ver_reportes: bool
    exportar_datos: bool
    configurar_sistema: bool

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
    if current_user["role"] not in ["admin", "administrador"]:
        raise HTTPException(status_code=403, detail="Requiere permisos de administrador")
    return current_user

def check_supervisor_or_admin(current_user = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "administrador", "supervisor"]:
        raise HTTPException(status_code=403, detail="Requiere permisos de supervisor o administrador")
    return current_user

# ==================== ENDPOINTS BÁSICOS ====================

@app.get("/")
def read_root():
    return {
        "message": "API de Gastos GrupLomi v3.0 - Sistema Completo",
        "status": "online",
        "version": "3.0.0",
        "features": [
            "Gestión completa de usuarios",
            "Sistema de roles y permisos",
            "Gestión avanzada de gastos",
            "Reportes y exportación",
            "Configuración del sistema",
            "Notificaciones por email"
        ]
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

# ==================== AUTENTICACIÓN ====================

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

# ==================== USUARIOS ====================

@app.get("/usuarios", response_model=List[UserResponse])
def get_usuarios(
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    activo: Optional[bool] = None,
    current_user = Depends(check_admin)
):
    """Listar usuarios (solo admin)"""
    where_clauses = []
    params = []
    
    if role:
        where_clauses.append("role = %s")
        params.append(role)
    
    if activo is not None:
        where_clauses.append("activo = %s")
        params.append(activo)
    
    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
    params.extend([limit, skip])
    
    rows = db_query(f"SELECT * FROM usuarios WHERE {where_clause} ORDER BY fecha_creacion DESC LIMIT %s OFFSET %s", params)
    return [UserResponse(**row) for row in rows]

@app.post("/usuarios", response_model=UserResponse)
def create_usuario(
    user: UserCreate,
    current_user = Depends(check_admin)
):
    """Crear usuario (solo admin)"""
    # Verificar si existe
    existing = db_query("SELECT id FROM usuarios WHERE email = %s", [user.email])
    if existing:
        raise HTTPException(status_code=400, detail="Email ya registrado")
    
    # Crear usuario
    password_hash = hash_password(user.password)
    rows = db_query("""
        INSERT INTO usuarios (email, password_hash, nombre, apellidos, role, departamento, telefono, activo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *
    """, [user.email, password_hash, user.nombre, user.apellidos, user.role, user.departamento, user.telefono, user.activo])
    
    return UserResponse(**rows[0])

@app.put("/usuarios/{user_id}", response_model=UserResponse)
def update_usuario(
    user_id: int,
    user_update: UserUpdate,
    current_user = Depends(check_admin)
):
    """Actualizar usuario (solo admin)"""
    # Verificar que existe
    existing = db_query("SELECT * FROM usuarios WHERE id = %s", [user_id])
    if not existing:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Construir UPDATE
    set_parts = []
    params = []
    
    if user_update.nombre:
        set_parts.append("nombre = %s")
        params.append(user_update.nombre)
    
    if user_update.apellidos is not None:
        set_parts.append("apellidos = %s")
        params.append(user_update.apellidos)
    
    if user_update.role:
        set_parts.append("role = %s")
        params.append(user_update.role)
    
    if user_update.departamento is not None:
        set_parts.append("departamento = %s")
        params.append(user_update.departamento)
    
    if user_update.telefono is not None:
        set_parts.append("telefono = %s")
        params.append(user_update.telefono)
    
    if user_update.activo is not None:
        set_parts.append("activo = %s")
        params.append(user_update.activo)
    
    if user_update.password:
        set_parts.append("password_hash = %s")
        params.append(hash_password(user_update.password))
    
    if not set_parts:
        return UserResponse(**existing[0])
    
    params.append(user_id)
    query = f"UPDATE usuarios SET {', '.join(set_parts)} WHERE id = %s RETURNING *"
    
    rows = db_query(query, params)
    return UserResponse(**rows[0])

@app.delete("/usuarios/{user_id}")
def delete_usuario(
    user_id: int,
    current_user = Depends(check_admin)
):
    """Eliminar usuario (solo admin)"""
    # No permitir eliminar al usuario actual
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")
    
    # Verificar que existe
    existing = db_query("SELECT id FROM usuarios WHERE id = %s", [user_id])
    if not existing:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    db_query("DELETE FROM usuarios WHERE id = %s", [user_id])
    return {"message": "Usuario eliminado correctamente"}

@app.put("/usuarios/{user_id}/toggle-active")
def toggle_user_active(
    user_id: int,
    current_user = Depends(check_admin)
):
    """Activar/desactivar usuario"""
    rows = db_query("UPDATE usuarios SET activo = NOT activo WHERE id = %s RETURNING *", [user_id])
    if not rows:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return UserResponse(**rows[0])

# ==================== GASTOS ====================

@app.get("/gastos", response_model=List[GastoResponse])
def get_gastos(
    skip: int = 0,
    limit: int = 100,
    estado: Optional[str] = None,
    tipo_gasto: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Listar gastos según permisos del usuario"""
    where_clauses = []
    params = []
    
    # Filtrar según rol
    if current_user["role"] in ["empleado", "operario"]:
        where_clauses.append("creado_por = %s")
        params.append(current_user["id"])
    elif current_user["role"] == "supervisor":
        where_clauses.append("(creado_por = %s OR supervisor_asignado = %s)")
        params.extend([current_user["id"], current_user["id"]])
    
    # Filtros adicionales
    if estado:
        where_clauses.append("estado = %s")
        params.append(estado)
    
    if tipo_gasto:
        where_clauses.append("tipo_gasto = %s")
        params.append(tipo_gasto)
    
    if fecha_desde:
        where_clauses.append("fecha_gasto >= %s")
        params.append(fecha_desde)
    
    if fecha_hasta:
        where_clauses.append("fecha_gasto <= %s")
        params.append(fecha_hasta)
    
    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
    params.extend([limit, skip])
    
    query = f"SELECT * FROM gastos WHERE {where_clause} ORDER BY fecha_creacion DESC LIMIT %s OFFSET %s"
    rows = db_query(query, params)
    
    return [GastoResponse(**row) for row in rows]

@app.post("/gastos", response_model=GastoResponse)
def create_gasto(
    gasto: GastoCreate,
    current_user = Depends(get_current_user)
):
    """Crear gasto"""
    # Obtener supervisor del usuario
    user_data = db_query("SELECT supervisor_id FROM usuarios WHERE id = %s", [current_user["id"]])
    supervisor_id = user_data[0].get("supervisor_id") if user_data else None
    
    # Crear gasto
    rows = db_query("""
        INSERT INTO gastos (
            tipo_gasto, descripcion, obra, importe, fecha_gasto,
            creado_por, supervisor_asignado, kilometros, precio_km, estado
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pendiente')
        RETURNING *
    """, [
        gasto.tipo_gasto, gasto.descripcion, gasto.obra, gasto.importe, gasto.fecha_gasto,
        current_user["id"], supervisor_id, gasto.kilometros, gasto.precio_km
    ])
    
    return GastoResponse(**rows[0])

@app.put("/gastos/{gasto_id}")
def update_gasto(
    gasto_id: int,
    updates: GastoUpdate,
    current_user = Depends(get_current_user)
):
    """Actualizar gasto"""
    # Verificar que existe
    gasto_rows = db_query("SELECT * FROM gastos WHERE id = %s", [gasto_id])
    if not gasto_rows:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    
    gasto = gasto_rows[0]
    
    # Verificar permisos
    if current_user["role"] in ["empleado", "operario"] and gasto["creado_por"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    # Si es empleado, solo puede editar gastos pendientes
    if current_user["role"] in ["empleado", "operario"] and gasto["estado"] != "pendiente":
        raise HTTPException(status_code=403, detail="Solo puedes editar gastos pendientes")
    
    # Construir UPDATE
    set_parts = []
    params = []
    
    if updates.tipo_gasto:
        set_parts.append("tipo_gasto = %s")
        params.append(updates.tipo_gasto)
    
    if updates.descripcion:
        set_parts.append("descripcion = %s")
        params.append(updates.descripcion)
    
    if updates.obra is not None:
        set_parts.append("obra = %s")
        params.append(updates.obra)
    
    if updates.importe:
        set_parts.append("importe = %s")
        params.append(updates.importe)
    
    if updates.fecha_gasto:
        set_parts.append("fecha_gasto = %s")
        params.append(updates.fecha_gasto)
    
    if updates.kilometros is not None:
        set_parts.append("kilometros = %s")
        params.append(updates.kilometros)
    
    if updates.precio_km is not None:
        set_parts.append("precio_km = %s")
        params.append(updates.precio_km)
    
    if updates.estado and current_user["role"] in ["supervisor", "admin", "administrador", "contabilidad"]:
        set_parts.append("estado = %s")
        params.append(updates.estado)
    
    if updates.comentarios:
        set_parts.append("comentarios = %s")
        params.append(updates.comentarios)
    
    if updates.supervisor_asignado and current_user["role"] in ["admin", "administrador"]:
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
    """Eliminar gasto"""
    # Verificar que existe
    gasto_rows = db_query("SELECT * FROM gastos WHERE id = %s", [gasto_id])
    if not gasto_rows:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    
    gasto = gasto_rows[0]
    
    # Verificar permisos
    is_admin = current_user["role"] in ["admin", "administrador"]
    is_owner = gasto["creado_por"] == current_user["id"]
    
    if not is_admin and not is_owner:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    if not is_admin and gasto["estado"] != "pendiente":
        raise HTTPException(status_code=400, detail="Solo se pueden eliminar gastos pendientes")
    
    db_query("DELETE FROM gastos WHERE id = %s", [gasto_id])
    return {"message": "Gasto eliminado correctamente"}

@app.post("/gastos/{gasto_id}/aprobar")
def aprobar_gasto(
    gasto_id: int,
    comentarios: Optional[str] = None,
    current_user = Depends(check_supervisor_or_admin)
):
    """Aprobar gasto"""
    rows = db_query("""
        UPDATE gastos 
        SET estado = 'aprobado', 
            comentarios = %s,
            fecha_aprobacion = CURRENT_TIMESTAMP,
            aprobado_por = %s
        WHERE id = %s
        RETURNING *
    """, [comentarios, current_user["id"], gasto_id])
    
    if not rows:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    
    return GastoResponse(**rows[0])

@app.post("/gastos/{gasto_id}/rechazar")
def rechazar_gasto(
    gasto_id: int,
    comentarios: str,
    current_user = Depends(check_supervisor_or_admin)
):
    """Rechazar gasto"""
    if not comentarios:
        raise HTTPException(status_code=400, detail="Debes proporcionar un motivo de rechazo")
    
    rows = db_query("""
        UPDATE gastos 
        SET estado = 'rechazado', 
            comentarios = %s
        WHERE id = %s
        RETURNING *
    """, [comentarios, gasto_id])
    
    if not rows:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    
    return GastoResponse(**rows[0])

# ==================== ROLES Y PERMISOS ====================

@app.get("/roles")
def get_roles(current_user = Depends(check_admin)):
    """Obtener roles y sus permisos"""
    roles = {
        "administrador": {
            "nombre": "Administrador",
            "descripcion": "Acceso completo al sistema",
            "permisos": {
                "ver_gastos": True,
                "crear_gastos": True,
                "editar_gastos": True,
                "eliminar_gastos": True,
                "aprobar_gastos": True,
                "ver_usuarios": True,
                "crear_usuarios": True,
                "editar_usuarios": True,
                "eliminar_usuarios": True,
                "ver_reportes": True,
                "exportar_datos": True,
                "configurar_sistema": True
            }
        },
        "supervisor": {
            "nombre": "Supervisor",
            "descripcion": "Aprobar gastos de su equipo",
            "permisos": {
                "ver_gastos": True,
                "crear_gastos": True,
                "editar_gastos": True,
                "eliminar_gastos": False,
                "aprobar_gastos": True,
                "ver_usuarios": False,
                "crear_usuarios": False,
                "editar_usuarios": False,
                "eliminar_usuarios": False,
                "ver_reportes": True,
                "exportar_datos": True,
                "configurar_sistema": False
            }
        },
        "contabilidad": {
            "nombre": "Contabilidad",
            "descripcion": "Gestionar pagos y reportes",
            "permisos": {
                "ver_gastos": True,
                "crear_gastos": False,
                "editar_gastos": True,
                "eliminar_gastos": False,
                "aprobar_gastos": False,
                "ver_usuarios": False,
                "crear_usuarios": False,
                "editar_usuarios": False,
                "eliminar_usuarios": False,
                "ver_reportes": True,
                "exportar_datos": True,
                "configurar_sistema": False
            }
        },
        "operario": {
            "nombre": "Operario",
            "descripcion": "Crear y ver sus gastos",
            "permisos": {
                "ver_gastos": True,
                "crear_gastos": True,
                "editar_gastos": True,
                "eliminar_gastos": True,
                "aprobar_gastos": False,
                "ver_usuarios": False,
                "crear_usuarios": False,
                "editar_usuarios": False,
                "eliminar_usuarios": False,
                "ver_reportes": False,
                "exportar_datos": False,
                "configurar_sistema": False
            }
        },
        "empleado": {
            "nombre": "Empleado",
            "descripcion": "Crear y ver sus gastos",
            "permisos": {
                "ver_gastos": True,
                "crear_gastos": True,
                "editar_gastos": True,
                "eliminar_gastos": True,
                "aprobar_gastos": False,
                "ver_usuarios": False,
                "crear_usuarios": False,
                "editar_usuarios": False,
                "eliminar_usuarios": False,
                "ver_reportes": False,
                "exportar_datos": False,
                "configurar_sistema": False
            }
        }
    }
    return roles

# ==================== REPORTES ====================

@app.get("/reportes/dashboard")
def get_dashboard_report(current_user = Depends(get_current_user)):
    """Reporte completo para el dashboard"""
    try:
        # Total de gastos según rol
        if current_user["role"] in ["empleado", "operario"]:
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
        
        # Gastos por tipo
        tipo_query = f"SELECT tipo_gasto, COUNT(*) as count FROM gastos {query_where} GROUP BY tipo_gasto"
        tipo_result = db_query(tipo_query, params)
        
        gastos_por_tipo = {
            "dietas": 0,
            "aparcamiento": 0,
            "gasolina": 0,
            "otros": 0
        }
        
        for row in tipo_result:
            tipo = row["tipo_gasto"].lower()
            if "diet" in tipo or "alimenta" in tipo:
                gastos_por_tipo["dietas"] += row["count"]
            elif "aparca" in tipo or "parking" in tipo:
                gastos_por_tipo["aparcamiento"] += row["count"]
            elif "gasol" in tipo or "combustible" in tipo:
                gastos_por_tipo["gasolina"] += row["count"]
            else:
                gastos_por_tipo["otros"] += row["count"]
        
        return {
            "total_gastos": total_gastos,
            "total_importe": total_importe,
            "pendientes": gastos_por_estado.get("pendiente", 0),
            "aprobados": gastos_por_estado.get("aprobado", 0),
            "rechazados": gastos_por_estado.get("rechazado", 0),
            "pagados": gastos_por_estado.get("pagado", 0),
            "por_tipo": gastos_por_tipo,
            "gastos_por_estado": gastos_por_estado
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard: {str(e)}")

@app.get("/reportes/gastos")
def get_reportes_gastos(
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    estado: Optional[str] = None,
    tipo_gasto: Optional[str] = None,
    usuario_id: Optional[int] = None,
    current_user = Depends(check_supervisor_or_admin)
):
    """Reporte detallado de gastos"""
    where_clauses = []
    params = []
    
    if fecha_desde:
        where_clauses.append("fecha_gasto >= %s")
        params.append(fecha_desde)
    
    if fecha_hasta:
        where_clauses.append("fecha_gasto <= %s")
        params.append(fecha_hasta)
    
    if estado:
        where_clauses.append("estado = %s")
        params.append(estado)
    
    if tipo_gasto:
        where_clauses.append("tipo_gasto = %s")
        params.append(tipo_gasto)
    
    if usuario_id:
        where_clauses.append("creado_por = %s")
        params.append(usuario_id)
    
    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    rows = db_query(f"""
        SELECT g.*, u.nombre as usuario_nombre, u.apellidos as usuario_apellidos
        FROM gastos g
        LEFT JOIN usuarios u ON g.creado_por = u.id
        WHERE {where_clause}
        ORDER BY g.fecha_gasto DESC
    """, params)
    
    return rows

@app.get("/reportes/export")
def export_gastos(
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    formato: str = "csv",
    current_user = Depends(check_supervisor_or_admin)
):
    """Exportar gastos a CSV"""
    where_clauses = []
    params = []
    
    if fecha_desde:
        where_clauses.append("fecha_gasto >= %s")
        params.append(fecha_desde)
    
    if fecha_hasta:
        where_clauses.append("fecha_gasto <= %s")
        params.append(fecha_hasta)
    
    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    rows = db_query(f"""
        SELECT 
            g.id, g.tipo_gasto, g.descripcion, g.obra, g.importe, 
            g.fecha_gasto, g.estado, g.kilometros, g.precio_km,
            u.nombre as usuario_nombre, u.apellidos as usuario_apellidos,
            u.email as usuario_email
        FROM gastos g
        LEFT JOIN usuarios u ON g.creado_por = u.id
        WHERE {where_clause}
        ORDER BY g.fecha_gasto DESC
    """, params)
    
    # Crear CSV
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys() if rows else [])
    writer.writeheader()
    writer.writerows(rows)
    
    # Preparar respuesta
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=gastos_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )

# ==================== CONFIGURACIÓN ====================

@app.get("/config")
def get_config():
    """Configuración pública (sin autenticación)"""
    return {
        "empresa": {
            "nombre": "GrupLomi",
            "logo_url": None,
            "colores": {
                "primario": "#1976d2",
                "secundario": "#dc004e",
                "acento": "#28a745"
            }
        },
        "gastos": {
            "tipos_gasto": [
                {"id": "transporte", "nombre": "Transporte", "icon": "🚗"},
                {"id": "alimentacion", "nombre": "Alimentación", "icon": "🍽️"},
                {"id": "hospedaje", "nombre": "Hospedaje", "icon": "🏨"},
                {"id": "material", "nombre": "Material", "icon": "💼"},
                {"id": "combustible", "nombre": "Combustible", "icon": "⛽"},
                {"id": "kilometros", "nombre": "Kilómetros", "icon": "📍"},
                {"id": "otro", "nombre": "Otro", "icon": "📎"}
            ],
            "estados": [
                {"id": "pendiente", "nombre": "Pendiente", "color": "#ffc107"},
                {"id": "aprobado", "nombre": "Aprobado", "color": "#28a745"},
                {"id": "rechazado", "nombre": "Rechazado", "color": "#dc3545"},
                {"id": "pagado", "nombre": "Pagado", "color": "#0066CC"}
            ]
        },
        "idioma": {
            "actual": "es",
            "disponibles": ["es", "en"],
            "traducciones": {
                "gastos": "Gastos",
                "nuevo_gasto": "Nuevo Gasto",
                "mis_gastos": "Mis Gastos",
                "dashboard": "Panel de Control",
                "usuarios": "Usuarios",
                "configuracion": "Configuración",
                "cerrar_sesion": "Cerrar Sesión",
                "hola": "Hola",
                "bienvenida": "Bienvenido al sistema de gastos",
                "footer": "© 2025 - Sistema de gestión de gastos"
            }
        },
        "apariencia": {
            "modo_oscuro": False,
            "tema": "default"
        },
        "version": "3.0.0",
        "permite_registro": False,
        "moneda": "EUR",
        "precio_km_default": 0.19,
        "roles": [
            {"value": "empleado", "label": "Empleado"},
            {"value": "operario", "label": "Operario"},
            {"value": "supervisor", "label": "Supervisor"},
            {"value": "contabilidad", "label": "Contabilidad"},
            {"value": "administrador", "label": "Administrador"}
        ]
    }

@app.get("/config/sistema")
def get_system_config(current_user = Depends(check_admin)):
    """Configuración del sistema (solo admin)"""
    return {
        "empresa_nombre": "GrupLomi",
        "version": "3.0.0",
        "proxy_enabled": True,
        "categorias_gastos": [
            "Transporte",
            "Alimentación",
            "Hospedaje",
            "Material",
            "Combustible",
            "Kilómetros",
            "Otro"
        ],
        "limite_aprobacion_supervisor": 1000.0,
        "requiere_justificante": True,
        "campos_obligatorios": ["tipo_gasto", "descripcion", "importe", "fecha_gasto"],
        "notificaciones": {
            "email_enabled": False,
            "notificar_nuevo_gasto": True,
            "notificar_aprobacion": True,
            "notificar_rechazo": True
        }
    }

@app.put("/config/gastos")
def update_config_gastos(
    config: ConfigGastos,
    current_user = Depends(check_admin)
):
    """Actualizar configuración de gastos"""
    # En una implementación real, esto se guardaría en la BD
    return {
        "message": "Configuración de gastos actualizada",
        "config": config.dict()
    }

@app.put("/config/notificaciones")
def update_config_notificaciones(
    config: ConfigNotificaciones,
    current_user = Depends(check_admin)
):
    """Actualizar configuración de notificaciones"""
    return {
        "message": "Configuración de notificaciones actualizada",
        "config": config.dict()
    }

@app.put("/config/smtp")
def update_config_smtp(
    config: ConfigSMTP,
    current_user = Depends(check_admin)
):
    """Configurar SMTP para envío de emails"""
    return {
        "message": "Configuración SMTP actualizada",
        "config": {
            "smtp_host": config.smtp_host,
            "smtp_port": config.smtp_port,
            "smtp_user": config.smtp_user,
            "smtp_from": config.smtp_from
            # No devolver password
        }
    }

# NOTA: Vercel detecta FastAPI automáticamente
# NO usar: handler = app (causa crash)
