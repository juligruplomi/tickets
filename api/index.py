from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import datetime
import os
from typing import Dict, Any, Optional
import jwt
import bcrypt
import requests

# Configuración del PROXY HTTP (no conexión directa a PostgreSQL)
PROXY_URL = os.getenv("PROXY_URL", "http://185.194.59.40:3001")
PROXY_API_KEY = os.getenv("PROXY_API_KEY", "GrupLomi2024ProxySecureKey_XyZ789")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "GrupLomi_JWT_Secret_Key_2024_Very_Secure_Hash")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

def db_query(text: str, params: list = None):
    """Ejecutar query a través del proxy HTTP"""
    try:
        response = requests.post(
            f"{PROXY_URL}/query",
            json={"text": text, "params": params or []},
            headers={"x-api-key": PROXY_API_KEY},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return data.get("rows", [])
    except Exception as e:
        print(f"Error en db_query: {e}")
        return []

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except:
        return False

def create_token(user_data: Dict) -> str:
    payload = {
        'user_id': user_data['id'],
        'email': user_data['email'],
        'role': user_data['role'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Optional[Dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        return None

class handler(BaseHTTPRequestHandler):
    
    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        
    def _send_json_response(self, data: Any, status_code: int = 200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode('utf-8'))
        
    def _get_request_data(self) -> Dict:
        try:
            content_length = int(self.headers.get('content-length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length)
                return json.loads(body.decode('utf-8'))
            return {}
        except:
            return {}
            
    def _verify_token(self) -> Optional[Dict]:
        try:
            auth_header = self.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return None
            token = auth_header.split(' ')[1]
            return verify_token(token)
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
                self._send_json_response({
                    "message": "API de Gastos GrupLomi v2.0 - Proxy HTTP",
                    "status": "online",
                    "version": "2.0.0",
                    "database": "PostgreSQL via Proxy"
                })
                
            elif path == '/health':
                try:
                    response = requests.get(f"{PROXY_URL}/health", timeout=5)
                    proxy_status = "connected" if response.status_code == 200 else "error"
                except:
                    proxy_status = "disconnected"
                
                self._send_json_response({
                    "status": "healthy" if proxy_status == "connected" else "unhealthy",
                    "proxy_status": proxy_status,
                    "timestamp": datetime.datetime.utcnow().isoformat()
                })
                
            elif path == '/auth/me':
                user_token = self._verify_token()
                if not user_token:
                    self._send_json_response({"error": "Token inválido"}, 401)
                    return
                
                rows = db_query("SELECT * FROM usuarios WHERE id = $1", [user_token['user_id']])
                if rows:
                    user = dict(rows[0])
                    user.pop('password_hash', None)
                    self._send_json_response(user)
                else:
                    self._send_json_response({"error": "Usuario no encontrado"}, 404)
            
            elif path == '/gastos':
                user_token = self._verify_token()
                if not user_token:
                    self._send_json_response({"error": "Token requerido"}, 401)
                    return
                
                if user_token['role'] == 'empleado':
                    rows = db_query("SELECT * FROM gastos WHERE creado_por = $1 ORDER BY fecha_creacion DESC", [user_token['user_id']])
                elif user_token['role'] == 'supervisor':
                    rows = db_query("SELECT * FROM gastos WHERE creado_por = $1 OR supervisor_asignado = $1 ORDER BY fecha_creacion DESC", [user_token['user_id']])
                else:
                    rows = db_query("SELECT * FROM gastos ORDER BY fecha_creacion DESC")
                
                self._send_json_response([dict(r) for r in rows])
            
            elif path == '/usuarios':
                user_token = self._verify_token()
                if not user_token or user_token['role'] != 'admin':
                    self._send_json_response({"error": "Sin permisos"}, 403)
                    return
                
                rows = db_query("SELECT id, email, nombre, apellidos, role, departamento, telefono, activo FROM usuarios")
                self._send_json_response([dict(r) for r in rows])
            
            elif path == '/roles':
                user_token = self._verify_token()
                if not user_token:
                    self._send_json_response({"error": "Token requerido"}, 401)
                    return
                
                roles = [
                    {"id": "admin", "nombre": "Administrador", "permisos": ["all"]},
                    {"id": "supervisor", "nombre": "Supervisor", "permisos": ["aprobar_gastos", "ver_reportes"]},
                    {"id": "empleado", "nombre": "Empleado", "permisos": ["crear_gastos", "ver_mis_gastos"]},
                    {"id": "contabilidad", "nombre": "Contabilidad", "permisos": ["ver_gastos", "exportar", "ver_reportes"]}
                ]
                self._send_json_response(roles)
            
            elif path == '/reportes/gastos':
                user_token = self._verify_token()
                if not user_token:
                    self._send_json_response({"error": "Token requerido"}, 401)
                    return
                
                rows = db_query("SELECT * FROM gastos ORDER BY fecha_creacion DESC")
                self._send_json_response([dict(r) for r in rows])
            
            elif path == '/config/sistema':
                user_token = self._verify_token()
                if not user_token or user_token['role'] != 'admin':
                    self._send_json_response({"error": "Sin permisos"}, 403)
                    return
                
                self._send_json_response({
                    "nombre_sistema": "GrupLomi Gastos",
                    "version": "2.0.0",
                    "modo_mantenimiento": False
                })
            
            elif path == '/reportes/dashboard':
                user_token = self._verify_token()
                if not user_token:
                    self._send_json_response({"error": "Token requerido"}, 401)
                    return
                
                total_gastos_rows = db_query("SELECT COUNT(*) as total FROM gastos")
                total_gastos = total_gastos_rows[0]['total'] if total_gastos_rows else 0
                
                total_importe_rows = db_query("SELECT SUM(importe) as total FROM gastos")
                total_importe = float(total_importe_rows[0]['total'] or 0) if total_importe_rows else 0
                
                pendientes_rows = db_query("SELECT COUNT(*) as total FROM gastos WHERE estado = $1", ['pendiente'])
                pendientes = pendientes_rows[0]['total'] if pendientes_rows else 0
                
                aprobados_rows = db_query("SELECT COUNT(*) as total FROM gastos WHERE estado = $1", ['aprobado'])
                aprobados = aprobados_rows[0]['total'] if aprobados_rows else 0
                
                dietas_rows = db_query("SELECT COUNT(*) as total FROM gastos WHERE tipo_gasto = $1", ['dieta'])
                dietas = dietas_rows[0]['total'] if dietas_rows else 0
                
                aparcamiento_rows = db_query("SELECT COUNT(*) as total FROM gastos WHERE tipo_gasto = $1", ['aparcamiento'])
                aparcamiento = aparcamiento_rows[0]['total'] if aparcamiento_rows else 0
                
                gasolina_rows = db_query("SELECT COUNT(*) as total FROM gastos WHERE tipo_gasto = $1", ['gasolina'])
                gasolina = gasolina_rows[0]['total'] if gasolina_rows else 0
                
                otros_rows = db_query("SELECT COUNT(*) as total FROM gastos WHERE tipo_gasto NOT IN ($1, $2, $3)", ['dieta', 'aparcamiento', 'gasolina'])
                otros = otros_rows[0]['total'] if otros_rows else 0
                
                self._send_json_response({
                    "total_gastos": total_gastos,
                    "total_importe": total_importe,
                    "pendientes": pendientes,
                    "aprobados": aprobados,
                    "por_tipo": {
                        "dietas": dietas,
                        "aparcamiento": aparcamiento,
                        "gasolina": gasolina,
                        "otros": otros
                    }
                })
            
            elif path == '/config':
                self._send_json_response({
                    "modo_oscuro": False,
                    "idioma_principal": "es",
                    "nombre_empresa": "GrupLomi",
                    "logo_url": "",
                    "color_primario": "#0066CC",
                    "color_secundario": "#f8f9fa",
                    "color_acento": "#28a745",
                    "metodos_pago": ["efectivo", "tarjeta", "transferencia"],
                    "limite_gasto_diario": 500,
                    "limite_gasto_mensual": 5000,
                    "categorias_gasto": [
                        {"id": "dieta", "nombre": "Dietas", "activo": True},
                        {"id": "gasolina", "nombre": "Combustible", "activo": True},
                        {"id": "aparcamiento", "nombre": "Aparcamiento", "activo": True},
                        {"id": "hotel", "nombre": "Alojamiento", "activo": True},
                        {"id": "transporte", "nombre": "Transporte", "activo": True},
                        {"id": "material", "nombre": "Material", "activo": True},
                        {"id": "formacion", "nombre": "Formación", "activo": True},
                        {"id": "otros", "nombre": "Otros", "activo": True}
                    ],
                    "idiomas": {
                        "es": {"activo": True, "nombre": "Español"},
                        "en": {"activo": True, "nombre": "English"},
                        "ca": {"activo": True, "nombre": "Català"},
                        "de": {"activo": True, "nombre": "Deutsch"},
                        "it": {"activo": True, "nombre": "Italiano"},
                        "pt": {"activo": True, "nombre": "Português"}
                    },
                    "notificaciones": {
                        "email_activo": False,
                        "smtp_host": "",
                        "smtp_port": 587,
                        "smtp_user": "",
                        "smtp_password": "",
                        "eventos": {
                            "nuevo_gasto": True,
                            "gasto_aprobado": True,
                            "gasto_rechazado": True
                        }
                    }
                })
            
            else:
                self._send_json_response({"error": "Endpoint no encontrado"}, 404)
                
        except Exception as e:
            print(f"Error en GET: {e}")
            self._send_json_response({"error": "Error interno", "details": str(e)}, 500)

    def do_POST(self):
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            data = self._get_request_data()
            
            if path == '/auth/login':
                email = data.get('email') or data.get('username')
                password = data.get('password')
                
                if not email or not password:
                    self._send_json_response({"error": "Email y contraseña requeridos"}, 400)
                    return
                
                rows = db_query("SELECT * FROM usuarios WHERE email = $1", [email])
                
                if not rows:
                    self._send_json_response({"error": "Credenciales incorrectas"}, 401)
                    return
                
                user = dict(rows[0])
                
                if not verify_password(password, user['password_hash']):
                    self._send_json_response({"error": "Credenciales incorrectas"}, 401)
                    return
                
                if not user.get('activo', True):
                    self._send_json_response({"error": "Usuario desactivado"}, 401)
                    return
                
                token = create_token(user)
                user.pop('password_hash', None)
                
                self._send_json_response({
                    "access_token": token,
                    "token_type": "bearer",
                    "user": user
                })
            
            elif path == '/gastos':
                user_token = self._verify_token()
                if not user_token:
                    self._send_json_response({"error": "Token requerido"}, 401)
                    return
                
                rows = db_query("""
                    INSERT INTO gastos (tipo_gasto, descripcion, obra, importe, fecha_gasto, creado_por, estado)
                    VALUES ($1, $2, $3, $4, $5, $6, 'pendiente')
                    RETURNING *
                """, [
                    data.get('tipo_gasto'),
                    data.get('descripcion'),
                    data.get('obra'),
                    data.get('importe'),
                    data.get('fecha_gasto'),
                    user_token['user_id']
                ])
                
                if rows:
                    self._send_json_response(dict(rows[0]), 201)
                else:
                    self._send_json_response({"error": "Error al crear gasto"}, 500)
            
            else:
                self._send_json_response({"error": "Endpoint no encontrado"}, 404)
                
        except Exception as e:
            print(f"Error en POST: {e}")
            self._send_json_response({"error": "Error interno", "details": str(e)}, 500)

    def do_PUT(self):
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            data = self._get_request_data()
            
            user_token = self._verify_token()
            if not user_token:
                self._send_json_response({"error": "Token requerido"}, 401)
                return
            
            if path.startswith('/gastos/'):
                gasto_id = path.split('/')[-1]
                
                gasto_rows = db_query("SELECT * FROM gastos WHERE id = $1", [gasto_id])
                if not gasto_rows:
                    self._send_json_response({"error": "Gasto no encontrado"}, 404)
                    return
                
                gasto = dict(gasto_rows[0])
                
                if user_token['role'] == 'empleado' and gasto['creado_por'] != user_token['user_id']:
                    self._send_json_response({"error": "Sin permisos"}, 403)
                    return
                
                if data.get('estado') and user_token['role'] in ['admin', 'supervisor']:
                    updated_rows = db_query("UPDATE gastos SET estado = $1 WHERE id = $2 RETURNING *", [data['estado'], gasto_id])
                    if updated_rows:
                        self._send_json_response(dict(updated_rows[0]))
                    else:
                        self._send_json_response({"error": "Error al actualizar"}, 500)
                else:
                    self._send_json_response({"error": "Sin permisos"}, 403)
            
            elif path.startswith('/usuarios/'):
                if user_token['role'] != 'admin':
                    self._send_json_response({"error": "Sin permisos"}, 403)
                    return
                
                user_id = path.split('/')[-1]
                
                updates = []
                params = []
                param_count = 1
                
                if 'nombre' in data:
                    updates.append(f"nombre = ${param_count}")
                    params.append(data['nombre'])
                    param_count += 1
                if 'apellidos' in data:
                    updates.append(f"apellidos = ${param_count}")
                    params.append(data['apellidos'])
                    param_count += 1
                if 'email' in data:
                    updates.append(f"email = ${param_count}")
                    params.append(data['email'])
                    param_count += 1
                if 'role' in data:
                    updates.append(f"role = ${param_count}")
                    params.append(data['role'])
                    param_count += 1
                if 'departamento' in data:
                    updates.append(f"departamento = ${param_count}")
                    params.append(data['departamento'])
                    param_count += 1
                if 'telefono' in data:
                    updates.append(f"telefono = ${param_count}")
                    params.append(data['telefono'])
                    param_count += 1
                if 'activo' in data:
                    updates.append(f"activo = ${param_count}")
                    params.append(data['activo'])
                    param_count += 1
                
                if updates:
                    params.append(user_id)
                    query = f"UPDATE usuarios SET {', '.join(updates)} WHERE id = ${param_count} RETURNING id, email, nombre, apellidos, role, departamento, telefono, activo"
                    updated_rows = db_query(query, params)
                    if updated_rows:
                        self._send_json_response(dict(updated_rows[0]))
                    else:
                        self._send_json_response({"error": "Error al actualizar"}, 500)
                else:
                    self._send_json_response({"error": "No hay datos para actualizar"}, 400)
            
            elif path == '/config/gastos':
                if user_token['role'] != 'admin':
                    self._send_json_response({"error": "Sin permisos"}, 403)
                    return
                
                self._send_json_response({"message": "Configuración guardada correctamente"})
            
            else:
                self._send_json_response({"error": "Endpoint no encontrado"}, 404)
                
        except Exception as e:
            print(f"Error en PUT: {e}")
            self._send_json_response({"error": "Error interno", "details": str(e)}, 500)

    def do_DELETE(self):
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            
            user_token = self._verify_token()
            if not user_token:
                self._send_json_response({"error": "Token requerido"}, 401)
                return
            
            if path.startswith('/gastos/'):
                gasto_id = path.split('/')[-1]
                
                gasto_rows = db_query("SELECT * FROM gastos WHERE id = $1", [gasto_id])
                if not gasto_rows:
                    self._send_json_response({"error": "Gasto no encontrado"}, 404)
                    return
                
                gasto = dict(gasto_rows[0])
                
                if user_token['role'] != 'admin' and gasto['creado_por'] != user_token['user_id']:
                    self._send_json_response({"error": "Sin permisos"}, 403)
                    return
                
                db_query("DELETE FROM gastos WHERE id = $1", [gasto_id])
                self._send_json_response({"message": "Gasto eliminado correctamente"})
            
            else:
                self._send_json_response({"error": "Endpoint no encontrado"}, 404)
                
        except Exception as e:
            print(f"Error en DELETE: {e}")
            self._send_json_response({"error": "Error interno", "details": str(e)}, 500)