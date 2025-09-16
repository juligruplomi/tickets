import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from models.db import Base
from models.user import User
from models.role import Role
from models.ticket import Ticket
from models.site_config import SiteConfig
from models.user_preferences import UserPreferences

load_dotenv()

def create_database():
    """Crear base de datos y tablas"""
    print("🚀 Configurando base de datos...")
    
    # Crear engine
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL no está configurada")
        return False
    
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        
        print("✅ Tablas creadas correctamente:")
        print("   - users")
        print("   - roles") 
        print("   - tickets")
        print("   - site_config")
        print("   - user_preferences")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR creando base de datos: {e}")
        return False

def seed_initial_data():
    """Poblar datos iniciales"""
    print("\n🌱 Poblando datos iniciales...")
    
    from models.role import ensure_base_roles
    from models.user import create_usuario
    from models.site_config import init_default_config
    
    try:
        # Crear roles base
        ensure_base_roles()
        print("✅ Roles base creados")
        
        # Crear super admin
        superadmin_email = os.getenv("SEED_SUPERADMIN_EMAIL", "admin@gruplomi.com")
        superadmin_password = os.getenv("SEED_SUPERADMIN_PASSWORD", "AdminSecure123!")
        
        admin_user = create_usuario(
            email=superadmin_email,
            password=superadmin_password,
            rol="admin",
            first_name="Super",
            last_name="Admin",
            employee_code="ADMIN001"
        )
        print(f"✅ Super admin creado: {superadmin_email}")
        
        # Inicializar configuración por defecto
        init_default_config()
        print("✅ Configuración por defecto inicializada")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Datos iniciales: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🏗️  CONFIGURACIÓN INICIAL - TICKETS GRUPLOMI")
    print("=" * 50)
    
    success = create_database()
    if success:
        seed_initial_data()
        print("\n✅ ¡Configuración completada!")
        print(f"🎯 Accede con: {os.getenv('SEED_SUPERADMIN_EMAIL', 'admin@gruplomi.com')}")
        print("🚀 Inicia el servidor con: python main.py")
    else:
        print("\n❌ Error en la configuración")
        sys.exit(1)