from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt
import os
from dotenv import load_dotenv
import json

# Cargar variables de entorno
load_dotenv()

# Configuración de la aplicación
app = FastAPI(title="GrupLomi Tickets API", version="2.0")

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de Base de Datos
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://gruplomi_user:GrupLomi2024#Secure!@185.194.59.40:5432/gruplomi_tickets")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Configuración JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "GrupLomi_JWT_Secret_Key_2024_Very_Secure_Hash")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ==================== MODELOS DE BASE DE DATOS ====================

class User(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nombre = Column(String(100))
    apellidos = Column(String(100))
    codigo_empleado = Column(String(50))
    telefono = Column(String(50))
    direccion = Column(Text)
    fecha_nacimiento = Column(String(50))
    fecha_contratacion = Column(String(50))
    foto_url = Column(String(255))
    role = Column(String(50), default="usuario")
    departamento = Column(String(100))
    supervisor_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    activo = Column(Boolean, default=True)
    idioma_preferido = Column(String(10), default="es")
    permisos_especiales = Column(Text, default="[]")
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    gastos = relationship("Gasto", back_populates="usuario", foreign_keys="Gasto.creado_por")
    supervisor = relationship("User", remote_side=[id])

class Gasto(Base):
    __tablename__ = "gastos"
    
    id = Column(Integer, primary_key=True, index=True)
    tipo_gasto = Column(String(50), nullable=False)
    descripcion = Column(Text)
    obra = Column(String(255))
    importe = Column(Float, nullable=False)
    fecha_gasto = Column(String(50))
    estado = Column(String(50), default="pendiente")
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    supervisor_asignado = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    archivos_adjuntos = Column(Text, default="[]")
    fecha_aprobacion = Column(DateTime, nullable=True)
    aprobado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    kilometros = Column(Float, nullable=True)
    precio_km = Column(Float, nullable=True)
    comentarios = Column(Text)
    
    usuario = relationship("User", back_populates="gastos", foreign_keys=[creado_por])
    supervisor = relationship("User", foreign_keys=[supervisor_asignado])
    aprobador = relationship("User", foreign_keys=[aprobado_por])

class SystemConfig(Base):
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    permissions = Column(Text, default="[]")
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# Crear las tablas
Base.metadata.create_all(bind=engine)

# ==================== PYDANTIC SCHEMAS ====================

class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    nombre: str
    apellidos: str
    codigo_empleado: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    role: str = "usuario"
    departamento: Optional[str] = None
    supervisor_id: Optional[int] = None

class UserUpdate(BaseModel):
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    departamento: Optional[str] = None
    supervisor_id: Optional[int] = None
    activo: Optional[bool] = None
    idioma_preferido: Optional[str] = None

class GastoCreate(BaseModel):
    tipo_gasto: str
    descripcion: str
    obra: Optional[str] = None
    importe: float
    fecha_gasto: str
    kilometros: Optional[float] = None
    precio_km: Optional[float] = None
    comentarios: Optional[str] = None

class GastoUpdate(BaseModel):
    estado: Optional[str] = None
    supervisor_asignado: Optional[int] = None
    comentarios: Optional[str] = None

class ConfigUpdate(BaseModel):
    empresa: Optional[Dict[str, Any]] = None
    gastos: Optional[Dict[str, Any]] = None
    idioma: Optional[Dict[str, Any]] = None
    notificaciones: Optional[Dict[str, Any]] = None

# ==================== FUNCIONES AUXILIARES ====================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token no proporcionado")
    
    token = authorization.split(" ")[1]
    payload = verify_token(token)
    
    user = db.query(User).filter(User.id == payload.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return user

def init_default_config(db: Session):
    """Inicializar configuración por defecto si no existe"""
    
    default_configs = {
        "empresa": json.dumps({
            "nombre": "GrupLomi",
            "logo_url": "/logo.png",
            "cif": "B12345678",
            "direccion": "Calle Empresa 123, Barcelona",
            "colores": {
                "primario": "#0066CC",
                "secundario": "#f8f9fa",
                "acento": "#28a745"
            }
        }),
        "gastos": json.dumps({
            "categorias": [
                {"id": "dietas", "nombre": "Dietas", "icon": "🍽️", "limite": 50},
                {"id": "combustible", "nombre": "Combustible", "icon": "⛽", "limite": 100},
                {"id": "aparcamiento", "nombre": "Aparcamiento", "icon": "🅿️", "limite": 20},
                {"id": "alojamiento", "nombre": "Alojamiento", "icon": "🏨", "limite": 150},
                {"id": "transporte", "nombre": "Transporte", "icon": "🚗", "limite": 80},
                {"id": "material", "nombre": "Material", "icon": "📝", "limite": 200},
                {"id": "formacion", "nombre": "Formación", "icon": "📚", "limite": 300},
                {"id": "otros", "nombre": "Otros", "icon": "📋", "limite": 100}
            ],
            "metodos_pago": ["Efectivo", "Tarjeta empresa", "Pago propio", "Transferencia"],
            "estados": ["pendiente", "aprobado", "rechazado", "pagado"]
        }),
        "idioma": json.dumps({
            "predeterminado": "es",
            "disponibles": ["es", "en", "ca", "de", "it", "pt"]
        }),
        "notificaciones": json.dumps({
            "email_habilitado": True,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_user": "",
            "smtp_password": "",
            "eventos": {
                "gasto_creado": True,
                "gasto_aprobado": True,
                "gasto_rechazado": True,
                "recordatorio_pendientes": True,
                "limite_excedido": True,
                "cierre_mensual": True
            }
        })
    }
    
    for key, value in default_configs.items():
        config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if not config:
            config = SystemConfig(key=key, value=value)
            db.add(config)
    
    db.commit()

def init_default_roles(db: Session):
    """Crear roles por defecto"""
    default_roles = [
        {"name": "admin", "permissions": json.dumps(["all"]), "description": "Administrador del sistema"},
        {"name": "supervisor", "permissions": json.dumps(["view_all", "approve", "reports"]), "description": "Supervisor"},
        {"name": "usuario", "permissions": json.dumps(["create", "view_own"]), "description": "Usuario estándar"},
        {"name": "contabilidad", "permissions": json.dumps(["view_all", "reports", "export"]), "description": "Contabilidad"}
    ]
    
    for role_data in default_roles:
        role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not role:
            role = Role(**role_data)
            db.add(role)
    
    db.commit()

def create_default_admin(db: Session):
    """Crear usuario administrador por defecto"""
    admin = db.query(User).filter(User.email == "admin@gruplomi.com").first()
    if not admin:
        admin = User(
            email="admin@gruplomi.com",
            password_hash=get_password_hash("AdminGrupLomi2025"),
            nombre="Admin",
            apellidos="GrupLomi",
            codigo_empleado="ADM001",
            role="admin",
            activo=True,
            idioma_preferido="es"
        )
        db.add(admin)
        db.commit()
        print("✅ Usuario admin creado: admin@gruplomi.com / AdminGrupLomi2025")

# ==================== INICIALIZACIÓN ====================

@app.on_event("startup")
async def startup_event():
    """Inicializar datos por defecto al arrancar"""
    db = SessionLocal()
    try:
        init_default_roles(db)
        init_default_config(db)
        create_default_admin(db)
        print("✅ Sistema inicializado correctamente")
    except Exception as e:
        print(f"⚠️ Error en inicialización: {e}")
    finally:
        db.close()

# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    return {
        "status": "working",
        "message": "🏢 GrupLomi - Sistema de Gestión de Gastos - v2.0",
        "api": "FastAPI + PostgreSQL",
        "database": "Connected to PostgreSQL"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# AUTH ENDPOINTS
@app.post("/auth/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.username).first()
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    if not user.activo:
        raise HTTPException(status_code=403, detail="Usuario desactivado")
    
    access_token = create_access_token(data={"user_id": user.id, "email": user.email, "role": user.role})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "nombre": user.nombre,
            "apellidos": user.apellidos,
            "role": user.role,
            "departamento": user.departamento,
            "idioma_preferido": user.idioma_preferido
        }
    }

@app.get("/auth/me")
async def get_me(authorization: str = Header(None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    return {
        "id": user.id,
        "email": user.email,
        "nombre": user.nombre,
        "apellidos": user.apellidos,
        "role": user.role,
        "departamento": user.departamento,
        "idioma_preferido": user.idioma_preferido,
        "activo": user.activo
    }

# GASTOS ENDPOINTS
@app.get("/gastos")
async def get_gastos(authorization: str = Header(None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    
    if user.role == "admin" or user.role == "contabilidad":
        gastos = db.query(Gasto).all()
    elif user.role == "supervisor":
        gastos = db.query(Gasto).filter(
            (Gasto.creado_por == user.id) | (Gasto.supervisor_asignado == user.id)
        ).all()
    else:
        gastos = db.query(Gasto).filter(Gasto.creado_por == user.id).all()
    
    return gastos

@app.post("/gastos")
async def create_gasto(gasto: GastoCreate, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    
    new_gasto = Gasto(
        **gasto.dict(),
        creado_por=user.id,
        supervisor_asignado=user.supervisor_id,
        estado="pendiente",
        fecha_creacion=datetime.utcnow()
    )
    
    db.add(new_gasto)
    db.commit()
    db.refresh(new_gasto)
    
    return new_gasto

@app.put("/gastos/{gasto_id}")
async def update_gasto(gasto_id: int, update: GastoUpdate, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    
    gasto = db.query(Gasto).filter(Gasto.id == gasto_id).first()
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    
    # Verificar permisos
    if user.role not in ["admin", "supervisor", "contabilidad"] and gasto.creado_por != user.id:
        raise HTTPException(status_code=403, detail="Sin permisos para modificar este gasto")
    
    for key, value in update.dict(exclude_unset=True).items():
        setattr(gasto, key, value)
    
    if update.estado == "aprobado":
        gasto.fecha_aprobacion = datetime.utcnow()
        gasto.aprobado_por = user.id
    
    db.commit()
    db.refresh(gasto)
    
    return gasto

@app.delete("/gastos/{gasto_id}")
async def delete_gasto(gasto_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    
    gasto = db.query(Gasto).filter(Gasto.id == gasto_id).first()
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    
    # Solo admin o el creador pueden eliminar
    if user.role != "admin" and gasto.creado_por != user.id:
        raise HTTPException(status_code=403, detail="Sin permisos para eliminar este gasto")
    
    db.delete(gasto)
    db.commit()
    
    return {"message": "Gasto eliminado correctamente"}

# USUARIOS ENDPOINTS
@app.get("/usuarios")
async def get_usuarios(authorization: str = Header(None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Sin permisos para ver usuarios")
    
    usuarios = db.query(User).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "nombre": u.nombre,
            "apellidos": u.apellidos,
            "codigo_empleado": u.codigo_empleado,
            "role": u.role,
            "departamento": u.departamento,
            "activo": u.activo
        }
        for u in usuarios
    ]

@app.post("/usuarios")
async def create_usuario(user_data: UserCreate, authorization: str = Header(None), db: Session = Depends(get_db)):
    current_user = get_current_user(authorization, db)
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sin permisos para crear usuarios")
    
    # Verificar si el usuario ya existe
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    new_user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        nombre=user_data.nombre,
        apellidos=user_data.apellidos,
        codigo_empleado=user_data.codigo_empleado,
        telefono=user_data.telefono,
        direccion=user_data.direccion,
        role=user_data.role,
        departamento=user_data.departamento,
        supervisor_id=user_data.supervisor_id,
        activo=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "id": new_user.id,
        "email": new_user.email,
        "nombre": new_user.nombre,
        "apellidos": new_user.apellidos,
        "role": new_user.role
    }

@app.put("/usuarios/{user_id}")
async def update_usuario(user_id: int, update: UserUpdate, authorization: str = Header(None), db: Session = Depends(get_db)):
    current_user = get_current_user(authorization, db)
    
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Sin permisos para modificar este usuario")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    for key, value in update.dict(exclude_unset=True).items():
        setattr(user, key, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    return {
        "id": user.id,
        "email": user.email,
        "nombre": user.nombre,
        "apellidos": user.apellidos,
        "role": user.role
    }

@app.delete("/usuarios/{user_id}")
async def delete_usuario(user_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    current_user = get_current_user(authorization, db)
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sin permisos para eliminar usuarios")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # No eliminar, solo desactivar
    user.activo = False
    db.commit()
    
    return {"message": "Usuario desactivado correctamente"}

# CONFIG ENDPOINTS
@app.get("/config")
async def get_config(db: Session = Depends(get_db)):
    configs = db.query(SystemConfig).all()
    config_dict = {}
    
    for config in configs:
        try:
            config_dict[config.key] = json.loads(config.value)
        except:
            config_dict[config.key] = config.value
    
    return config_dict

@app.get("/config/admin")
async def get_admin_config(authorization: str = Header(None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Sin permisos para ver configuración de admin")
    
    configs = db.query(SystemConfig).all()
    config_dict = {}
    
    for config in configs:
        try:
            config_dict[config.key] = json.loads(config.value)
        except:
            config_dict[config.key] = config.value
    
    return config_dict

@app.put("/config/admin")
async def update_config(update: ConfigUpdate, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Sin permisos para modificar configuración")
    
    for key, value in update.dict(exclude_unset=True).items():
        config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        
        if config:
            config.value = json.dumps(value)
            config.updated_at = datetime.utcnow()
        else:
            config = SystemConfig(key=key, value=json.dumps(value))
            db.add(config)
    
    db.commit()
    
    return {"success": True, "message": "Configuración actualizada correctamente"}

@app.put("/config/language")
async def update_language(language: Dict[str, str], authorization: str = Header(None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    
    user.idioma_preferido = language.get("language", "es")
    db.commit()
    
    return {"success": True, "language": user.idioma_preferido}

# ROLES ENDPOINTS
@app.get("/roles")
async def get_roles(authorization: str = Header(None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Sin permisos para ver roles")
    
    roles = db.query(Role).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "permissions": json.loads(r.permissions) if r.permissions else [],
            "description": r.description
        }
        for r in roles
    ]

# REPORTS ENDPOINTS
@app.get("/reportes/dashboard")
async def get_dashboard(authorization: str = Header(None), db: Session = Depends(get_db)):
    user = get_current_user(authorization, db)
    
    # Estadísticas básicas
    if user.role in ["admin", "contabilidad"]:
        total_gastos = db.query(Gasto).count()
        gastos_pendientes = db.query(Gasto).filter(Gasto.estado == "pendiente").count()
        gastos_aprobados = db.query(Gasto).filter(Gasto.estado == "aprobado").count()
        total_importe = db.query(func.sum(Gasto.importe)).filter(Gasto.estado == "aprobado").scalar() or 0
    else:
        total_gastos = db.query(Gasto).filter(Gasto.creado_por == user.id).count()
        gastos_pendientes = db.query(Gasto).filter(
            Gasto.creado_por == user.id, Gasto.estado == "pendiente"
        ).count()
        gastos_aprobados = db.query(Gasto).filter(
            Gasto.creado_por == user.id, Gasto.estado == "aprobado"
        ).count()
        total_importe = db.query(func.sum(Gasto.importe)).filter(
            Gasto.creado_por == user.id, Gasto.estado == "aprobado"
        ).scalar() or 0
    
    return {
        "total_gastos": total_gastos,
        "gastos_pendientes": gastos_pendientes,
        "gastos_aprobados": gastos_aprobados,
        "total_importe": float(total_importe),
        "ultimo_update": datetime.utcnow().isoformat()
    }

# Handler for Vercel
handler = app
