#!/bin/bash
# Script para configurar proxy PostgreSQL en servidor Ubuntu

echo "🚀 Configurando proxy PostgreSQL para GrupLomi..."

# 1. Crear directorio para el proxy
mkdir -p ~/postgres-proxy
cd ~/postgres-proxy

# 2. Crear package.json
cat > package.json << 'EOF'
{
  "name": "gruplomi-postgres-proxy",
  "version": "1.0.0",
  "description": "Proxy seguro PostgreSQL para GrupLomi",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "node server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "pg": "^8.11.3",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1",
    "helmet": "^7.1.0",
    "express-rate-limit": "^7.1.5"
  }
}
EOF

# 3. Crear el servidor proxy
cat > server.js << 'EOF'
const express = require('express');
const { Pool } = require('pg');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

const app = express();
const port = process.env.PORT || 3001;

// Configuración de seguridad
app.use(helmet());

// CORS - Solo permitir desde Vercel
app.use(cors({
  origin: [
    'https://tickets-alpha-pink.vercel.app',
    'https://tickets.gruplomi.com',
    'http://localhost:3000' // Para pruebas locales
  ],
  credentials: true
}));

app.use(express.json({ limit: '10mb' }));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutos
  max: 100 // límite de 100 requests por IP
});
app.use('/api/', limiter);

// Verificar API Key
const verifyApiKey = (req, res, next) => {
  const apiKey = req.headers['x-api-key'];
  if (!apiKey || apiKey !== process.env.API_KEY) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  next();
};

// Pool de conexiones PostgreSQL
const pool = new Pool({
  host: 'localhost',
  port: 5432,
  database: 'gruplomi_tickets',
  user: 'gruplomi_user',
  password: 'GrupLomi2024#Secure!',
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Test de conexión
pool.query('SELECT NOW()', (err, res) => {
  if (err) {
    console.error('❌ Error conectando a PostgreSQL:', err);
  } else {
    console.log('✅ Conectado a PostgreSQL:', res.rows[0].now);
  }
});

// ==================== ENDPOINTS ====================

app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    timestamp: new Date(),
    service: 'GrupLomi PostgreSQL Proxy'
  });
});

// Login
app.post('/api/auth/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    
    const result = await pool.query(
      'SELECT id, email, nombre, apellidos, role, departamento, password_hash FROM usuarios WHERE email = $1 AND activo = true',
      [email]
    );
    
    if (result.rows.length === 0) {
      return res.status(401).json({ error: 'Credenciales incorrectas' });
    }
    
    const user = result.rows[0];
    
    // Aquí deberías verificar el password con bcrypt
    // Por ahora comparación simple (CAMBIAR EN PRODUCCIÓN)
    const crypto = require('crypto');
    const hash = crypto.createHash('sha256').update(password + 'GrupLomi2024').digest('hex');
    
    if (hash !== user.password_hash) {
      return res.status(401).json({ error: 'Credenciales incorrectas' });
    }
    
    // Generar token JWT simple
    const jwt = require('crypto').randomBytes(32).toString('hex');
    
    res.json({
      success: true,
      token: jwt,
      user: {
        id: user.id,
        email: user.email,
        nombre: user.nombre,
        apellidos: user.apellidos,
        role: user.role,
        departamento: user.departamento
      }
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ error: 'Error del servidor' });
  }
});

// Obtener usuarios (con API key)
app.get('/api/usuarios', verifyApiKey, async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT id, email, nombre, apellidos, role, departamento, activo FROM usuarios ORDER BY id'
    );
    res.json(result.rows);
  } catch (error) {
    console.error('Error obteniendo usuarios:', error);
    res.status(500).json({ error: 'Error del servidor' });
  }
});

// Obtener gastos
app.get('/api/gastos', verifyApiKey, async (req, res) => {
  try {
    const { user_id, role } = req.query;
    
    let query = 'SELECT * FROM gastos';
    let params = [];
    
    if (role === 'empleado') {
      query += ' WHERE creado_por = $1';
      params = [user_id];
    }
    
    query += ' ORDER BY fecha_creacion DESC';
    
    const result = await pool.query(query, params);
    res.json(result.rows);
  } catch (error) {
    console.error('Error obteniendo gastos:', error);
    res.status(500).json({ error: 'Error del servidor' });
  }
});

// Crear gasto
app.post('/api/gastos', verifyApiKey, async (req, res) => {
  try {
    const { 
      tipo_gasto, descripcion, obra, importe, 
      fecha_gasto, creado_por, kilometros, precio_km 
    } = req.body;
    
    let importe_final = importe;
    if (tipo_gasto === 'gasolina' && kilometros && precio_km) {
      importe_final = kilometros * precio_km;
    }
    
    const result = await pool.query(
      `INSERT INTO gastos 
       (tipo_gasto, descripcion, obra, importe, fecha_gasto, creado_por, kilometros, precio_km)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
       RETURNING *`,
      [tipo_gasto, descripcion, obra, importe_final, fecha_gasto, creado_por, kilometros, precio_km]
    );
    
    res.json(result.rows[0]);
  } catch (error) {
    console.error('Error creando gasto:', error);
    res.status(500).json({ error: 'Error del servidor' });
  }
});

// Crear usuario
app.post('/api/usuarios', verifyApiKey, async (req, res) => {
  try {
    const { email, password, nombre, apellidos, role, departamento } = req.body;
    
    // Hash del password
    const crypto = require('crypto');
    const password_hash = crypto.createHash('sha256').update(password + 'GrupLomi2024').digest('hex');
    
    const result = await pool.query(
      `INSERT INTO usuarios 
       (email, password_hash, nombre, apellidos, role, departamento)
       VALUES ($1, $2, $3, $4, $5, $6)
       RETURNING id, email, nombre, apellidos, role, departamento`,
      [email, password_hash, nombre, apellidos, role, departamento]
    );
    
    res.json(result.rows[0]);
  } catch (error) {
    console.error('Error creando usuario:', error);
    if (error.code === '23505') {
      res.status(400).json({ error: 'El email ya está registrado' });
    } else {
      res.status(500).json({ error: 'Error del servidor' });
    }
  }
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 Proxy PostgreSQL ejecutándose en puerto ${PORT}`);
  console.log(`📍 URL: http://185.194.59.40:${PORT}`);
});
EOF

# 4. Crear archivo .env
cat > .env << 'EOF'
PORT=3001
API_KEY=GrupLomi2024ProxySecureKey_XyZ789
NODE_ENV=production
EOF

# 5. Instalar dependencias
echo "📦 Instalando dependencias..."
npm install

# 6. Crear servicio systemd para que se ejecute siempre
sudo tee /etc/systemd/system/postgres-proxy.service > /dev/null << 'EOF'
[Unit]
Description=PostgreSQL Proxy for GrupLomi
After=network.target

[Service]
Type=simple
User=lomi
WorkingDirectory=/home/lomi/postgres-proxy
ExecStart=/usr/bin/node server.js
Restart=always
RestartSec=10
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
EOF

# 7. Habilitar y arrancar servicio
sudo systemctl daemon-reload
sudo systemctl enable postgres-proxy
sudo systemctl start postgres-proxy

# 8. Configurar firewall
sudo ufw allow 3001/tcp

echo "✅ Proxy configurado y ejecutándose!"
echo "📍 URL del proxy: http://185.194.59.40:3001"
echo "🔑 API Key: GrupLomi2024ProxySecureKey_XyZ789"
echo ""
echo "Para ver logs: sudo journalctl -u postgres-proxy -f"
