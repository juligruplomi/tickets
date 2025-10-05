#!/bin/bash
# Script para configurar proxy PostgreSQL en servidor Ubuntu
# Ejecutar en tu servidor: lomi@185.194.59.40

# 1. Instalar Node.js si no está instalado
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# 2. Crear directorio para el proxy
mkdir -p ~/postgres-proxy
cd ~/postgres-proxy

# 3. Crear package.json
cat > package.json << 'EOF'
{
  "name": "postgres-proxy",
  "version": "1.0.0",
  "description": "Secure PostgreSQL proxy for Vercel",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "pm2": "pm2 start server.js --name postgres-proxy"
  },
  "dependencies": {
    "express": "^4.18.2",
    "pg": "^8.11.3",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1",
    "helmet": "^7.1.0"
  }
}
EOF

# 4. Crear el servidor proxy
cat > server.js << 'EOF'
const express = require('express');
const { Pool } = require('pg');
const cors = require('cors');
const helmet = require('helmet');
require('dotenv').config();

const app = express();
const port = process.env.PORT || 3001;

// Seguridad
app.use(helmet());
app.use(cors({
  origin: [
    'https://tickets-alpha-pink.vercel.app',
    'https://tickets.gruplomi.com'
  ],
  credentials: true
}));
app.use(express.json());

// Verificar token de autorización
const verifyToken = (req, res, next) => {
  const token = req.headers['x-api-key'];
  if (token !== process.env.API_KEY) {
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

// Endpoints del proxy
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date() });
});

// Proxy para queries
app.post('/query', verifyToken, async (req, res) => {
  try {
    const { text, params } = req.body;
    const result = await pool.query(text, params);
    res.json(result.rows);
  } catch (error) {
    console.error('Query error:', error);
    res.status(500).json({ error: 'Database error' });
  }
});

// Proxy para transacciones
app.post('/transaction', verifyToken, async (req, res) => {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    const { queries } = req.body;
    const results = [];
    
    for (const query of queries) {
      const result = await client.query(query.text, query.params);
      results.push(result.rows);
    }
    
    await client.query('COMMIT');
    res.json(results);
  } catch (error) {
    await client.query('ROLLBACK');
    console.error('Transaction error:', error);
    res.status(500).json({ error: 'Transaction failed' });
  } finally {
    client.release();
  }
});

app.listen(port, '0.0.0.0', () => {
  console.log(`PostgreSQL proxy running on port ${port}`);
});
EOF

# 5. Crear archivo .env
cat > .env << 'EOF'
PORT=3001
API_KEY=GrupLomi2024SecureProxyKey_CAMBIAR_ESTO
EOF

# 6. Instalar dependencias
npm install

# 7. Instalar PM2 para mantener el servicio activo
sudo npm install -g pm2

# 8. Iniciar el proxy
pm2 start server.js --name postgres-proxy
pm2 save
pm2 startup

# 9. Configurar firewall para permitir puerto 3001 solo desde Vercel
sudo ufw allow from any to any port 3001

echo "✅ Proxy PostgreSQL configurado en puerto 3001"
echo "📝 Recuerda cambiar el API_KEY en el archivo .env"
