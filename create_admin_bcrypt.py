"""
Script para crear usuario administrador con bcrypt (compatible con el API)
Ejecutar una sola vez después de configurar la BD
"""
import psycopg2
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Configuración
DATABASE_URL = "postgresql://gruplomi_user:GrupLomi2024#Secure!@185.194.59.40:5432/gruplomi_tickets"
ADMIN_EMAIL = "admin@gruplomi.com"
ADMIN_PASSWORD = "AdminGrupLomi2025"  # Cambiar por una contraseña segura
ADMIN_NOMBRE = "Administrador"
ADMIN_APELLIDOS = "GrupLomi"

print("🔐 Creando usuario administrador...")
print(f"Email: {ADMIN_EMAIL}")

try:
    # Conectar a la BD
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Verificar si ya existe
    cursor.execute("SELECT id, role FROM usuarios WHERE email = %s", (ADMIN_EMAIL,))
    existing = cursor.fetchone()
    
    if existing:
        print(f"⚠️  El usuario {ADMIN_EMAIL} ya existe (ID: {existing[0]}, Role: {existing[1]})")
        respuesta = input("¿Deseas actualizar la contraseña? (s/n): ")
        
        if respuesta.lower() == 's':
            password_hash = hash_password(ADMIN_PASSWORD)
            cursor.execute("""
                UPDATE usuarios 
                SET password_hash = %s, role = 'admin', activo = true
                WHERE email = %s
            """, (password_hash, ADMIN_EMAIL))
            conn.commit()
            print("✅ Contraseña actualizada correctamente")
        else:
            print("❌ Operación cancelada")
    else:
        # Crear usuario admin
        password_hash = hash_password(ADMIN_PASSWORD)
        cursor.execute("""
            INSERT INTO usuarios (
                email, password_hash, nombre, apellidos, role, departamento, activo
            ) VALUES (%s, %s, %s, %s, 'admin', 'Administración', true)
            RETURNING id
        """, (ADMIN_EMAIL, password_hash, ADMIN_NOMBRE, ADMIN_APELLIDOS))
        
        user_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"✅ Usuario administrador creado con ID: {user_id}")
        print(f"   Email: {ADMIN_EMAIL}")
        print(f"   Password: {ADMIN_PASSWORD}")
        print(f"   Rol: admin")
        print("\n⚠️  IMPORTANTE: Guarda estas credenciales de forma segura")
    
except Exception as e:
    print(f"❌ Error: {e}")
    if conn:
        conn.rollback()
finally:
    if conn:
        cursor.close()
        conn.close()

print("\n✅ Script completado")
