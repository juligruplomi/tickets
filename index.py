from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import datetime
import os
from typing import Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import jwt
import bcrypt

# Configuración de base de datos externa
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://gruplomi_user:GrupLomi2024#Secure!@185.194.59.40:5432/gruplomi_tickets")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "GrupLomi_JWT_Secret_Key_2024_Very_Secure_Hash")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

def get_db_connection():
    """Conectar a PostgreSQL"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Error conectando a BD: {e}")
        return None

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

class GrupLomiAPI(BaseHTTPRequestHandler):
    
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
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            # ===== ENDPOINTS PRINCIPALES =====
            
            if path == '/' or path == '/api':
                self._send_json_response({
                    "message": "API de Gastos GrupLomi v2.0 - PostgreSQL",
                    "status": "online",
                    "version": "2.0.0",
                    "database": "PostgreSQL Externo"
                })
                
            elif path == '/health':
                conn = get_db_connection()
                if conn:
                    conn.close()
                    self._send_json_response({"status": "healthy", "database": "connected"})
                else:
                    self._send_json_response({"status": "unhealthy", "database": "disconnected"}, 500)
                
            # ===== AUTENTICACIÓN =====
            
            elif path == '/auth/me':
                user_token = self._verify_token()
                if not user_token:
                    self._send_json_response({"error": "Token inválido"}, 401)
                    return
                
                conn = get_db_connection()
                if not conn:
                    self._send_json_response({"error": "Error de conexión"}, 500)
                    return
                
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute("SELECT * FROM usuarios WHERE id = %s", (user_token['user_id'],))
                user = cur.fetchone()
                cur.close()
                conn.close()
                
                if user:
                    user_dict = dict(user)
                    user_dict.pop('password_hash', None)
                    self._send_json_response(user_dict)
                else:
                    self._send_json_response({"error": "Usuario no encontrado"}, 404)
            
            # ===== GASTOS =====
            
            elif path == '/gastos':
                user_token = self._verify_token()
                if not user_token:
                    self._send_json_response({"error": "Token requerido"}, 401)
                    return
                
                conn = get_db_connection()
                if not conn:
                    self._send_json_response({"error": "Error de conexión"}, 500)
                    return
                
                cur = conn.cursor(cursor_factory=RealDictCursor)
                
                # Filtrar gastos según rol
                if user_token['role'] == 'empleado':
                    cur.execute("SELECT * FROM gastos WHERE creado_por = %s ORDER BY fecha_creacion DESC", 
                              (user_token['user_id'],))
                elif user_token['role'] == 'supervisor':
                    cur.execute("SELECT * FROM gastos WHERE creado_por = %s OR supervisor_asignado = %s ORDER BY fecha_creacion DESC", 
                              (user_token['user_id'], user_token['user_id']))
                else:
                    cur.execute("SELECT * FROM gastos ORDER BY fecha_creacion DESC")
                
                gastos = cur.fetchall()
                cur.close()
                conn.close()
                
                self._send_json_response([dict(g) for g in gastos])
            
            # ===== USUARIOS =====
            
            elif path == '/usuarios':
                user_token = self._verify_token()
                if not user_token or user_token['role'] != 'admin':
                    self._send_json_response({"error": "Sin permisos"}, 403)
                    return
                
                conn = get_db_connection()
                if not conn:
                    self._send_json_response({"error": "Error de conexión"}, 500)
                    return
                
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute("SELECT id, email, nombre, apellidos, role, departamento, telefono, activo FROM usuarios")
                usuarios = cur.fetchall()
                cur.close()
                conn.close()
                
                self._send_json_response([dict(u) for u in usuarios])
            
            # ===== DASHBOARD =====
            
            elif path == '/reportes/dashboard':
                user_token = self._verify_token()
                if not user_token:
                    self._send_json_response({"error": "Token requerido"}, 401)
                    return
                
                conn = get_db_connection()
                if not conn:
                    self._send_json_response({"error": "Error de conexión"}, 500)
                    return
                
                cur = conn.cursor(cursor_factory=RealDictCursor)
                
                # Estadísticas básicas
                cur.execute("SELECT COUNT(*) as total FROM gastos")
                total_gastos = cur.fetchone()['total']
                
                cur.execute("SELECT SUM(importe) as total FROM gastos")
                total_importe = cur.fetchone()['total'] or 0
                
                cur.execute("SELECT COUNT(*) as total FROM gastos WHERE estado = 'pendiente'")
                pendientes = cur.fetchone()['total']
                
                cur.execute("SELECT COUNT(*) as total FROM gastos WHERE estado = 'aprobado'")
                aprobados = cur.fetchone()['total']
                
                cur.close()
                conn.close()
                
                self._send_json_response({
                    "total_gastos": total_gastos,
                    "total_importe": float(total_importe),
                    "pendientes": pendientes,
                    "aprobados": aprobados
                })
            
            # ===== CONFIGURACIÓN (estructura corregida para el frontend) =====
            
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
            
            # ===== LOGIN =====
            
            if path == '/auth/login':
                email = data.get('email') or data.get('username')
                password = data.get('password')
                
                if not email or not password:
                    self._send_json_response({"error": "Email y contraseña requeridos"}, 400)
                    return
                
                conn = get_db_connection()
                if not conn:
                    self._send_json_response({"error": "Error de conexión a la base de datos"}, 500)
                    return
                
                try:
                    cur = conn.cursor(cursor_factory=RealDictCursor)
                    cur.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
                    user = cur.fetchone()
                    cur.close()
                    conn.close()
                    
                    if not user or not verify_password(password, user['password_hash']):
                        self._send_json_response({"error": "Credenciales incorrectas"}, 401)
                        return
                    
                    if not user.get('activo', True):
                        self._send_json_response({"error": "Usuario desactivado"}, 401)
                        return
                    
                    token = create_token(user)
                    user_dict = dict(user)
                    user_dict.pop('password_hash', None)
                    
                    self._send_json_response({
                        "access_token": token,
                        "token_type": "bearer",
                        "user": user_dict
                    })
                except Exception as e:
                    print(f"Error en login: {e}")
                    self._send_json_response({"error": "Error al procesar login", "details": str(e)}, 500)
            
            # ===== CREAR GASTO =====
            
            elif path == '/gastos':
                user_token = self._verify_token()
                if not user_token:
                    self._send_json_response({"error": "Token requerido"}, 401)
                    return
                
                conn = get_db_connection()
                if not conn:
                    self._send_json_response({"error": "Error de conexión"}, 500)
                    return
                
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute("""
                    INSERT INTO gastos (tipo_gasto, descripcion, obra, importe, fecha_gasto, creado_por, estado)
                    VALUES (%s, %s, %s, %s, %s, %s, 'pendiente')
                    RETURNING *
                """, (
                    data.get('tipo_gasto'),
                    data.get('descripcion'),
                    data.get('obra'),
                    data.get('importe'),
                    data.get('fecha_gasto'),
                    user_token['user_id']
                ))
                gasto = cur.fetchone()
                conn.commit()
                cur.close()
                conn.close()
                
                self._send_json_response(dict(gasto), 201)
            
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
            
            # ===== ACTUALIZAR GASTO =====
            
            if path.startswith('/gastos/'):
                gasto_id = path.split('/')[-1]
                
                conn = get_db_connection()
                if not conn:
                    self._send_json_response({"error": "Error de conexión"}, 500)
                    return
                
                cur = conn.cursor(cursor_factory=RealDictCursor)
                
                # Verificar permisos
                cur.execute("SELECT * FROM gastos WHERE id = %s", (gasto_id,))
                gasto = cur.fetchone()
                
                if not gasto:
                    cur.close()
                    conn.close()
                    self._send_json_response({"error": "Gasto no encontrado"}, 404)
                    return
                
                # Actualizar estado si tiene permisos
                if data.get('estado') and user_token['role'] in ['admin', 'supervisor']:
                    cur.execute("UPDATE gastos SET estado = %s WHERE id = %s RETURNING *", 
                              (data['estado'], gasto_id))
                    gasto_actualizado = cur.fetchone()
                    conn.commit()
                    cur.close()
                    conn.close()
                    self._send_json_response(dict(gasto_actualizado))
                else:
                    cur.close()
                    conn.close()
                    self._send_json_response({"error": "Sin permisos"}, 403)
            
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
            
            # ===== ELIMINAR GASTO =====
            
            if path.startswith('/gastos/'):
                gasto_id = path.split('/')[-1]
                
                conn = get_db_connection()
                if not conn:
                    self._send_json_response({"error": "Error de conexión"}, 500)
                    return
                
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute("SELECT * FROM gastos WHERE id = %s", (gasto_id,))
                gasto = cur.fetchone()
                
                if not gasto:
                    cur.close()
                    conn.close()
                    self._send_json_response({"error": "Gasto no encontrado"}, 404)
                    return
                
                # Solo admin o creador pueden eliminar
                if user_token['role'] != 'admin' and gasto['creado_por'] != user_token['user_id']:
                    cur.close()
                    conn.close()
                    self._send_json_response({"error": "Sin permisos"}, 403)
                    return
                
                cur.execute("DELETE FROM gastos WHERE id = %s", (gasto_id,))
                conn.commit()
                cur.close()
                conn.close()
                
                self._send_json_response({"message": "Gasto eliminado correctamente"})
            
            else:
                self._send_json_response({"error": "Endpoint no encontrado"}, 404)
                
        except Exception as e:
            print(f"Error en DELETE: {e}")
            self._send_json_response({"error": "Error interno", "details": str(e)}, 500)

handler = GrupLomiAPI
