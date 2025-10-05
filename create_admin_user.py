"""
Script para crear el primer usuario administrador
Ejecutar una sola vez después de configurar la BD
"""
import psycopg2
import hashlib
import sys

def hash_password(password):
    salt = "GrupLomi2024"
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

# Configuración de conexión
DATABASE_URL = input("Introduce la DATABASE_URL: ")
ADMIN_EMAIL = input("Email del administrador: ")
ADMIN_PASSWORD = input("Contraseña del administrador: ")
ADMIN_NOMBRE = input("Nombre del administrador: ")
ADMIN_APELLIDOS = input("Apellidos del administrador: ")

try:
    # Conectar a la BD
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Verificar si ya existe
    cursor.execute("SELECT id FROM usuarios WHERE email = %s", (ADMIN_EMAIL,))
    if cursor.fetchone():
        print(f"❌ El usuario {ADMIN_EMAIL} ya existe")
        sys.exit(1)
    
    # Crear usuario admin
    cursor.execute("""
        INSERT INTO usuarios (
            email, password_hash, nombre, apellidos, role, departamento, activo
        ) VALUES (%s, %s, %s, %s, 'admin', 'Administración', true)
        RETURNING id
    """, (ADMIN_EMAIL, hash_password(ADMIN_PASSWORD), ADMIN_NOMBRE, ADMIN_APELLIDOS))
    
    user_id = cursor.fetchone()[0]
    conn.commit()
    
    print(f"✅ Usuario administrador creado con ID: {user_id}")
    print(f"   Email: {ADMIN_EMAIL}")
    print(f"   Rol: admin")
    print("\n⚠️  IMPORTANTE: Guarda estas credenciales de forma segura")
    
except Exception as e:
    print(f"❌ Error: {e}")
    if conn:
        conn.rollback()
finally:
    if conn:
        conn.close()
