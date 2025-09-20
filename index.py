from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import hashlib
import datetime
import os
from typing import Dict, Any, Optional

# Datos simulados para pruebas
USERS_DB = {
    "admin@gruplomi.com": {
        "id": 1,
        "email": "admin@gruplomi.com",
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "nombre": "Administrador",
        "role": "admin",
        "activo": True
    },
    "user@gruplomi.com": {
        "id": 2,
        "email": "user@gruplomi.com", 
        "password_hash": hashlib.sha256("user123".encode()).hexdigest(),
        "nombre": "Usuario Test",
        "role": "usuario",
        "activo": True
    }
}

TICKETS_DB = {
    1: {
        "id": 1,
        "titulo": "Problema con impresora",
        "descripcion": "La impresora no funciona correctamente",
        "estado": "abierto",
        "prioridad": "media",
        "asignado_a": 1,
        "creado_por": 2,
        "fecha_creacion": "2025-01-15T10:00:00Z",
        "categoria": "hardware"
    }
}

# Configuración del sistema
SYSTEM_CONFIG = {
    "empresa": {
        "nombre": "GrupLomi",
        "logo_url": "/logo.png",
        "colores": {
            "primario": "#0066CC",
            "secundario": "#f8f9fa",
            "acento": "#28a745"
        }
    },
    "mensajes": {
        "bienvenida": "Bienvenido al sistema de tickets de GrupLomi",
        "footer": "© 2025 GrupLomi - Sistema de gestión de tickets"
    },
    "apariencia": {
        "modo_oscuro": False,
        "tema": "default"
    },
    "tickets": {
        "estados": ["abierto", "en_progreso", "pendiente", "resuelto", "cerrado"],
        "prioridades": ["baja", "media", "alta", "urgente"],
        "categorias": ["hardware", "software", "red", "acceso", "otro"]
    },
    "notificaciones": {
        "email_habilitado": True,
        "notificar_asignacion": True,
        "notificar_cambio_estado": True
    }
}

# Simulador simple de JWT (sin librería)
JWT_SECRET = "mi-clave-secreta-jwt-2025"

def create_simple_token(user_data: Dict) -> str:
    """Crear token simple (simulado)"""
    import base64
    payload = {
        'user_id': user_data['id'],
        'email': user_data['email'],
        'role': user_data['role'],
        'exp': str(datetime.datetime.utcnow() + datetime.timedelta(hours=24))
    }
    token_data = json.dumps(payload)
    return base64.b64encode(token_data.encode()).decode()

def verify_simple_token(token: str) -> Optional[Dict]:
    """Verificar token simple"""
    try:
        import base64
        token_data = base64.b64decode(token.encode()).decode()
        payload = json.loads(token_data)
        return payload
    except:
        return None

class TicketsAPI(BaseHTTPRequestHandler):
    
    def _set_cors_headers(self):
        """Configurar headers CORS"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        
    def _send_json_response(self, data: Any, status_code: int = 200):
        """Enviar respuesta JSON"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
        
    def _get_request_data(self) -> Dict:
        """Obtener datos del request"""
        try:
            content_length = int(self.headers.get('content-length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length)
                body_str = body.decode('utf-8')
                return json.loads(body_str)
            return {}
        except Exception as e:
            return {}
            
    def _verify_token(self) -> Optional[Dict]:
        """Verificar token"""
        try:
            auth_header = self.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return None
            
            token = auth_header.split(' ')[1]
            return verify_simple_token(token)
        except:
            return None

    def do_OPTIONS(self):
        """Manejar CORS preflight"""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        """Manejar GET requests"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            
            if path == '/' or path == '/api':
                response = {
                    "status": "working",
                    "message": "API completa con configuración - Version 10",
                    "endpoints": {
                        "auth": ["/auth/login", "/auth/me"],
                        "tickets": ["/tickets", "/tickets/{id}"],
                        "usuarios": ["/usuarios", "/usuarios/{id}"],
                        "config": ["/config"]
                    }
                }
                self._send_json_response(response)
                
            elif path == '/health':
                self._send_json_response({"status": "ok", "version": "10"})
                
            elif path == '/config':
                # Configuración pública (sin autenticación necesaria)
                public_config = {
                    "empresa": SYSTEM_CONFIG["empresa"],
                    "mensajes": SYSTEM_CONFIG["mensajes"],
                    "apariencia": SYSTEM_CONFIG["apariencia"],
                    "tickets": {
                        "estados": SYSTEM_CONFIG["tickets"]["estados"],
                        "prioridades": SYSTEM_CONFIG["tickets"]["prioridades"],
                        "categorias": SYSTEM_CONFIG["tickets"]["categorias"]
                    }
                }
                self._send_json_response(public_config)
                
            elif path == '/auth/me':
                user = self._verify_token()
                if not user:
                    self._send_json_response({"error": "Token inválido"}, 401)
                    return
                    
                user_data = next((u for u in USERS_DB.values() if u['id'] == user['user_id']), None)
                if user_data:
                    safe_user = {k: v for k, v in user_data.items() if k != 'password_hash'}
                    self._send_json_response(safe_user)
                else:
                    self._send_json_response({"error": "Usuario no encontrado"}, 404)
                    
            elif path == '/tickets':
                user = self._verify_token()
                if not user:
                    self._send_json_response({"error": "Token requerido"}, 401)
                    return
                    
                tickets_list = list(TICKETS_DB.values())
                # Filtrar tickets según rol
                if user['role'] != 'admin':
                    tickets_list = [t for t in tickets_list if t['creado_por'] == user['user_id'] or t.get('asignado_a') == user['user_id']]
                    
                self._send_json_response(tickets_list)
                
            elif path.startswith('/tickets/'):
                user = self._verify_token()
                if not user:
                    self._send_json_response({"error": "Token requerido"}, 401)
                    return
                    
                ticket_id = int(path.split('/')[-1])
                if ticket_id in TICKETS_DB:
                    ticket = TICKETS_DB[ticket_id]
                    # Verificar permisos
                    if user['role'] == 'admin' or ticket['creado_por'] == user['user_id'] or ticket.get('asignado_a') == user['user_id']:
                        self._send_json_response(ticket)
                    else:
                        self._send_json_response({"error": "Sin permisos"}, 403)
                else:
                    self._send_json_response({"error": "Ticket no encontrado"}, 404)
                    
            elif path == '/usuarios':
                user = self._verify_token()
                if not user or user['role'] != 'admin':
                    self._send_json_response({"error": "Acceso denegado - Solo administradores"}, 403)
                    return
                    
                users_list = [{k: v for k, v in user.items() if k != 'password_hash'} 
                             for user in USERS_DB.values()]
                self._send_json_response(users_list)
                
            else:
                self._send_json_response({"error": "Endpoint no encontrado"}, 404)
                
        except Exception as e:
            self._send_json_response({"error": "Error interno", "details": str(e)}, 500)

    def do_POST(self):
        """Manejar POST requests"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            data = self._get_request_data()
            
            if path == '/auth/login':
                email = data.get('username')  
                password = data.get('password')
                
                if not email or not password:
                    self._send_json_response({
                        "error": "Email y contraseña requeridos"
                    }, 400)
                    return
                    
                user = USERS_DB.get(email)
                if not user:
                    self._send_json_response({"error": "Usuario no encontrado"}, 401)
                    return
                    
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                if password_hash != user['password_hash']:
                    self._send_json_response({"error": "Contraseña incorrecta"}, 401)
                    return
                    
                if not user['activo']:
                    self._send_json_response({"error": "Usuario desactivado"}, 401)
                    return
                    
                token = create_simple_token(user)
                response = {
                    "access_token": token,
                    "token_type": "bearer",
                    "user": {k: v for k, v in user.items() if k != 'password_hash'}
                }
                self._send_json_response(response)
                
            elif path == '/tickets':
                user = self._verify_token()
                if not user:
                    self._send_json_response({"error": "Token requerido"}, 401)
                    return
                    
                # Crear nuevo ticket
                new_id = max(TICKETS_DB.keys()) + 1 if TICKETS_DB else 1
                new_ticket = {
                    "id": new_id,
                    "titulo": data.get('titulo'),
                    "descripcion": data.get('descripcion'),
                    "estado": "abierto",
                    "prioridad": data.get('prioridad', 'media'),
                    "creado_por": user['user_id'],
                    "fecha_creacion": datetime.datetime.utcnow().isoformat() + 'Z',
                    "categoria": data.get('categoria', 'general'),
                    "asignado_a": data.get('asignado_a')
                }
                TICKETS_DB[new_id] = new_ticket
                self._send_json_response(new_ticket, 201)
                
            else:
                self._send_json_response({"error": "Endpoint no encontrado"}, 404)
                
        except Exception as e:
            self._send_json_response({"error": "Error interno", "details": str(e)}, 500)

    def do_PUT(self):
        """Manejar PUT requests"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            data = self._get_request_data()
            
            user = self._verify_token()
            if not user:
                self._send_json_response({"error": "Token requerido"}, 401)
                return
                
            if path == '/config':
                # Solo admin puede cambiar configuración
                if user['role'] != 'admin':
                    self._send_json_response({"error": "Solo administradores pueden cambiar la configuración"}, 403)
                    return
                    
                # Actualizar configuración
                for key, value in data.items():
                    if key in SYSTEM_CONFIG:
                        if isinstance(SYSTEM_CONFIG[key], dict) and isinstance(value, dict):
                            SYSTEM_CONFIG[key].update(value)
                        else:
                            SYSTEM_CONFIG[key] = value
                            
                self._send_json_response({"message": "Configuración actualizada", "config": SYSTEM_CONFIG})
                
            elif path.startswith('/tickets/'):
                ticket_id = int(path.split('/')[-1])
                if ticket_id not in TICKETS_DB:
                    self._send_json_response({"error": "Ticket no encontrado"}, 404)
                    return
                    
                ticket = TICKETS_DB[ticket_id]
                
                # Verificar permisos
                if user['role'] != 'admin' and ticket['creado_por'] != user['user_id']:
                    self._send_json_response({"error": "Sin permisos para editar este ticket"}, 403)
                    return
                    
                # Actualizar ticket
                for key, value in data.items():
                    if key in ['titulo', 'descripcion', 'estado', 'prioridad', 'asignado_a', 'categoria']:
                        ticket[key] = value
                        
                self._send_json_response(ticket)
                
            else:
                self._send_json_response({"error": "Endpoint no encontrado"}, 404)
                
        except Exception as e:
            self._send_json_response({"error": "Error interno", "details": str(e)}, 500)

    def do_DELETE(self):
        """Manejar DELETE requests"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            
            user = self._verify_token()
            if not user:
                self._send_json_response({"error": "Token requerido"}, 401)
                return
                
            if path.startswith('/tickets/'):
                ticket_id = int(path.split('/')[-1])
                if ticket_id not in TICKETS_DB:
                    self._send_json_response({"error": "Ticket no encontrado"}, 404)
                    return
                
                # Solo admin puede eliminar tickets
                if user['role'] != 'admin':
                    self._send_json_response({"error": "Solo administradores pueden eliminar tickets"}, 403)
                    return
                    
                del TICKETS_DB[ticket_id]
                self._send_json_response({"message": "Ticket eliminado"})
                
            else:
                self._send_json_response({"error": "Endpoint no encontrado"}, 404)
                
        except Exception as e:
            self._send_json_response({"error": "Error interno", "details": str(e)}, 500)

# Handler principal para Vercel
handler = TicketsAPI