from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import datetime
import os
from typing import Dict, Any, Optional
import jwt
import bcrypt
import requests

PROXY_URL = os.getenv("PROXY_URL", "http://185.194.59.40:3001")
PROXY_API_KEY = os.getenv("PROXY_API_KEY", "GrupLomi2024ProxySecureKey_XyZ789")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "GrupLomi_JWT_Secret_Key_2024_Very_Secure_Hash")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

def db_query(text: str, params: list = None):
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

class GrupLomiAPI(BaseHTTPRequestHandler):
    
    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS, PATCH')
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
                    "message": "API GrupLomi v2.3 - Fotos en BD",
                    "status": "online",
                    "version": "2.3.0"
                })
                
            elif path == '/health':
                try:
                    response = requests.get(f"{PROXY_URL}/health", timeout=5)
                    proxy_status = "connected" if response.status_code == 200 else "error"
                except:
                    proxy_status = "disconnected"
                
                self._send_json_response({
                    "status": "healthy" if proxy_status == "connected" else "unhealthy",
                    "proxy_status": proxy_status
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
            
            elif path.startswith('/gastos/') and path.count('/') == 2:
                gasto_id = path.split('/')[-1]
                user_token = self._verify_token()
                if not user_token:
                    self._send_json_response({"error": "Token requerido"}, 401)
                    return
                
                rows = db_query("SELECT * FROM gastos WHERE id = $1", [gasto_id])
                if rows:
                    self._send_json_response(dict(rows[0]))
                else:
                    self._send_json_response({"error": "Gasto no encontrado"}, 404)
            
            elif path == '/usuarios':
                user_token = self._verify_token()
                if not user_token or user_token['role'] != 'admin':
                    self._send_json_response({"error": "Sin permisos"}, 403)
                    return
                
                rows = db_query("SELECT id, email, nombre, apellidos, role, departamento, telefono, activo, foto_perfil FROM usuarios")
                self._send_json_response([dict(r) for r in rows])
            
            elif path.startswith('/usuarios/') and path.count('/') == 2:
                usuario_id = path.split('/')[-1]
                user_token = self._verify_token()
                if not user_token or user_token['role'] != 'admin':
                    self._send_json_response({"error": "Sin permisos"}, 403)
                    return
                
                rows = db_query("SELECT id, email, nombre, apellidos, role, departamento, telefono, activo, foto_perfil FROM usuarios WHERE id = $1", [usuario_id])
                if rows:
                    self._send_json_response(dict(rows[0]))
                else:
                    self._send_json_response({"error": "Usuario no encontrado"}, 404)
            
            elif path == '/roles':
                user_token = self._verify_token()
                if not user_token or user_token['role'] != 'admin':
                    self._send_json_response({"error": "Sin permisos"}, 403)
                    return
                
                # Leer roles desde la base de datos
                rows = db_query("SELECT role, permisos FROM roles_permisos ORDER BY role")
                
                roles = []
                for row in rows:
                    roles.append({
                        "id": row['role'],
                        "nombre": row['role'].capitalize(),
                        "permisos": row['permisos'] if isinstance(row['permisos'], list) else json.loads(row['permisos'])
                    })
                
                self._send_json_response(roles)
            
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
            
            elif path == '/reportes/gastos':
                user_token = self._verify_token()
                if not user_token:
                    self._send_json_response({"error": "Token requerido"}, 401)
                    return
                
                rows = db_query("SELECT * FROM gastos ORDER BY fecha_creacion DESC")
                self._send_json_response([dict(r) for r in rows])
            
            elif path == '/config' or path == '/config/sistema':
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
                    "limite_aprobacion_supervisor": 1000,
                    "requiere_justificante": True,
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
                
                # Guardar foto si existe
                foto_justificante = data.get('foto_justificante') or None
                
                rows = db_query("""
                    INSERT INTO gastos (tipo_gasto, descripcion, obra, importe, fecha_gasto, creado_por, estado, foto_justificante, foto_uploaded_at)
                    VALUES ($1, $2, $3, $4, $5, $6, 'pendiente', $7, $8)
                    RETURNING *
                """, [
                    data.get('tipo_gasto'),
                    data.get('descripcion'),
                    data.get('obra'),
                    data.get('importe'),
                    data.get('fecha_gasto'),
                    user_token['user_id'],
                    foto_justificante,
                    datetime.datetime.utcnow() if foto_justificante else None
                ])
                
                if rows:
                    self._send_json_response(dict(rows[0]), 201)
                else:
                    self._send_json_response({"error": "Error al crear gasto"}, 500)
            
            elif path == '/usuarios':
                user_token = self._verify_token()
                if not user_token or user_token['role'] != 'admin':
                    self._send_json_response({"error": "Sin permisos"}, 403)
                    return
                
                password_hash = hash_password(data.get('password', 'user123'))
                foto_perfil = data.get('foto_perfil') or None
                
                rows = db_query("""
                    INSERT INTO usuarios (email, nombre, apellidos, role, departamento, telefono, password_hash, activo, foto_perfil, foto_updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    RETURNING id, email, nombre, apellidos, role, departamento, telefono, activo, foto_perfil
                """, [
                    data.get('email'),
                    data.get('nombre'),
                    data.get('apellidos'),
                    data.get('role', 'empleado'),
                    data.get('departamento'),
                    data.get('telefono'),
                    password_hash,
                    data.get('activo', True),
                    foto_perfil,
                    datetime.datetime.utcnow() if foto_perfil else None
                ])
                
                if rows:
                    self._send_json_response(dict(rows[0]), 201)
                else:
                    self._send_json_response({"error": "Error al crear usuario"}, 500)
            
            # Limpiar fotos antiguas manualmente
            elif path == '/admin/limpiar-fotos':
                user_token = self._verify_token()
                if not user_token or user_token['role'] != 'admin':
                    self._send_json_response({"error": "Sin permisos"}, 403)
                    return
                
                db_query("SELECT limpiar_fotos_antiguas()")
                self._send_json_response({"message": "Fotos antiguas limpiadas correctamente"})
            
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
            
            if path.startswith('/gastos/') and path.count('/') == 2:
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
            
            elif path.startswith('/usuarios/') and path.count('/') == 2:
                usuario_id = path.split('/')[-1]
                
                if user_token['role'] != 'admin':
                    self._send_json_response({"error": "Sin permisos"}, 403)
                    return
                
                update_fields = []
                update_values = []
                
                for field in ['nombre', 'apellidos', 'email', 'role', 'departamento', 'telefono', 'activo']:
                    if field in data:
                        update_fields.append(f"{field} = ${len(update_values) + 1}")
                        update_values.append(data[field])
                
                if 'foto_perfil' in data:
                    update_fields.append(f"foto_perfil = ${len(update_values) + 1}")
                    update_values.append(data['foto_perfil'])
                    update_fields.append(f"foto_updated_at = ${len(update_values) + 1}")
                    update_values.append(datetime.datetime.utcnow())
                
                if 'password' in data and data['password']:
                    update_fields.append(f"password_hash = ${len(update_values) + 1}")
                    update_values.append(hash_password(data['password']))
                
                if not update_fields:
                    self._send_json_response({"error": "No hay campos para actualizar"}, 400)
                    return
                
                update_values.append(usuario_id)
                
                query = f"UPDATE usuarios SET {', '.join(update_fields)} WHERE id = ${len(update_values)} RETURNING id, email, nombre, apellidos, role, departamento, telefono, activo, foto_perfil"
                
                updated_rows = db_query(query, update_values)
                
                if updated_rows:
                    self._send_json_response(dict(updated_rows[0]))
                else:
                    self._send_json_response({"error": "Usuario no encontrado"}, 404)
            
            # Actualizar permisos de rol
            elif path.startswith('/roles/') and path.count('/') == 2:
                role_id = path.split('/')[-1]
                
                if user_token['role'] != 'admin':
                    self._send_json_response({"error": "Solo admin"}, 403)
                    return
                
                permisos = data.get('permisos', [])
                
                updated_rows = db_query(
                    "UPDATE roles_permisos SET permisos = $1, updated_at = $2 WHERE role = $3 RETURNING role, permisos",
                    [json.dumps(permisos), datetime.datetime.utcnow(), role_id]
                )
                
                if updated_rows:
                    self._send_json_response({
                        "message": "Permisos actualizados correctamente",
                        "role": updated_rows[0]['role'],
                        "permisos": permisos
                    })
                else:
                    self._send_json_response({"error": "Rol no encontrado"}, 404)
            
            elif path == '/config/gastos':
                if user_token['role'] != 'admin':
                    self._send_json_response({"error": "Solo admin"}, 403)
                    return
                
                self._send_json_response({"message": "Configuración actualizada"})
            
            elif path == '/config/notificaciones':
                if user_token['role'] != 'admin':
                    self._send_json_response({"error": "Solo admin"}, 403)
                    return
                
                self._send_json_response({"message": "Notificaciones actualizadas"})
            
            elif path == '/config/smtp':
                if user_token['role'] != 'admin':
                    self._send_json_response({"error": "Solo admin"}, 403)
                    return
                
                self._send_json_response({"message": "SMTP actualizado"})
            
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
            
            if path.startswith('/gastos/') and path.count('/') == 2:
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
                self._send_json_response({"message": "Gasto eliminado"})
            
            elif path.startswith('/usuarios/') and path.count('/') == 2:
                usuario_id = path.split('/')[-1]
                
                if user_token['role'] != 'admin':
                    self._send_json_response({"error": "Sin permisos"}, 403)
                    return
                
                if str(usuario_id) == str(user_token['user_id']):
                    self._send_json_response({"error": "No puedes eliminar tu propio usuario"}, 400)
                    return
                
                usuario_rows = db_query("SELECT id FROM usuarios WHERE id = $1", [usuario_id])
                if not usuario_rows:
                    self._send_json_response({"error": "Usuario no encontrado"}, 404)
                    return
                
                db_query("DELETE FROM usuarios WHERE id = $1", [usuario_id])
                self._send_json_response({"message": "Usuario eliminado"})
            
            else:
                self._send_json_response({"error": "Endpoint no encontrado"}, 404)
                
        except Exception as e:
            print(f"Error en DELETE: {e}")
            self._send_json_response({"error": "Error interno", "details": str(e)}, 500)

    def do_PATCH(self):
        self.do_PUT()

handler = GrupLomiAPI
