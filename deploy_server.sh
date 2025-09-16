#!/bin/bash

# Script para desplegar backend en servidor 185.194.59.40
# Ejecutar como: ssh lomi@185.194.59.40 'bash -s' < deploy_server.sh

set -e

echo "🚀 DESPLEGANDO BACKEND EN SERVIDOR"
echo "================================="

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar usuario
if [ "$USER" != "lomi" ]; then
    log_error "Ejecutar como usuario lomi"
    exit 1
fi

# Actualizar sistema
log_info "Actualizando sistema..."
sudo apt update && sudo apt upgrade -y

# Instalar dependencias si no existen
log_info "Instalando dependencias..."
sudo apt install -y python3 python3-pip python3-venv python3-dev git postgresql postgresql-contrib nginx certbot python3-certbot-nginx curl

# Crear directorio del proyecto
log_info "Creando directorio del proyecto..."
sudo mkdir -p /opt/tickets
sudo chown -R lomi:lomi /opt/tickets

# Clonar repositorio
log_info "Clonando repositorio..."
cd /opt
if [ -d "tickets" ]; then
    cd tickets
    git pull origin main
else
    git clone https://github.com/juligruplomi/tickets.git
    cd tickets
fi

# Configurar backend
log_info "Configurando backend..."
cd api-backend

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Configurar variables de entorno
if [ ! -f ".env" ]; then
    log_info "Configurando variables de entorno..."
    cp .env.example .env
    
    # Generar SECRET_KEY aleatoria
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    sed -i "s/your-super-secret-key-change-this-in-production/$SECRET_KEY/g" .env
    
    # Configurar base de datos
    sed -i "s/secure_password/GrupLomi2024!/g" .env
    sed -i "s/localhost/127.0.0.1/g" .env
    
    log_info "⚠️  Archivo .env creado. Configuración:"
    cat .env
    
    echo ""
    read -p "¿La configuración es correcta? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        log_error "Edita el archivo .env manualmente: nano .env"
        exit 1
    fi
fi

# Configurar PostgreSQL
log_info "Configurando PostgreSQL..."
sudo -u postgres psql -c "CREATE DATABASE gestion_gastos;" || true
sudo -u postgres psql -c "CREATE USER gestion_user WITH PASSWORD 'GrupLomi2024!';" || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE gestion_gastos TO gestion_user;" || true

# Inicializar base de datos
log_info "Inicializando base de datos..."
python scripts/setup_database.py

# Crear servicio systemd
log_info "Creando servicio systemd..."
sudo tee /etc/systemd/system/tickets-gruplomi.service > /dev/null <<EOF
[Unit]
Description=Sistema de Gestión de Gastos - Grup Lomi
After=network.target postgresql.service

[Service]
Type=simple
User=lomi
WorkingDirectory=/opt/tickets/api-backend
Environment=PATH=/opt/tickets/api-backend/venv/bin
ExecStart=/opt/tickets/api-backend/venv/bin/python main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Habilitar y arrancar servicio
sudo systemctl daemon-reload
sudo systemctl enable tickets-gruplomi
sudo systemctl start tickets-gruplomi

# Verificar estado
sleep 5
if systemctl is-active --quiet tickets-gruplomi; then
    log_success "Servicio backend iniciado correctamente"
else
    log_error "Error iniciando servicio backend"
    sudo journalctl -u tickets-gruplomi --no-pager -n 20
    exit 1
fi

# Configurar firewall
log_info "Configurando firewall..."
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 4443/tcp
sudo ufw allow from 127.0.0.1 to any port 5432
sudo ufw --force enable

# Obtener certificados SSL
log_info "Configurando SSL para api.gruplomi.com..."
sudo systemctl stop nginx || true

# Obtener certificado
if sudo certbot certonly --standalone -d api.gruplomi.com --agree-tos --email admin@gruplomi.com --non-interactive; then
    log_success "Certificado SSL obtenido correctamente"
    
    # Actualizar .env con rutas SSL
    sed -i "s|#SSL_KEYFILE=.*|SSL_KEYFILE=/etc/letsencrypt/live/api.gruplomi.com/privkey.pem|g" .env
    sed -i "s|#SSL_CERTFILE=.*|SSL_CERTFILE=/etc/letsencrypt/live/api.gruplomi.com/fullchain.pem|g" .env
    
    # Reiniciar servicio con SSL
    sudo systemctl restart tickets-gruplomi
    
    log_success "Servicio reiniciado con SSL"
else
    log_error "Error obteniendo certificado SSL. Continuando sin SSL..."
fi

# Configurar renovación automática SSL
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -

# Crear directorio de uploads
sudo mkdir -p /opt/tickets/uploads
sudo chown -R lomi:lomi /opt/tickets/uploads
sudo chmod 755 /opt/tickets/uploads

# Verificar instalación
log_info "Verificando instalación..."
sleep 5

if curl -k -s https://localhost:4443/health > /dev/null 2>&1; then
    log_success "✅ API funcionando con SSL"
    echo "🌐 URL: https://api.gruplomi.com:4443"
    echo "📚 Docs: https://api.gruplomi.com:4443/docs"
elif curl -s http://localhost:4443/health > /dev/null 2>&1; then
    log_success "✅ API funcionando (sin SSL)"
    echo "🌐 URL: http://api.gruplomi.com:4443"
    echo "📚 Docs: http://api.gruplomi.com:4443/docs"
else
    log_error "❌ Error: API no responde"
    sudo journalctl -u tickets-gruplomi --no-pager -n 20
    exit 1
fi

echo ""
echo "🎉 ¡BACKEND DESPLEGADO CORRECTAMENTE!"
echo "===================================="
echo "🔐 Credenciales iniciales:"
echo "   Email: admin@gruplomi.com"
echo "   Password: AdminSecure123!"
echo ""
echo "🔧 Comandos útiles:"
echo "   sudo systemctl status tickets-gruplomi"
echo "   sudo journalctl -u tickets-gruplomi -f"
echo "   sudo systemctl restart tickets-gruplomi"
echo ""
echo "📁 Archivos importantes:"
echo "   Código: /opt/tickets/"
echo "   Config: /opt/tickets/api-backend/.env"
echo "   Uploads: /opt/tickets/uploads/"
echo "   Logs: sudo journalctl -u tickets-gruplomi"
echo ""
echo "🌐 CONFIGURAR DNS:"
echo "   A    api.gruplomi.com    ->  185.194.59.40"
echo ""
echo "✅ Listo para configurar frontend en Vercel"