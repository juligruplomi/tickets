"""
Backend FastAPI para Sistema de Gastos GrupLomi - Versión Vercel
==================================================================
IMPORTANTE: Esta versión NO tiene eventos de startup.
Usa init_db.py externamente para inicializar la base de datos.
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import Optional, List
import jwt
import bcrypt
import os

# Configuración de la base de datos - ACTUALIZADA CON BASE DE DATOS EXTERNA
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://gruplomi_user:GrupLomi2024#Secure!@185.194.59.40:5432/gruplomi_tickets")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "GrupLomi_JWT_Secret_Key_2024_Very_Secure_Hash")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Configuración SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Inicializar FastAPI
app = FastAPI(
    title="GrupLomi Gastos API",
    description="API para gestión de gastos de empresa - Vercel",
    version="1.0.0"
)

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== MODELOS DE BASE DE DATOS ====================

class User(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    nombre = Column(String, nullable=False)
    apellidos = Column(String)
    role = Column(String, default="empleado")
    departamento = Column(String)
    telefono = Column(String)
    direccion = Column(String)
    fecha_nacimiento = Column(String)
    fecha_contratacion = Column(String)
    foto_url = Column(String)
    supervisor_id = Column(Integer, ForeignKey("usuarios.id"))
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    gastos = relationship("Gasto", back_populates="usuario", foreign_keys="Gasto.creado_por")
    gastos_supervisados = relationship("Gasto", back_populates="supervisor", foreign_keys="Gasto.supervisor_asignado")

class Gasto(Base):
    __tablename__ = "gastos"
    
    id = Column(Integer, primary_key=True, index=True)
    tipo_gasto = Column(String, nullable=False)
    descripcion = Column(Text)
    obra = Column(String)
    importe = Column(Float, nullable=False)
    fecha_gasto = Column(String, nullable=False)
    estado = Column(String, default="pendiente")
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    supervisor_asignado = Column(Integer, ForeignKey("usuarios.id"))
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_aprobacion = Column(DateTime)
    aprobado_por = Column(Integer)
    archivos_adjuntos = Column(Text)
    kilometros = Column(Float)
    precio_km = Column(Float)
    comentarios = Column(Text)
    
    usuario = relationship("User", back_populates="gastos", foreign_keys=[creado_por])
    supervisor = relationship("User", back_populates="gastos_supervisados", foreign_keys=[supervisor_asignado])

class ConfigSistema(Base):
    __tablename__ = "config_sistema"
    
    id = Column(Integer, primary_key=True)
    clave = Column(String, unique=True, nullable=False)
    valor = Column(Text)
    descripcion = Column(String)
    fecha_modificacion = Column(DateTime, default=datetime.utcnow)

# NO crear tablas automáticamente en Vercel
# Base.metadata.create_all(bind=engine)  # ❌ COMENTADO para Vercel

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
    
    class Config:
        from_attributes = True

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
    
    class Config:
        from_attributes = True

# ==================== UTILIDADES ====================

security = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

def get_current_user(db: Session = Depends(get_db), token_data = Depends(verify_token)):
    user = db.query(User).filter(User.id == token_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

def check_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador")
    return current_user

def check_supervisor(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "supervisor"]:
        raise HTTPException(status_code=403, detail="No tienes permisos de supervisor")
    return current_user

# ==================== ENDPOINTS ====================

@app.get("/")
def read_root():
    return {
        "message": "API de Gastos GrupLomi v1.0 - Vercel",
        "status": "online",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/debug/db")
def debug_database():
    """Endpoint de diagnóstico para verificar la conexión a la base de datos"""
    try:
        # Intentar conectar
        db = SessionLocal()
        
        # Intentar hacer una query simple
        result = db.execute(text("SELECT 1 as test")).fetchone()
        
        # Intentar contar usuarios
        user_count = db.query(User).count()
        
        db.close()
        
        return {
            "status": "success",
            "database_url": DATABASE_URL.replace(DATABASE_URL.split('@')[0].split('://')[1], "***"),  # Ocultar credenciales
            "connection": "OK",
            "test_query": "OK",
            "users_count": user_count
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "database_url": DATABASE_URL.replace(DATABASE_URL.split('@')[0].split('://')[1], "***")
        }

# === AUTENTICACIÓN ===

@app.post("/auth/login")
def login(user_login: UserLogin, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == user_login.email).first()
        if not user:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        
        if not verify_password(user_login.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        
        if not user.activo:
            raise HTTPException(status_code=401, detail="Usuario desactivado")
        
        access_token = create_access_token({"user_id": user.id, "email": user.email, "role": user.role})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "nombre": user.nombre,
                "apellidos": user.apellidos,
                "role": user.role,
                "departamento": user.departamento
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        # Log del error para debugging
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.from_orm(current_user)

# === USUARIOS ===

@app.get("/usuarios", response_model=List[UserResponse])
def get_usuarios(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    usuarios = db.query(User).offset(skip).limit(limit).all()
    return usuarios

@app.post("/usuarios", response_model=UserResponse)
def create_usuario(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email ya registrado")
    
    db_user = User(
        email=user.email,
        password_hash=hash_password(user.password),
        nombre=user.nombre,
        apellidos=user.apellidos,
        role=user.role,
        departamento=user.departamento,
        telefono=user.telefono,
        supervisor_id=user.supervisor_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.put("/usuarios/{user_id}")
def update_usuario(
    user_id: int,
    updates: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    allowed_fields = ["nombre", "apellidos", "departamento", "telefono", "role", "activo", "supervisor_id"]
    for field, value in updates.items():
        if field in allowed_fields:
            setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return UserResponse.from_orm(current_user)

@app.delete("/usuarios/{user_id}")
def delete_usuario(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    user.activo = False
    db.commit()
    return {"message": "Usuario desactivado correctamente"}

# === GASTOS ===

@app.get("/gastos", response_model=List[GastoResponse])
def get_gastos(
    skip: int = 0,
    limit: int = 100,
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Gasto)
    
    if current_user.role == "empleado":
        query = query.filter(Gasto.creado_por == current_user.id)
    elif current_user.role == "supervisor":
        query = query.filter(
            (Gasto.creado_por == current_user.id) | 
            (Gasto.supervisor_asignado == current_user.id)
        )
    
    if estado:
        query = query.filter(Gasto.estado == estado)
    
    gastos = query.offset(skip).limit(limit).all()
    return gastos

@app.post("/gastos", response_model=GastoResponse)
def create_gasto(
    gasto: GastoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    supervisor_id = current_user.supervisor_id
    
    db_gasto = Gasto(
        tipo_gasto=gasto.tipo_gasto,
        descripcion=gasto.descripcion,
        obra=gasto.obra,
        importe=gasto.importe,
        fecha_gasto=gasto.fecha_gasto,
        creado_por=current_user.id,
        supervisor_asignado=supervisor_id,
        kilometros=gasto.kilometros,
        precio_km=gasto.precio_km,
        archivos_adjuntos=gasto.archivos_adjuntos
    )
    db.add(db_gasto)
    db.commit()
    db.refresh(db_gasto)
    return db_gasto

@app.put("/gastos/{gasto_id}")
def update_gasto(
    gasto_id: int,
    updates: GastoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    gasto = db.query(Gasto).filter(Gasto.id == gasto_id).first()
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    
    if current_user.role == "empleado" and gasto.creado_por != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permisos para modificar este gasto")
    
    if updates.estado and current_user.role in ["supervisor", "admin", "contabilidad"]:
        gasto.estado = updates.estado
        if updates.estado == "aprobado":
            gasto.fecha_aprobacion = datetime.utcnow()
            gasto.aprobado_por = current_user.id
    
    if updates.comentarios:
        gasto.comentarios = updates.comentarios
    
    if updates.supervisor_asignado and current_user.role == "admin":
        gasto.supervisor_asignado = updates.supervisor_asignado
    
    db.commit()
    db.refresh(gasto)
    return GastoResponse.from_orm(gasto)

@app.delete("/gastos/{gasto_id}")
def delete_gasto(
    gasto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    gasto = db.query(Gasto).filter(Gasto.id == gasto_id).first()
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    
    if current_user.role != "admin" and gasto.creado_por != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar este gasto")
    
    if gasto.estado != "pendiente":
        raise HTTPException(status_code=400, detail="Solo se pueden eliminar gastos pendientes")
    
    db.delete(gasto)
    db.commit()
    return {"message": "Gasto eliminado correctamente"}

# === CONFIGURACIÓN ===

@app.get("/config/admin")
def get_admin_config(current_user: User = Depends(check_admin)):
    return {
        "message": "Configuración de administrador",
        "user_role": current_user.role,
        "permissions": ["all"]
    }

@app.get("/config/sistema")
def get_system_config(db: Session = Depends(get_db)):
    configs = db.query(ConfigSistema).all()
    return {config.clave: config.valor for config in configs}

# NOTA: Vercel detecta FastAPI automáticamente
# NO usar: handler = app (causa crash)
