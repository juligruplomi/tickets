-- Script para crear las tablas en PostgreSQL
-- Ejecutar en tu servidor: psql -U gruplomi_user -d gruplomi_tickets

-- Eliminar tablas si existen (CUIDADO en producción)
DROP TABLE IF EXISTS gastos CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;
DROP TABLE IF EXISTS config_sistema CASCADE;

-- Tabla de usuarios
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100),
    role VARCHAR(50) DEFAULT 'empleado' CHECK (role IN ('admin', 'supervisor', 'empleado', 'contabilidad')),
    departamento VARCHAR(100),
    telefono VARCHAR(50),
    direccion TEXT,
    fecha_nacimiento DATE,
    fecha_contratacion DATE,
    foto_url TEXT,
    supervisor_id INTEGER REFERENCES usuarios(id),
    activo BOOLEAN DEFAULT true,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso TIMESTAMP,
    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Tabla de gastos
CREATE TABLE gastos (
    id SERIAL PRIMARY KEY,
    tipo_gasto VARCHAR(50) NOT NULL,
    descripcion TEXT NOT NULL,
    obra VARCHAR(200),
    importe DECIMAL(10,2) NOT NULL CHECK (importe > 0),
    fecha_gasto DATE NOT NULL,
    estado VARCHAR(50) DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'aprobado', 'rechazado', 'pagado')),
    creado_por INTEGER REFERENCES usuarios(id) NOT NULL,
    supervisor_asignado INTEGER REFERENCES usuarios(id),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_aprobacion TIMESTAMP,
    aprobado_por INTEGER REFERENCES usuarios(id),
    archivos_adjuntos JSONB,
    kilometros DECIMAL(10,2),
    precio_km DECIMAL(10,4),
    comentarios TEXT
);

-- Tabla de configuración del sistema
CREATE TABLE config_sistema (
    id SERIAL PRIMARY KEY,
    clave VARCHAR(100) UNIQUE NOT NULL,
    valor TEXT,
    descripcion VARCHAR(500),
    fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para mejorar rendimiento
CREATE INDEX idx_gastos_creado_por ON gastos(creado_por);
CREATE INDEX idx_gastos_estado ON gastos(estado);
CREATE INDEX idx_gastos_fecha ON gastos(fecha_gasto);
CREATE INDEX idx_usuarios_email ON usuarios(email);
CREATE INDEX idx_usuarios_role ON usuarios(role);

-- Crear usuario administrador inicial (CAMBIAR CONTRASEÑA)
-- La contraseña 'AdminGrupLomi2025!' con el hash SHA256 y salt 'GrupLomi2024'
INSERT INTO usuarios (email, password_hash, nombre, apellidos, role, departamento) 
VALUES (
    'admin@gruplomi.com',
    '3f8c5d2a9b7e1c4f6d8a2b5e9c3f7d1a8e4b6c9d2f5a8e1b7c4d9f6a3e2b8c5d', -- CAMBIAR ESTO
    'Administrador',
    'Sistema',
    'admin',
    'IT'
);

-- Insertar configuración inicial
INSERT INTO config_sistema (clave, valor, descripcion) VALUES
('empresa_nombre', 'GrupLomi', 'Nombre de la empresa'),
('empresa_cif', 'B12345678', 'CIF de la empresa'),
('limite_dieta', '50', 'Límite diario para dietas en euros'),
('limite_gasolina', '100', 'Límite diario para gasolina en euros'),
('limite_aparcamiento', '20', 'Límite diario para aparcamiento en euros'),
('dias_limite_presentacion', '30', 'Días máximos para presentar un gasto'),
('version_sistema', '2.0.0', 'Versión del sistema');

-- Mensaje de finalización
SELECT 'Tablas creadas correctamente. Usuario admin creado: admin@gruplomi.com' as mensaje;
