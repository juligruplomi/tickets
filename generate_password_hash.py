#!/usr/bin/env python3
"""
Generador de hash para contraseñas de GrupLomi
"""
import hashlib

def hash_password(password):
    salt = "GrupLomi2024"
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

print("=== Generador de Hash para GrupLomi ===")
print()

# Generar hash para el admin
admin_password = input("Introduce la contraseña para admin@gruplomi.com: ")
admin_hash = hash_password(admin_password)

print()
print("Hash generado:", admin_hash)
print()
print("SQL para actualizar:")
print(f"UPDATE usuarios SET password_hash = '{admin_hash}' WHERE email = 'admin@gruplomi.com';")
print()

# Opción para generar más usuarios
while True:
    print("-" * 40)
    otro = input("¿Generar hash para otro usuario? (s/n): ")
    if otro.lower() != 's':
        break
    
    email = input("Email: ")
    nombre = input("Nombre: ")
    apellidos = input("Apellidos: ")
    password = input("Contraseña: ")
    role = input("Rol (admin/supervisor/empleado/contabilidad): ")
    
    password_hash = hash_password(password)
    
    print()
    print(f"INSERT INTO usuarios (email, password_hash, nombre, apellidos, role)")
    print(f"VALUES ('{email}', '{password_hash}', '{nombre}', '{apellidos}', '{role}');")
    print()
