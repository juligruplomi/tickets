"""
Script de Inicialización de Base de Datos
==========================================
Ejecuta este script UNA VEZ para:
1. Crear las tablas en la base de datos
2. Insertar usuarios por defecto
3. Configurar el sistema

USO:
  python init_db.py

NOTA: Este script reemplaza el evento @app.on_event("startup") que no funciona en Vercel
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import bcrypt
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos - ACTUALIZADA CON BASE DE DATOS EXTERNA
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://gruplomi_user:GrupLomi2024#Secure!@185.194.59.40:5432/gruplomi_tickets")

# Configuración SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==================== MODELOS ====================

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

# ==================== FUNCIONES ====================

def hash_password(password: str) -> str:
    """Hashear contraseña con bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def init_database():
    """Inicializar base de datos completa"""
    print("=" * 60)
    print("🚀 INICIALIZANDO BASE DE DATOS")
    print("=" * 60)
    
    # Crear todas las tablas
    print("\n📊 Creando tablas...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas correctamente")
    
    db = SessionLocal()
    
    try:
        # Verificar si ya existen datos
        existing_users = db.query(User).count()
        
        if existing_users > 0:
            print(f"\n⚠️  Ya existen {existing_users} usuarios en la base de datos")
            response = input("¿Deseas continuar y agregar usuarios de prueba? (s/n): ")
            if response.lower() != 's':
                print("❌ Inicialización cancelada")
                return
        
        # Crear usuarios por defecto
        print("\n👥 Creando usuarios por defecto...")
        
        # 1. Administrador
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
            print("✅ Usuario Admin creado - admin@gruplomi.com / admin123")
        else:
            print("⚠️  Usuario Admin ya existe")
        
        # 2. Supervisor
        supervisor = db.query(User).filter(User.email == "supervisor@gruplomi.com").first()
        if not supervisor:
            supervisor = User(
                email="supervisor@gruplomi.com",
                password_hash=hash_password("super123"),
                nombre="Juan",
                apellidos="Pérez",
                role="supervisor",
                departamento="Operaciones"
            )
            db.add(supervisor)
            print("✅ Usuario Supervisor creado - supervisor@gruplomi.com / super123")
        else:
            print("⚠️  Usuario Supervisor ya existe")
        
        db.flush()  # Para obtener IDs
        
        # 3. Empleado
        empleado = db.query(User).filter(User.email == "empleado@gruplomi.com").first()
        if not empleado:
            empleado = User(
                email="empleado@gruplomi.com",
                password_hash=hash_password("empleado123"),
                nombre="María",
                apellidos="García",
                role="empleado",
                departamento="Construcción",
                supervisor_id=supervisor.id if supervisor else 2
            )
            db.add(empleado)
            print("✅ Usuario Empleado creado - empleado@gruplomi.com / empleado123")
        else:
            print("⚠️  Usuario Empleado ya existe")
        
        # 4. Contabilidad
        contable = db.query(User).filter(User.email == "contabilidad@gruplomi.com").first()
        if not contable:
            contable = User(
                email="contabilidad@gruplomi.com",
                password_hash=hash_password("conta123"),
                nombre="Ana",
                apellidos="Martínez",
                role="contabilidad",
                departamento="Finanzas"
            )
            db.add(contable)
            print("✅ Usuario Contabilidad creado - contabilidad@gruplomi.com / conta123")
        else:
            print("⚠️  Usuario Contabilidad ya existe")
        
        db.commit()
        
        # Configuración del sistema
        print("\n⚙️  Configurando sistema...")
        
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
                print(f"  ✅ {clave}: {valor}")
            else:
                print(f"  ⚠️  {clave} ya existe")
        
        db.commit()
        
        print("\n" + "=" * 60)
        print("✅ BASE DE DATOS INICIALIZADA CORRECTAMENTE")
        print("=" * 60)
        print("\n📝 USUARIOS CREADOS:")
        print("  1. Admin:        admin@gruplomi.com / admin123")
        print("  2. Supervisor:   supervisor@gruplomi.com / super123")
        print("  3. Empleado:     empleado@gruplomi.com / empleado123")
        print("  4. Contabilidad: contabilidad@gruplomi.com / conta123")
        print("\n🎉 ¡Listo! Ahora puedes usar la API")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
