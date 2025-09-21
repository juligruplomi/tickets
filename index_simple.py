from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import hashlib
import datetime

# Datos simulados
USERS_DB = {
    "admin@gruplomi.com": {
        "id": 1,
        "email": "admin@gruplomi.com",
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "nombre": "Carlos",
        "apellidos": "Administrador López",
        "role": "administrador",
        "activo": True,
        "idioma_preferido": "es"
    }
}

GASTOS_DB = {
    1: {
        "id": 1,
        "tipo_gasto": "dieta",
        "descripcion": "Almuerzo para equipo",
        "importe": 45.50,
        "fecha_gasto": "2025-01-20",
        "estado": "pendiente",
        "creado_por": 1
    }
}

SYSTEM_CONFIG = {
    "idioma": {
        "predeterminado": "es",
        "idiomas_disponibles": ["es", "en", "ca", "de", "it", "pt"],
        "traducciones": {
            "es": {"gastos": "Gastos", "dashboard": "Panel de Control"},
            "en": {"gastos": "Expenses", "dashboard": "Dashboard"},
            "ca": {"gastos": "Despeses", "dashboard": "Tauler de Control"},
            "de": {"gastos": "Ausgaben", "dashboard": "Dashboard"},
            "it": {"gastos": "Spese", "dashboard": "Dashboard"},
            "pt": {"gastos": "Despesas", "dashboard": "Painel"}
        }
    }
}

def create_simple_token(user_data):
    import base64
    payload = {
        'user_id': user_data['id'],
        'email': user_data['email'],
        'role': user_data['role']
    }
    token_data = json.dumps(payload)
    return base64.b64encode(token_data.encode()).decode()

def verify_simple_token(token):
    try:
        import base64
        token_data = base64.b64decode(token.encode()).decode()
        payload = json.loads(token_data)
        return payload
    except:
        return None

class GastosAPI(BaseHTTPRequestHandler):
    
    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        
    def _send_json_response(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
        
    def _get_request_data(self):
        try:
            content_length = int(self.headers.get('content-length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length)
                body_str = body.decode('utf-8')
                return json.loads(body_str)
            return {}
        except:
            return {}
            
    def _verify_token(self):
        try:
            auth_header = self.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return None
            token = auth_header.split(' ')[1]
            return verify_simple_token(token)
        except:
            return None

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            
            if path == '/' or path == '/api':
                response = {
                    "status": "working",
                    "message": "🏢 GrupLomi - Sistema de Gestión de Gastos - v1.0",
                    "version": "simplified"
                }
                self._send_json_response(response)
                
            elif path == '/health':
                self._send_json_response({"status": "ok", "version": "1.0"})
                
            elif path == '/config':
                user = self._verify_token()
                idioma = "es"
                
                if user:
                    user_data = USERS_DB.get(list(USERS_DB.keys())[0])
                    if user_data and 'idioma_preferido' in user_data:
                        idioma = user_data['idioma_preferido']
                
                config = {
                    "idioma": {
                        "actual": idioma,
                        "disponibles": SYSTEM_CONFIG["idioma"]["idiomas_disponibles"],
                        "traducciones": SYSTEM_CONFIG["idioma"]["traducciones"].get(idioma, SYSTEM_CONFIG["idioma"]["traducciones"]["es"])
                    }
                }
                self._send_json_response(config)
                
            elif path == '/auth/me':
                user = self._verify_token()
                if not user:
                    self._send_json_response({"error": "Token inválido"}, 401)
                    return
                    
                user_data = USERS_DB.get("admin@gruplomi.com")
                if user_data:
                    safe_user = {k: v for k, v in user_data.items() if k != 'password_hash'}
                    self._send_json_response(safe_user)
                else:
                    self._send_json_response({"error": "Usuario no encontrado"}, 404)
                    
            elif path == '/gastos':
                user = self._verify_token()
                if not user:
                    self._send_json_response({"error": "Token requerido"}, 401)
                    return
                    
                self._send_json_response(list(GASTOS_DB.values()))
                
            elif path == '/reportes/dashboard':
                user = self._verify_token()
                if not user:
                    self._send_json_response({"error": "Token requerido"}, 401)
                    return
                    
                dashboard_data = {
                    "total_gastos": len(GASTOS_DB),
                    "total_importe": sum(g['importe'] for g in GASTOS_DB.values()),
                    "pendientes": 1,
                    "aprobados": 0
                }
                self._send_json_response(dashboard_data)
                
            else:
                self._send_json_response({"error": "Endpoint no encontrado"}, 404)
                
        except Exception as e:
            self._send_json_response({"error": "Error interno", "details": str(e)}, 500)

    def do_POST(self):
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            data = self._get_request_data()
            
            if path == '/auth/login':
                email = data.get('username')  
                password = data.get('password')
                
                if not email or not password:
                    self._send_json_response({"error": "Email y contraseña requeridos"}, 400)
                    return
                    
                user = USERS_DB.get(email)
                if not user:
                    self._send_json_response({"error": "Usuario no encontrado"}, 401)
                    return
                    
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                if password_hash != user['password_hash']:
                    self._send_json_response({"error": "Contraseña incorrecta"}, 401)
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
            self._send_json_response({"error": "Error interno", "details": str(e)}, 500)

    def do_PUT(self):
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            data = self._get_request_data()
            
            user = self._verify_token()
            if not user:
                self._send_json_response({"error": "Token requerido"}, 401)
                return
                
            if path == '/config/language':
                nuevo_idioma = data.get('language')
                if not nuevo_idioma:
                    self._send_json_response({"error": "Idioma requerido"}, 400)
                    return
                    
                if nuevo_idioma not in SYSTEM_CONFIG['idioma']['idiomas_disponibles']:
                    self._send_json_response({"error": "Idioma no disponible"}, 400)
                    return
                    
                # Actualizar idioma del usuario
                for user_data in USERS_DB.values():
                    if user_data['id'] == user['user_id']:
                        user_data['idioma_preferido'] = nuevo_idioma
                        break
                    
                updated_config = {
                    "idioma": {
                        "actual": nuevo_idioma,
                        "disponibles": SYSTEM_CONFIG["idioma"]["idiomas_disponibles"],
                        "traducciones": SYSTEM_CONFIG["idioma"]["traducciones"].get(nuevo_idioma, SYSTEM_CONFIG["idioma"]["traducciones"]["es"])
                    }
                }
                self._send_json_response(updated_config)
                
            else:
                self._send_json_response({"error": "Endpoint no encontrado"}, 404)
                
        except Exception as e:
            self._send_json_response({"error": "Error interno", "details": str(e)}, 500)

handler = GastosAPI