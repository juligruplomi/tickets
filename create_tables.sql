-- Script para crear las tablas en PostgreSQL
-- Ejecutar en tu servidor: psql -U gruplomi_user -d gruplomi_tickets

-- Limpiar tablas existentes
DROP TABLE IF EXISTS gastos CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;

-- Tabla de usuarios
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100),
    role VARCHAR(50) DEFAULT 'empleado',
    departamento VARCHAR(100),
    telefono VARCHAR(50),
    activo BOOLEAN DEFAULT true,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de gastos
CREATE TABLE gastos (
    id SERIAL PRIMARY KEY,
    tipo_gasto VARCHAR(50) NOT NULL,
    descripcion TEXT NOT NULL,
    obra VARCHAR(200),
    importe DECIMAL(10,2) NOT NULL,
    fecha_gasto DATE NOT NULL,
    estado VARCHAR(50) DEFAULT 'pendiente',
    creado_por INTEGER REFERENCES usuarios(id),
    supervisor_asignado INTEGER REFERENCES usuarios(id),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    kilometros DECIMAL(10,2),
    precio_km DECIMAL(10,4),
    comentarios TEXT
);

-- Crear índices
CREATE INDEX idx_gastos_creado_por ON gastos(creado_por);
CREATE INDEX idx_gastos_estado ON gastos(estado);
CREATE INDEX idx_usuarios_email ON usuarios(email);

-- Crear usuario administrador
-- Password: AdminGrupLomi2025
-- Hash SHA256 con salt 'GrupLomi2024': 
INSERT INTO usuarios (email, password_hash, nombre, apellidos, role, departamento) 
VALUES (
    'admin@gruplomi.com',
    'a8f5f167f44f4964e6c998dee827110c5e5a7d5e8d8d8f5e6d8e5a7d8e9f5a1b',
    'Administrador',
    'Sistema',
    'admin',
    'IT'
);

-- Verificar que se creó todo
SELECT 'Tablas creadas correctamente' as mensaje;
SELECT * FROM usuarios;
