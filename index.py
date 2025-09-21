from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import hashlib
import datetime
import os
from typing import Dict, Any, Optional

# Datos simulados para el sistema de gastos
USERS_DB = {
    "admin@gruplomi.com": {
        "id": 1,
        "email": "admin@gruplomi.com",
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "nombre": "Carlos",
        "apellidos": "Administrador López",
        "codigo_empleado": "ADM001",
        "telefono": "+34 666 123 456",
        "direccion": "Calle Principal 123, Barcelona",
        "fecha_nacimiento": "1980-05-15",
        "fecha_contratacion": "2020-01-01",
        "foto_url": "/avatars/admin.jpg",
        "role": "administrador",
        "departamento": "IT",
        "supervisor_id": None,
        "activo": True,
        "idioma_preferido": "es",
        "permisos_especiales": ["gestion_usuarios", "configuracion_sistema", "reportes_avanzados"]
    },
    "supervisor@gruplomi.com": {
        "id": 2,
        "email": "supervisor@gruplomi.com", 
        "password_hash": hashlib.sha256("super123".encode()).hexdigest(),
        "nombre": "Juan",
        "apellidos": "Supervisor García",
        "codigo_empleado": "SUP001",
        "telefono": "+34 666 234 567",
        "direccion": "Avenida Central 456, Madrid",
        "fecha_nacimiento": "1975-08-22",
        "fecha_contratacion": "2020-03-15",
        "foto_url": "/avatars/supervisor.jpg",
        "role": "supervisor",
        "departamento": "Operaciones",
        "supervisor_id": 1,
        "activo": True,
        "idioma_preferido": "es",
        "permisos_especiales": ["aprobacion_gastos"]
    },
    "operario@gruplomi.com": {
        "id": 3,
        "email": "operario@gruplomi.com", 
        "password_hash": hashlib.sha256("opera123".encode()).hexdigest(),
        "nombre": "Carlos",
        "apellidos": "Operario Martínez",
        "codigo_empleado": "OPE001",
        "telefono": "+34 666 345 678",
        "direccion": "Calle Trabajo 789, Valencia",
        "fecha_nacimiento": "1990-12-10",
        "fecha_contratacion": "2021-06-01",
        "foto_url": "/avatars/operario.jpg",
        "role": "operario",
        "departamento": "Campo",
        "supervisor_id": 2,
        "activo": True,
        "idioma_preferido": "es",
        "permisos_especiales": []
    },
    "contabilidad@gruplomi.com": {
        "id": 4,
        "email": "contabilidad@gruplomi.com", 
        "password_hash": hashlib.sha256("conta123".encode()).hexdigest(),
        "nombre": "María",
        "apellidos": "Contable Fernández",
        "codigo_empleado": "CON001",
        "telefono": "+34 666 456 789",
        "direccion": "Plaza Finanzas 12, Sevilla",
        "fecha_nacimiento": "1985-03-18",
        "fecha_contratacion": "2020-09-01",
        "foto_url": "/avatars/contabilidad.jpg",
        "role": "contabilidad",
        "departamento": "Finanzas",
        "supervisor_id": 1,
        "activo": True,
        "idioma_preferido": "es",
        "permisos_especiales": ["gestion_pagos", "reportes_financieros"]
    }
}

# Base de datos de gastos/tickets
GASTOS_DB = {
    1: {
        "id": 1,
        "tipo_gasto": "dieta",
        "descripcion": "Almuerzo para equipo durante trabajo en obra Madrid",
        "obra": "Construcción Edificio Plaza",
        "importe": 45.50,
        "fecha_gasto": "2025-01-20",
        "estado": "pendiente",
        "creado_por": 3,
        "supervisor_asignado": 2,
        "fecha_creacion": "2025-01-20T10:00:00Z",
        "archivos_adjuntos": ["ticket_almuerzo_123.jpg"],
        "fecha_aprobacion": None,
        "aprobado_por": None,
        # Campos específicos para combustible
        "kilometros": None,
        "precio_km": None
    },
    2: {
        "id": 2,
        "tipo_gasto": "gasolina",
        "descripcion": "Desplazamiento a obra Barcelona",
        "obra": "Reparación Nave Industrial",
        "importe": 78.30,
        "fecha_gasto": "2025-01-19",
        "estado": "aprobado",
        "creado_por": 3,
        "supervisor_asignado": 2,
        "fecha_creacion": "2025-01-19T15:30:00Z",
        "archivos_adjuntos": [],
        "fecha_aprobacion": "2025-01-20T09:00:00Z",
        "aprobado_por": 2,
        # Campos específicos para combustible
        "kilometros": 156,
        "precio_km": 0.502
    }
}

# Configuración del sistema de gastos
SYSTEM_CONFIG = {
    "empresa": {
        "nombre": "GrupLomi",
        "logo_url": "/logo.png",
        "cif": "B12345678",
        "direccion": "Calle Empresa 123, Barcelona",
        "colores": {
            "primario": "#0066CC",
            "secundario": "#f8f9fa",
            "acento": "#28a745"
        }
    },
    "gastos": {
        "tipos_gasto": [
            {
                "id": "dieta",
                "nombre": "Dietas",
                "descripcion": "Gastos de comida durante jornada laboral",
                "limite_diario": 50.00,
                "requiere_justificante": True,
                "icon": "🍽️"
            },
            {
                "id": "aparcamiento", 
                "nombre": "Aparcamiento",
                "descripcion": "Gastos de parking y estacionamiento",
                "limite_diario": 20.00,
                "requiere_justificante": True,
                "icon": "🅿️"
            },
            {
                "id": "gasolina",
                "nombre": "Combustible",
                "descripcion": "Gastos de gasolina y combustible",
                "limite_diario": 100.00,
                "requiere_justificante": True,
                "icon": "⛽"
            },
            {
                "id": "otros",
                "nombre": "Otros gastos",
                "descripcion": "Otros gastos operativos",
                "limite_diario": 75.00,
                "requiere_justificante": True,
                "icon": "📎"
            }
        ],
        "estados": [
            {"id": "pendiente", "nombre": "Pendiente", "color": "#ffc107"},
            {"id": "aprobado", "nombre": "Aprobado", "color": "#28a745"},
            {"id": "rechazado", "nombre": "Rechazado", "color": "#dc3545"},
            {"id": "pagado", "nombre": "Pagado", "color": "#0066CC"}
        ],
        "limites_aprobacion": {
            "operario": 0,  # No puede aprobar
            "supervisor": 500.00,  # Hasta 500€
            "administrador": 9999999,  # Sin límite
            "contabilidad": 9999999  # Sin límite
        }
    },
    "idioma": {
        "predeterminado": "es",
        "idiomas_disponibles": ["es", "en", "ca"],
        "traducciones": {
            "es": {
                "gastos": "Gastos",
                "nuevo_gasto": "Nuevo Gasto",
                "mis_gastos": "Mis Gastos",
                "dashboard": "Panel de Control",
                "usuarios": "Usuarios", 
                "configuracion": "Configuración",
                "reportes": "Reportes",
                "pendientes_aprobacion": "Pendientes de Aprobación",
                "total_mensual": "Total Mensual",
                "por_aprobar": "Por Aprobar",
                "aprobados_mes": "Aprobados este mes",
                "dietas": "Dietas",
                "aparcamiento": "Aparcamiento", 
                "gasolina": "Combustible",
                "otros": "Otros gastos",
                "pendiente": "Pendiente",
                "aprobado": "Aprobado",
                "rechazado": "Rechazado",
                "pagado": "Pagado"
            },
            "en": {
                "gastos": "Expenses",
                "nuevo_gasto": "New Expense",
                "mis_gastos": "My Expenses",
                "dashboard": "Dashboard",
                "usuarios": "Users",
                "configuracion": "Settings", 
                "reportes": "Reports",
                "pendientes_aprobacion": "Pending Approval",
                "total_mensual": "Monthly Total",
                "por_aprobar": "To Approve",
                "aprobados_mes": "Approved this month",
                "dietas": "Meals",
                "aparcamiento": "Parking",
                "gasolina": "Fuel",
                "otros": "Other expenses",
                "pendiente": "Pending",
                "aprobado": "Approved", 
                "rechazado": "Rejected",
                "pagado": "Paid"
            },
            "ca": {
                "gastos": "Despeses",
                "nuevo_gasto": "Nova Despesa",
                "mis_gastos": "Les meves Despeses", 
                "dashboard": "Tauler de Control",
                "usuarios": "Usuaris",
                "configuracion": "Configuració",
                "reportes": "Informes",
                "pendientes_aprobacion": "Pendents d'Aprovació",
                "total_mensual": "Total Mensual",
                "por_aprobar": "Per Aprovar",
                "aprobados_mes": "Aprovats aquest mes",
                "dietas": "Dietes",
                "aparcamiento": "Aparcament",
                "gasolina": "Combustible", 
                "otros": "Altres despeses",
                "pendiente": "Pendent",
                "aprobado": "Aprovat",
                "rechazado": "Rebutjat",
                "pagado": "Pagat"
            }
        }
    },
    "apariencia": {
        "modo_oscuro": False,
        "tema": "default"
    }
}

# Simulador simple de JWT
JWT_SECRET = "gruplomi-gastos-jwt-2025"

def create_simple_token(user_data: Dict) -> str:
    import base64
    payload = {
        'user_id': user_data['id'],
        'email': user_data['email'],
        'role': user_data['role'],
        'departamento': user_data.get('departamento', ''),
        'exp': str(datetime.datetime.utcnow() + datetime.timedelta(hours=24))
    }
    token_data = json.dumps(payload)
    return base64.b64encode(token_data.encode()).decode()

def verify_simple_token(token: str) -> Optional[Dict]:
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
        
    def _send_json_response(self, data: Any, status_code: int = 200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
        
    def _get_request_data(self) -> Dict:
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
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            if path == '/' or path == '/api':
                response = {
                    "status": "working",
                    "message": "🏢 GrupLomi - Sistema de Gestión de Gastos - v1.0",
                    "sistema": "gastos_empresariales",
                    "roles": ["administrador", "supervisor", "operario", "contabilidad"],
                    "tipos_gasto": ["dietas", "aparcamiento", "gasolina", "otros"],
                    "endpoints": {
                        "auth": ["/auth/login", "/auth/me"],
                        "gastos": ["/gastos", "/gastos/{id}", "/gastos/mis-gastos"],
                        "usuarios": ["/usuarios", "/usuarios/{id}"],
                        "config": ["/config", "/config/admin"],
                        "reportes": ["/reportes/dashboard", "/reportes/gastos"]
                    }
                }
                self._send_json_response(response)
                
            elif path == '/health':
                self._send_json_response({"status": "ok", "version": "1.0", "sistema": "gastos"})
                
            elif path == '/config':
                # Configuración pública
                user = self._verify_token()
                idioma = query_params.get('lang', ['es'])[0]
                
                if user:
                    user_data = next((u for u in USERS_DB.values() if u['id'] == user['user_id']), None)
                    if user_data and 'idioma_preferido' in user_data:
                        idioma = user_data['idioma_preferido']
                
                public_config = {
                    "empresa": SYSTEM_CONFIG["empresa"],
                    "gastos": SYSTEM_CONFIG["gastos"],
                    "idioma": {
                        "actual": idioma,
                        "disponibles": SYSTEM_CONFIG["idioma"]["idiomas_disponibles"],
                        "traducciones": SYSTEM_CONFIG["idioma"]["traducciones"].get(idioma, SYSTEM_CONFIG["idioma"]["traducciones"]["es"])
                    },
                    "apariencia": SYSTEM_CONFIG["apariencia"]
                }
                self._send_json_response(public_config)
                
            elif path == '/config/admin':
                # Configuración completa para administradores
                user = self._verify_token()
                if not user or user['role'] != 'administrador':
                    self._send_json_response({"error": "Sin permisos para acceder a configuración de admin"}, 403)
                    return
                
                # Devolver configuración completa incluyendo estructura para frontend
                admin_config = {
                    "empresa": SYSTEM_CONFIG["empresa"],
                    "gastos": SYSTEM_CONFIG["gastos"],
                    "idioma": SYSTEM_CONFIG["idioma"],
                    "apariencia": SYSTEM_CONFIG["apariencia"],
                    "tickets": {
                        "estados": ["nuevo", "en_progreso", "resuelto", "cerrado"],
                        "prioridades": ["baja", "media", "alta", "crítica"],
                        "categorias": ["soporte", "desarrollo", "infraestructura", "otros"]
                    },
                    "notificaciones": {
                        "email_habilitado": True,
                        "notificar_asignacion": True,
                        "notificar_cambio_estado": True
                    }
                }
                self._send_json_response(admin_config)
                
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
                    
            elif path == '/gastos':
                user = self._verify_token()
                if not user:
                    self._send_json_response({"error": "Token requerido"}, 401)
                    return
                    
                gastos_list = list(GASTOS_DB.values())
                
                # Filtrar gastos según el rol
                if user['role'] == 'operario':
                    # Los operarios solo ven sus propios gastos
                    gastos_list = [g for g in gastos_list if g['creado_por'] == user['user_id']]
                elif user['role'] == 'supervisor':
                    # Los supervisores ven gastos de su departamento o asignados a ellos
                    gastos_list = [g for g in gastos_list if g.get('supervisor_asignado') == user['user_id']]
                # Administradores y contabilidad ven todos
                
                self._send_json_response(gastos_list)
                
            elif path == '/gastos/mis-gastos':
                user = self._verify_token()
                if not user:
                    self._send_json_response({"error": "Token requerido"}, 401)
                    return
                    
                mis_gastos = [g for g in GASTOS_DB.values() if g['creado_por'] == user['user_id']]
                self._send_json_response(mis_gastos)
                
            elif path == '/gastos/pendientes':
                user = self._verify_token()
                if not user or user['role'] not in ['supervisor', 'administrador', 'contabilidad']:
                    self._send_json_response({"error": "Sin permisos"}, 403)
                    return
                    
                pendientes = [g for g in GASTOS_DB.values() if g['estado'] == 'pendiente']
                if user['role'] == 'supervisor':
                    # Solo pendientes asignados al supervisor
                    pendientes = [g for g in pendientes if g.get('supervisor_asignado') == user['user_id']]
                    
                self._send_json_response(pendientes)
                
            elif path == '/usuarios':
                user = self._verify_token()
                if not user or user['role'] != 'administrador':
                    self._send_json_response({"error": "Sin permisos para ver usuarios"}, 403)
                    return
                
                # Devolver todos los usuarios sin el hash de contraseña
                usuarios_list = []
                for usuario in USERS_DB.values():
                    user_safe = {k: v for k, v in usuario.items() if k != 'password_hash'}
                    usuarios_list.append(user_safe)
                
                # Añadir información del supervisor
                for usuario in usuarios_list:
                    if usuario.get('supervisor_id'):
                        supervisor = next((u for u in USERS_DB.values() if u['id'] == usuario['supervisor_id']), None)
                        if supervisor:
                            usuario['supervisor_nombre'] = f"{supervisor['nombre']} {supervisor['apellidos']}"
                    else:
                        usuario['supervisor_nombre'] = None
                
                self._send_json_response(usuarios_list)
                
            elif path.startswith('/usuarios/'):
                user = self._verify_token()
                if not user:
                    self._send_json_response({"error": "Token requerido"}, 401)
                    return
                
                user_id = int(path.split('/')[-1])
                target_user = next((u for u in USERS_DB.values() if u['id'] == user_id), None)
                
                if not target_user:
                    self._send_json_response({"error": "Usuario no encontrado"}, 404)
                    return
                
                # Solo admin puede ver cualquier usuario, otros solo su propio perfil
                if user['role'] != 'administrador' and user['user_id'] != user_id:
                    self._send_json_response({"error": "Sin permisos"}, 403)
                    return
                
                user_safe = {k: v for k, v in target_user.items() if k != 'password_hash'}
                
                # Añadir información del supervisor
                if user_safe.get('supervisor_id'):
                    supervisor = next((u for u in USERS_DB.values() if u['id'] == user_safe['supervisor_id']), None)
                    if supervisor:
                        user_safe['supervisor_nombre'] = f"{supervisor['nombre']} {supervisor['apellidos']}"
                else:
                    user_safe['supervisor_nombre'] = None
                
                self._send_json_response(user_safe)
                
            elif path == '/reportes/dashboard':
                user = self._verify_token()
                if not user:
                    self._send_json_response({"error": "Token requerido"}, 401)
                    return
                    
                # Calcular estadísticas según el rol
                total_gastos = len(GASTOS_DB)
                total_importe = sum(g['importe'] for g in GASTOS_DB.values())
                pendientes = len([g for g in GASTOS_DB.values() if g['estado'] == 'pendiente'])
                aprobados = len([g for g in GASTOS_DB.values() if g['estado'] == 'aprobado'])
                
                if user['role'] == 'operario':
                    mis_gastos = [g for g in GASTOS_DB.values() if g['creado_por'] == user['user_id']]
                    total_gastos = len(mis_gastos)
                    total_importe = sum(g['importe'] for g in mis_gastos)
                    pendientes = len([g for g in mis_gastos if g['estado'] == 'pendiente'])
                    aprobados = len([g for g in mis_gastos if g['estado'] == 'aprobado'])
                
                dashboard_data = {
                    "total_gastos": total_gastos,
                    "total_importe": total_importe,
                    "pendientes": pendientes,
                    "aprobados": aprobados,
                    "por_tipo": {
                        "dietas": len([g for g in GASTOS_DB.values() if g['tipo_gasto'] == 'dieta']),
                        "aparcamiento": len([g for g in GASTOS_DB.values() if g['tipo_gasto'] == 'aparcamiento']),
                        "gasolina": len([g for g in GASTOS_DB.values() if g['tipo_gasto'] == 'gasolina']),
                        "otros": len([g for g in GASTOS_DB.values() if g['tipo_gasto'] == 'otros'])
                    }
                }
                self._send_json_response(dashboard_data)
                
            elif path == '/usuarios':
                user = self._verify_token()
                if not user or user['role'] != 'administrador':
                    self._send_json_response({"error": "Sin permisos para crear usuarios"}, 403)
                    return
                
                # Validar email único
                email = data.get('email')
                if email in USERS_DB:
                    self._send_json_response({"error": "El email ya existe"}, 400)
                    return
                
                # Generar nuevo ID
                new_id = max(u['id'] for u in USERS_DB.values()) + 1
                
                # Hashear contraseña
                password = data.get('password', 'temp123')
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                nuevo_usuario = {
                    "id": new_id,
                    "email": email,
                    "password_hash": password_hash,
                    "nombre": data.get('nombre', ''),
                    "apellidos": data.get('apellidos', ''),
                    "codigo_empleado": data.get('codigo_empleado', ''),
                    "telefono": data.get('telefono', ''),
                    "direccion": data.get('direccion', ''),
                    "fecha_nacimiento": data.get('fecha_nacimiento', ''),
                    "fecha_contratacion": data.get('fecha_contratacion', ''),
                    "foto_url": data.get('foto_url', '/avatars/default.jpg'),
                    "role": data.get('role', 'operario'),
                    "departamento": data.get('departamento', ''),
                    "supervisor_id": data.get('supervisor_id'),
                    "activo": data.get('activo', True),
                    "idioma_preferido": data.get('idioma_preferido', 'es'),
                    "permisos_especiales": data.get('permisos_especiales', [])
                }
                
                USERS_DB[email] = nuevo_usuario
                
                # Devolver usuario sin contraseña
                user_safe = {k: v for k, v in nuevo_usuario.items() if k != 'password_hash'}
                self._send_json_response(user_safe, 201)
                
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
                
            elif path == '/gastos':
                user = self._verify_token()
                if not user:
                    self._send_json_response({"error": "Token requerido"}, 401)
                    return
                    
                # Validar que el usuario puede crear gastos
                if user['role'] not in ['operario', 'administrador']:
                    self._send_json_response({"error": "Sin permisos para crear gastos"}, 403)
                    return
                    
                new_id = max(GASTOS_DB.keys()) + 1 if GASTOS_DB else 1
                
                # Procesar campos según el tipo de gasto
                tipo_gasto = data.get('tipo_gasto')
                descripcion = data.get('descripcion')
                obra = data.get('obra')
                archivos_adjuntos = data.get('archivos_adjuntos', [])
                
                # Validar archivos obligatorios para dieta y aparcamiento
                if tipo_gasto in ['dieta', 'aparcamiento']:
                    if not archivos_adjuntos or len(archivos_adjuntos) == 0:
                        self._send_json_response({
                            "error": f"Es obligatorio adjuntar una foto del ticket para {tipo_gasto}"
                        }, 400)
                        return
                
                # Calcular importe según el tipo de gasto
                if tipo_gasto == 'gasolina':
                    kilometros = float(data.get('kilometros', 0))
                    precio_km = float(data.get('precio_km', 0))
                    importe_calculado = kilometros * precio_km
                    
                    nuevo_gasto = {
                        "id": new_id,
                        "tipo_gasto": tipo_gasto,
                        "descripcion": descripcion,
                        "obra": obra,
                        "importe": round(importe_calculado, 2),
                        "fecha_gasto": data.get('fecha_gasto'),
                        "estado": "pendiente",
                        "creado_por": user['user_id'],
                        "supervisor_asignado": data.get('supervisor_asignado'),
                        "fecha_creacion": datetime.datetime.utcnow().isoformat() + 'Z',
                        "archivos_adjuntos": archivos_adjuntos,
                        "fecha_aprobacion": None,
                        "aprobado_por": None,
                        "kilometros": kilometros,
                        "precio_km": precio_km
                    }
                else:
                    # Para otros tipos de gasto (dieta, aparcamiento, otros)
                    importe = float(data.get('importe', 0))
                    
                    nuevo_gasto = {
                        "id": new_id,
                        "tipo_gasto": tipo_gasto,
                        "descripcion": descripcion,
                        "obra": obra,
                        "importe": importe,
                        "fecha_gasto": data.get('fecha_gasto'),
                        "estado": "pendiente",
                        "creado_por": user['user_id'],
                        "supervisor_asignado": data.get('supervisor_asignado'),
                        "fecha_creacion": datetime.datetime.utcnow().isoformat() + 'Z',
                        "archivos_adjuntos": archivos_adjuntos,
                        "fecha_aprobacion": None,
                        "aprobado_por": None,
                        "kilometros": None,
                        "precio_km": None
                    }
                
                # Validar límites
                tipo_config = next((t for t in SYSTEM_CONFIG['gastos']['tipos_gasto'] if t['id'] == nuevo_gasto['tipo_gasto']), None)
                if tipo_config and nuevo_gasto['importe'] > tipo_config['limite_diario']:
                    self._send_json_response({
                        "error": f"El importe supera el límite diario de {tipo_config['limite_diario']}€ para {tipo_config['nombre']}"
                    }, 400)
                    return
                
                GASTOS_DB[new_id] = nuevo_gasto
                self._send_json_response(nuevo_gasto, 201)
                
            elif path.startswith('/usuarios/'):
                # Actualizar usuario
                user_id = int(path.split('/')[-1])
                target_user_entry = next(((email, u) for email, u in USERS_DB.items() if u['id'] == user_id), None)
                
                if not target_user_entry:
                    self._send_json_response({"error": "Usuario no encontrado"}, 404)
                    return
                
                email, target_user = target_user_entry
                
                # Solo admin puede editar cualquier usuario, otros solo su perfil
                if user['role'] != 'administrador' and user['user_id'] != user_id:
                    self._send_json_response({"error": "Sin permisos"}, 403)
                    return
                
                # Actualizar campos (admin puede cambiar todo, usuario solo datos personales)
                if user['role'] == 'administrador':
                    # Admin puede cambiar cualquier campo
                    updateable_fields = [
                        'nombre', 'apellidos', 'codigo_empleado', 'telefono', 'direccion',
                        'fecha_nacimiento', 'fecha_contratacion', 'foto_url', 'role',
                        'departamento', 'supervisor_id', 'activo', 'idioma_preferido',
                        'permisos_especiales'
                    ]
                else:
                    # Usuario normal solo puede cambiar datos personales
                    updateable_fields = [
                        'nombre', 'apellidos', 'telefono', 'direccion', 'foto_url',
                        'idioma_preferido'
                    ]
                
                for field in updateable_fields:
                    if field in data:
                        target_user[field] = data[field]
                
                # Cambiar contraseña si se proporciona
                if 'password' in data and data['password']:
                    target_user['password_hash'] = hashlib.sha256(data['password'].encode()).hexdigest()
                
                # Cambiar email (solo admin)
                if 'email' in data and user['role'] == 'administrador':
                    new_email = data['email']
                    if new_email != email and new_email in USERS_DB:
                        self._send_json_response({"error": "El email ya existe"}, 400)
                        return
                    
                    if new_email != email:
                        # Cambiar clave en el diccionario
                        USERS_DB[new_email] = target_user
                        target_user['email'] = new_email
                        del USERS_DB[email]
                
                # Devolver usuario actualizado sin contraseña
                user_safe = {k: v for k, v in target_user.items() if k != 'password_hash'}
                self._send_json_response(user_safe)
                
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
                
            if path.startswith('/gastos/') and '/aprobar' in path:
                # Aprobar gasto
                gasto_id = int(path.split('/')[-2])
                if gasto_id not in GASTOS_DB:
                    self._send_json_response({"error": "Gasto no encontrado"}, 404)
                    return
                    
                gasto = GASTOS_DB[gasto_id]
                
                # Verificar permisos de aprobación
                if user['role'] not in ['supervisor', 'administrador', 'contabilidad']:
                    self._send_json_response({"error": "Sin permisos para aprobar gastos"}, 403)
                    return
                    
                # Verificar límites de aprobación
                limite = SYSTEM_CONFIG['gastos']['limites_aprobacion'].get(user['role'], 0)
                if gasto['importe'] > limite:
                    self._send_json_response({"error": f"El importe supera tu límite de aprobación ({limite}€)"}, 403)
                    return
                    
                accion = data.get('accion')  # 'aprobar' o 'rechazar'
                observaciones = data.get('observaciones', '')
                
                if accion == 'aprobar':
                    gasto['estado'] = 'aprobado'
                elif accion == 'rechazar':
                    gasto['estado'] = 'rechazado'
                else:
                    self._send_json_response({"error": "Acción no válida"}, 400)
                    return
                
                gasto['fecha_aprobacion'] = datetime.datetime.utcnow().isoformat() + 'Z'
                gasto['aprobado_por'] = user['user_id']
                gasto['observaciones'] = observaciones
                
                self._send_json_response(gasto)
                
            elif path.startswith('/gastos/'):
                # Actualizar gasto
                gasto_id = int(path.split('/')[-1])
                if gasto_id not in GASTOS_DB:
                    self._send_json_response({"error": "Gasto no encontrado"}, 404)
                    return
                    
                gasto = GASTOS_DB[gasto_id]
                
                # Solo el creador o admin puede editar
                if user['role'] != 'administrador' and gasto['creado_por'] != user['user_id']:
                    self._send_json_response({"error": "Sin permisos para editar este gasto"}, 403)
                    return
                    
                # No se puede editar si ya está aprobado o pagado
                if gasto['estado'] in ['aprobado', 'pagado']:
                    self._send_json_response({"error": "No se puede editar un gasto aprobado o pagado"}, 400)
                    return
                    
                # Actualizar campos
                for key, value in data.items():
                    if key in ['descripcion', 'obra', 'importe', 'fecha_gasto', 'tipo_gasto', 'archivos_adjuntos', 'kilometros', 'precio_km']:
                        gasto[key] = value
                
                # Recalcular importe si es combustible y se proporcionan km/precio
                if gasto['tipo_gasto'] == 'gasolina' and 'kilometros' in data and 'precio_km' in data:
                    gasto['importe'] = round(float(data['kilometros']) * float(data['precio_km']), 2)
                        
                self._send_json_response(gasto)
                
            elif path == '/config/admin':
                # Actualizar configuración del sistema
                if user['role'] != 'administrador':
                    self._send_json_response({"error": "Sin permisos para modificar configuración"}, 403)
                    return
                
                # Actualizar SYSTEM_CONFIG con los nuevos datos
                if 'empresa' in data:
                    SYSTEM_CONFIG['empresa'].update(data['empresa'])
                if 'gastos' in data:
                    SYSTEM_CONFIG['gastos'].update(data['gastos'])
                if 'idioma' in data:
                    SYSTEM_CONFIG['idioma'].update(data['idioma'])
                if 'apariencia' in data:
                    SYSTEM_CONFIG['apariencia'].update(data['apariencia'])
                
                # Devolver configuración actualizada
                updated_config = {
                    "success": True,
                    "message": "Configuración actualizada correctamente",
                    "config": {
                        "empresa": SYSTEM_CONFIG["empresa"],
                        "gastos": SYSTEM_CONFIG["gastos"],
                        "idioma": SYSTEM_CONFIG["idioma"],
                        "apariencia": SYSTEM_CONFIG["apariencia"]
                    }
                }
                self._send_json_response(updated_config)
                
            elif path.startswith('/usuarios/'):
                user_id = int(path.split('/')[-1])
                target_user_entry = next(((email, u) for email, u in USERS_DB.items() if u['id'] == user_id), None)
                
                if not target_user_entry:
                    self._send_json_response({"error": "Usuario no encontrado"}, 404)
                    return
                
                email, target_user = target_user_entry
                
                # Solo admin puede eliminar usuarios
                if user['role'] != 'administrador':
                    self._send_json_response({"error": "Sin permisos para eliminar usuarios"}, 403)
                    return
                
                # No se puede eliminar a sí mismo
                if user['user_id'] == user_id:
                    self._send_json_response({"error": "No puedes eliminarte a ti mismo"}, 400)
                    return
                
                # Verificar que no tenga gastos pendientes
                gastos_pendientes = [g for g in GASTOS_DB.values() if g['creado_por'] == user_id and g['estado'] == 'pendiente']
                if gastos_pendientes:
                    self._send_json_response({"error": f"El usuario tiene {len(gastos_pendientes)} gastos pendientes"}, 400)
                    return
                
                del USERS_DB[email]
                self._send_json_response({"message": "Usuario eliminado correctamente"})
                
            else:
                self._send_json_response({"error": "Endpoint no encontrado"}, 404)
                
        except Exception as e:
            self._send_json_response({"error": "Error interno", "details": str(e)}, 500)

    def do_DELETE(self):
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            
            user = self._verify_token()
            if not user:
                self._send_json_response({"error": "Token requerido"}, 401)
                return
                
            if path.startswith('/gastos/'):
                gasto_id = int(path.split('/')[-1])
                if gasto_id not in GASTOS_DB:
                    self._send_json_response({"error": "Gasto no encontrado"}, 404)
                    return
                
                gasto = GASTOS_DB[gasto_id]
                
                # Solo admin o el creador pueden eliminar
                if user['role'] != 'administrador' and gasto['creado_por'] != user['user_id']:
                    self._send_json_response({"error": "Sin permisos para eliminar este gasto"}, 403)
                    return
                    
                # No se puede eliminar si está aprobado o pagado
                if gasto['estado'] in ['aprobado', 'pagado']:
                    self._send_json_response({"error": "No se puede eliminar un gasto aprobado o pagado"}, 400)
                    return
                    
                del GASTOS_DB[gasto_id]
                self._send_json_response({"message": "Gasto eliminado"})
                
            else:
                self._send_json_response({"error": "Endpoint no encontrado"}, 404)
                
        except Exception as e:
            self._send_json_response({"error": "Error interno", "details": str(e)}, 500)

handler = GastosAPI