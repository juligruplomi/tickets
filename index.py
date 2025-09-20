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
    # Token simple sin encriptación real para testing
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
        """Obtener datos del request con debugging"""
        try:
            content_length = int(self.headers.get('content-length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length)
                body_str = body.decode('utf-8')
                
                # Log para debugging
                print(f"DEBUG - Request body: {body_str}")
                print(f"DEBUG - Content-Type: {self.headers.get('content-type')}")
                
                return json.loads(body_str)
            return {}
        except Exception as e:
            print(f"DEBUG - Error parsing request: {str(e)}")
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
                    "message": "API completa funcionando - Version 9 DEBUG",
                    "endpoints": {
                        "auth": ["/auth/login", "/auth/me"],
                        "tickets": ["/tickets", "/tickets/{id}"],
                        "usuarios": ["/usuarios", "/usuarios/{id}"]
                    }
                }
                self._send_json_response(response)
                
            elif path == '/health':
                self._send_json_response({"status": "ok", "version": "9"})
                
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
                self._send_json_response(tickets_list)
                
            else:
                self._send_json_response({"error": "Endpoint no encontrado"}, 404)
                
        except Exception as e:
            self._send_json_response({"error": "Error interno", "details": str(e)}, 500)

    def do_POST(self):
        """Manejar POST requests"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            
            print(f"DEBUG - POST to {path}")
            
            if path == '/auth/login':
                data = self._get_request_data()
                print(f"DEBUG - Login data received: {data}")
                
                email = data.get('username')  
                password = data.get('password')
                
                print(f"DEBUG - Email: {email}, Password: {'***' if password else 'None'}")
                
                if not email or not password:
                    self._send_json_response({
                        "error": "Email y contraseña requeridos",
                        "received_data": data
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
                
            else:
                self._send_json_response({"error": "Endpoint no encontrado"}, 404)
                
        except Exception as e:
            print(f"DEBUG - Error in POST: {str(e)}")
            self._send_json_response({"error": "Error interno", "details": str(e)}, 500)

    def do_PUT(self):
        self.do_GET()

    def do_DELETE(self):
        self.do_GET()

# Handler principal para Vercel
handler = TicketsAPI