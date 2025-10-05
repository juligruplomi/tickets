"""
Backend FastAPI para Sistema de Gastos GrupLomi
================================================
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import Optional, List
import jwt
import bcrypt
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://gruplomi_user:GrupLomi2024%23Secure!@localhost:5433/gruplomi_tickets")
SECRET_KEY = os.getenv("SECRET_KEY", "GrupLomi2024SecretKey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas

# Configuración SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Inicializar FastAPI
app = FastAPI(
    title="GrupLomi Gastos API",
    description="API para gestión de gastos de empresa",
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
    role = Column(String, default="empleado")  # empleado, supervisor, contabilidad, admin
    departamento = Column(String)
    telefono = Column(String)
    direccion = Column(String)
    fecha_nacimiento = Column(String)
    fecha_contratacion = Column(String)
    foto_url = Column(String)
    supervisor_id = Column(Integer, ForeignKey("usuarios.id"))
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    gastos = relationship("Gasto", back_populates="usuario", foreign_keys="Gasto.creado_por")
    gastos_supervisados = relationship("Gasto", back_populates="supervisor", foreign_keys="Gasto.supervisor_asignado")

class Gasto(Base):
    __tablename__ = "gastos"
    
    id = Column(Integer, primary_key=True, index=True)
    tipo_gasto = Column(String, nullable=False)  # dieta, gasolina, aparcamiento, otros
    descripcion = Column(Text)
    obra = Column(String)
    importe = Column(Float, nullable=False)
    fecha_gasto = Column(String, nullable=False)
    estado = Column(String, default="pendiente")  # pendiente, aprobado, rechazado
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    supervisor_asignado = Column(Integer, ForeignKey("usuarios.id"))
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_aprobacion = Column(DateTime)
    aprobado_por = Column(Integer)
    archivos_adjuntos = Column(Text)  # JSON string de archivos
    kilometros = Column(Float)  # Para gastos de gasolina
    precio_km = Column(Float)  # Para gastos de gasolina
    comentarios = Column(Text)
    
    # Relaciones
    usuario = relationship("User", back_populates="gastos", foreign_keys=[creado_por])
    supervisor = relationship("User", back_populates="gastos_supervisados", foreign_keys=[supervisor_asignado])

class ConfigSistema(Base):
    __tablename__ = "config_sistema"
    
    id = Column(Integer, primary_key=True)
    clave = Column(String, unique=True, nullable=False)
    valor = Column(Text)
    descripcion = Column(String)
    fecha_modificacion = Column(DateTime, default=datetime.utcnow)

# Crear tablas
Base.metadata.create_all(bind=engine)

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
    return {"message": "API de Gastos GrupLomi v1.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# === AUTENTICACIÓN ===

@app.post("/auth/login")
def login(user_login: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_login.email).first()
    if not user or not verify_password(user_login.password, user.password_hash):
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
    # Verificar si el email ya existe
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email ya registrado")
    
    # Crear nuevo usuario
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
    
    # Actualizar campos permitidos
    allowed_fields = ["nombre", "apellidos", "departamento", "telefono", "role", "activo", "supervisor_id"]
    for field, value in updates.items():
        if field in allowed_fields:
            setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return UserResponse.from_orm(user)

@app.delete("/usuarios/{user_id}")
def delete_usuario(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Soft delete - solo desactivar
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
    
    # Filtrar por rol
    if current_user.role == "empleado":
        # Empleados solo ven sus propios gastos
        query = query.filter(Gasto.creado_por == current_user.id)
    elif current_user.role == "supervisor":
        # Supervisores ven gastos propios y de sus supervisados
        query = query.filter(
            (Gasto.creado_por == current_user.id) | 
            (Gasto.supervisor_asignado == current_user.id)
        )
    # Admin y contabilidad ven todos
    
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
    # Buscar supervisor del usuario
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
    
    # Verificar permisos
    if current_user.role == "empleado" and gasto.creado_por != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permisos para modificar este gasto")
    
    # Actualizar campos
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
    
    # Solo el creador o admin puede eliminar
    if current_user.role != "admin" and gasto.creado_por != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar este gasto")
    
    # Solo se pueden eliminar gastos pendientes
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

# === INICIALIZACIÓN ===

def init_db():
    """Inicializar base de datos con datos por defecto"""
    db = SessionLocal()
    
    # Crear usuario admin si no existe
    admin = db.query(User).filter(User.email == "admin@gruplomi.com").first()
    if not admin:
        admin = User(
            email="admin@gruplomi.com",
            password_hash=hash_password("admin123"),
            nombre="Administrador",
            apellidos="Sistema",
            role="admin",
            departamento="IT"
        )
        db.add(admin)
        
        # Crear supervisor de prueba
        supervisor = User(
            email="supervisor@gruplomi.com",
            password_hash=hash_password("super123"),
            nombre="Juan",
            apellidos="Pérez",
            role="supervisor",
            departamento="Operaciones"
        )
        db.add(supervisor)
        
        # Crear empleado de prueba
        empleado = User(
            email="empleado@gruplomi.com",
            password_hash=hash_password("empleado123"),
            nombre="María",
            apellidos="García",
            role="empleado",
            departamento="Construcción",
            supervisor_id=2  # Juan Pérez
        )
        db.add(empleado)
        
        # Crear contabilidad
        contable = User(
            email="contabilidad@gruplomi.com",
            password_hash=hash_password("conta123"),
            nombre="Ana",
            apellidos="Martínez",
            role="contabilidad",
            departamento="Finanzas"
        )
        db.add(contable)
        
        db.commit()
        print("✅ Usuarios por defecto creados")
    
    # Configuración del sistema
    config_keys = [
        ("empresa_nombre", "GrupLomi", "Nombre de la empresa"),
        ("empresa_cif", "B12345678", "CIF de la empresa"),
        ("limite_dieta", "50", "Límite diario para dietas"),
        ("limite_gasolina", "100", "Límite diario para gasolina"),
        ("limite_aparcamiento", "20", "Límite diario para aparcamiento")
    ]
    
    for clave, valor, descripcion in config_keys:
        config = db.query(ConfigSistema).filter(ConfigSistema.clave == clave).first()
        if not config:
            config = ConfigSistema(clave=clave, valor=valor, descripcion=descripcion)
            db.add(config)
    
    db.commit()
    print("✅ Configuración del sistema inicializada")
    db.close()

# Inicializar DB al arrancar
@app.on_event("startup")
def startup_event():
    print("🚀 Iniciando servidor...")
    init_db()
    print("✅ Servidor listo")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
