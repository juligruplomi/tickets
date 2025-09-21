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
            "operario": 0,
            "supervisor": 500.00,
            "administrador": 9999999,
            "contabilidad": 9999999
        }
    },
    "idioma": {
        "predeterminado": "es",
        "idiomas_disponibles": ["es", "en", "ca", "de", "it", "pt"],
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
            },
            "de": {
                "gastos": "Ausgaben",
                "nuevo_gasto": "Neue Ausgabe",
                "mis_gastos": "Meine Ausgaben",
                "dashboard": "Dashboard",
                "usuarios": "Benutzer",
                "configuracion": "Einstellungen",
                "reportes": "Berichte",
                "pendientes_aprobacion": "Genehmigung ausstehend",
                "total_mensual": "Monatssumme",
                "por_aprobar": "Zu genehmigen",
                "aprobados_mes": "Genehmigt diesen Monat",
                "dietas": "Mahlzeiten",
                "aparcamiento": "Parken",
                "gasolina": "Kraftstoff",
                "otros": "Andere Ausgaben",
                "pendiente": "Ausstehend",
                "aprobado": "Genehmigt",
                "rechazado": "Abgelehnt",
                "pagado": "Bezahlt"
            },
            "it": {
                "gastos": "Spese",
                "nuevo_gasto": "Nuova Spesa",
                "mis_gastos": "Le mie Spese",
                "dashboard": "Dashboard",
                "usuarios": "Utenti",
                "configuracion": "Impostazioni",
                "reportes": "Report",
                "pendientes_aprobacion": "In attesa di approvazione",
                "total_mensual": "Totale mensile",
                "por_aprobar": "Da approvare",
                "aprobados_mes": "Approvati questo mese",
                "dietas": "Pasti",
                "aparcamiento": "Parcheggio",
                "gasolina": "Carburante",
                "otros": "Altre spese",
                "pendiente": "In attesa",
                "aprobado": "Approvato",
                "rechazado": "Rifiutato",
                "pagado": "Pagato"
            },
            "pt": {
                "gastos": "Despesas",
                "nuevo_gasto": "Nova Despesa",
                "mis_gastos": "Minhas Despesas",
                "dashboard": "Painel",
                "usuarios": "Usuários",
                "configuracion": "Configurações",
                "reportes": "Relatórios",
                "pendientes_aprobacion": "Aguardando aprovação",
                "total_mensual": "Total mensal",
                "por_aprobar": "Para aprovar",
                "aprobados_mes": "Aprovados este mês",
                "dietas": "Refeições",
                "aparcamiento": "Estacionamento",
                "gasolina": "Combustível",
                "otros": "Outras despesas",
                "pendiente": "Pendente",
                "aprobado": "Aprovado",
                "rechazado": "Rejeitado",
                "pagado": "Pago"
            }
        }
    },
    "tickets": {
        "estados": [
            {"id": "abierto", "nombre": "Abierto", "color": "#17a2b8"},
            {"id": "en_progreso", "nombre": "En Progreso", "color": "#ffc107"},
            {"id": "pendiente_aprobacion", "nombre": "Pendiente Aprobación", "color": "#fd7e14"},
            {"id": "resuelto", "nombre": "Resuelto", "color": "#28a745"},
            {"id": "cerrado", "nombre": "Cerrado", "color": "#6c757d"},
            {"id": "rechazado", "nombre": "Rechazado", "color": "#dc3545"}
        ],
        "prioridades": [
            {"id": "baja", "nombre": "Baja", "color": "#6c757d", "orden": 1},
            {"id": "normal", "nombre": "Normal", "color": "#17a2b8", "orden": 2},
            {"id": "alta", "nombre": "Alta", "color": "#ffc107", "orden": 3},
            {"id": "urgente", "nombre": "Urgente", "color": "#fd7e14", "orden": 4},
            {"id": "critica", "nombre": "Crítica", "color": "#dc3545", "orden": 5}
        ],
        "categorias": [
            {"id": "soporte_tecnico", "nombre": "Soporte Técnico", "descripcion": "Problemas técnicos y de software"},
            {"id": "recursos_humanos", "nombre": "Recursos Humanos", "descripcion": "Consultas de personal y nóminas"},
            {"id": "administracion", "nombre": "Administración", "descripcion": "Gestiones administrativas"},
            {"id": "mantenimiento", "nombre": "Mantenimiento", "descripcion": "Mantenimiento de equipos e instalaciones"},
            {"id": "compras", "nombre": "Compras", "descripcion": "Solicitudes de compra y proveedores"},
            {"id": "general", "nombre": "General", "descripcion": "Consultas generales"}
        ],
        "configuracion": {
            "auto_asignar_supervisor": True,
            "tiempo_limite_resolucion": 72,
            "permitir_reabrir": True,
            "requiere_aprobacion_cierre": False,
            "adjuntos_permitidos": [".jpg", ".jpeg", ".png", ".pdf", ".doc", ".docx", ".xls", ".xlsx"],
            "tamano_maximo_adjunto": 10
        }
    },
    "notificaciones": {
        "email_habilitado": True,
        "plantilla_asunto": "[{{empresa}}] {{tipo}}: {{titulo}}",
        "configuracion_email": {
            "servidor_smtp": "smtp.gmail.com",
            "puerto": 587,
            "ssl_habilitado": True,
            "usuario": "admin@gruplomi.com",
            "password": "******"
        },
        "eventos": {
            "gasto_creado": {
                "habilitado": True,
                "destinatarios": ["supervisor", "contabilidad"],
                "plantilla": "Se ha creado un nuevo gasto por {{usuario}} por valor de {{importe}}€"
            },
            "gasto_aprobado": {
                "habilitado": True,
                "destinatarios": ["creador", "contabilidad"],
                "plantilla": "Tu gasto #{{id}} ha sido aprobado por {{aprobador}}"
            },
            "gasto_rechazado": {
                "habilitado": True,
                "destinatarios": ["creador"],
                "plantilla": "Tu gasto #{{id}} ha sido rechazado. Motivo: {{motivo}}"
            },
            "ticket_creado": {
                "habilitado": True,
                "destinatarios": ["asignado", "supervisor"],
                "plantilla": "Nuevo ticket #{{id}}: {{titulo}}"
            },
            "ticket_asignado": {
                "habilitado": True,
                "destinatarios": ["asignado"],
                "plantilla": "Se te ha asignado el ticket #{{id}}: {{titulo}}"
            },
            "ticket_resuelto": {
                "habilitado": True,
                "destinatarios": ["creador", "supervisor"],
                "plantilla": "El ticket #{{id}} ha sido resuelto"
            }
        },
        "recordatorios": {
            "gastos_pendientes": {
                "habilitado": True,
                "frecuencia": "diaria",
                "hora": "09:00",
                "destinatarios": ["supervisor", "contabilidad"]
            },
            "tickets_sin_asignar": {
                "habilitado": True,
                "frecuencia": "cada_hora",
                "destinatarios": ["administrador"]
            },
            "tickets_vencidos": {
                "habilitado": True,
                "frecuencia": "diaria",
                "hora": "10:00",
                "destinatarios": ["supervisor", "administrador"]
            }
        }
    },
    "apariencia": {
        "modo_oscuro": False,
        "tema": "default"
    }
}

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
                        "config": ["/config", "/config/admin", "/config/language"],
                        "reportes": ["/reportes/dashboard", "/reportes/gastos"]
                    }
                }
                self._send_json_response(response)
                
            elif path == '/health':
                self._send_json_response({"status": "ok", "version": "1.0", "sistema": "gastos"})
                
            elif path == '/config':
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
                user = self._verify_token()
                if not user or user['role'] != 'administrador':
                    self._send_json_response({"error": "Sin permisos para acceder a configuración de admin"}, 403)
                    return
                
                admin_config = {
                    "empresa": SYSTEM_CONFIG["empresa"],
                    "gastos": SYSTEM_CONFIG["gastos"],
                    "idioma": SYSTEM_CONFIG["idioma"],
                    "tickets": SYSTEM_CONFIG["tickets"],
                    "notificaciones": SYSTEM_CONFIG["notificaciones"],
                    "apariencia": SYSTEM_CONFIG["apariencia"]
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
                
                if user['role'] == 'operario':
                    gastos_list = [g for g in gastos_list if g['creado_por'] == user['user_id']]
                elif user['role'] == 'supervisor':
                    gastos_list = [g for g in gastos_list if g.get('supervisor_asignado') == user['user_id']]
                
                self._send_json_response(gastos_list)
                
            elif path == '/gastos/mis-gastos':
                user = self._verify_token()
                if not user:
                    self._send_json_response({"error": "Token requerido"}, 401)
                    return
                    
                mis_gastos = [g for g in GASTOS_DB.values() if g['creado_por'] == user['user_id']]
                self._send_json_response(mis_gastos)
                
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
                    
                user_data = next((u for u in USERS_DB.values() if u['id'] == user['user_id']), None)
                if user_data:
                    user_data['idioma_preferido'] = nuevo_idioma
                    
                updated_config = {
                    "empresa": SYSTEM_CONFIG["empresa"],
                    "gastos": SYSTEM_CONFIG["gastos"],
                    "idioma": {
                        "actual": nuevo_idioma,
                        "disponibles": SYSTEM_CONFIG["idioma"]["idiomas_disponibles"],
                        "traducciones": SYSTEM_CONFIG["idioma"]["traducciones"].get(nuevo_idioma, SYSTEM_CONFIG["idioma"]["traducciones"]["es"])
                    },
                    "apariencia": SYSTEM_CONFIG["apariencia"]
                }
                self._send_json_response(updated_config)
                
            elif path == '/config/admin':
                # Actualizar configuración del sistema (modo demo)
                if user['role'] != 'administrador':
                    self._send_json_response({"error": "Sin permisos para modificar configuración"}, 403)
                    return
                
                # Actualizar SYSTEM_CONFIG con los nuevos datos (en memoria)
                if 'empresa' in data:
                    SYSTEM_CONFIG['empresa'].update(data['empresa'])
                if 'gastos' in data:
                    SYSTEM_CONFIG['gastos'].update(data['gastos'])
                if 'idioma' in data:
                    SYSTEM_CONFIG['idioma'].update(data['idioma'])
                if 'tickets' in data:
                    SYSTEM_CONFIG['tickets'].update(data['tickets'])
                if 'notificaciones' in data:
                    SYSTEM_CONFIG['notificaciones'].update(data['notificaciones'])
                if 'apariencia' in data:
                    SYSTEM_CONFIG['apariencia'].update(data['apariencia'])
                
                # Devolver configuración actualizada
                updated_config = {
                    "success": True,
                    "message": "Configuración actualizada correctamente (MODO DEMO - cambios temporales)",
                    "config": {
                        "empresa": SYSTEM_CONFIG["empresa"],
                        "gastos": SYSTEM_CONFIG["gastos"],
                        "idioma": SYSTEM_CONFIG["idioma"],
                        "tickets": SYSTEM_CONFIG["tickets"],
                        "notificaciones": SYSTEM_CONFIG["notificaciones"],
                        "apariencia": SYSTEM_CONFIG["apariencia"]
                    }
                }
                self._send_json_response(updated_config)
                
            else:
                self._send_json_response({"error": "Endpoint no encontrado"}, 404)
                
        except Exception as e:
            self._send_json_response({"error": "Error interno", "details": str(e)}, 500)

handler = GastosAPI