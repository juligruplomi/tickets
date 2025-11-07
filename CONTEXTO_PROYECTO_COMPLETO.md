# 🚀 CONTEXTO COMPLETO DEL PROYECTO GRUPLOMI

## 📋 INFORMACIÓN ESENCIAL DEL PROYECTO

**Proyecto**: Sistema de Gestión de Gastos Empresariales GrupLomi
**Estado**: EN PRODUCCIÓN ✅
**Última actualización**: 06/11/2025

## 🏗️ ARQUITECTURA DEL SISTEMA

### Stack Tecnológico

**Frontend**:
- React 18 + React Router v6 + Axios
- Create React App (NO Next.js)
- CSS personalizado + diseño responsive
- Autenticación con JWT (localStorage)

**Backend**:
- Python 3.9+ con BaseHTTPRequestHandler
- ⚠️ **IMPORTANTE**: NO usar FastAPI en producción (causa errores en Vercel)
- JWT para autenticación
- CORS configurado para múltiples orígenes

**Base de Datos**:
- PostgreSQL 15 (servidor externo: 185.194.59.40)
- ⚠️ **CRÍTICO**: Conexión vía PROXY HTTP en puerto 3001 (NO conexión directa)
- Schema completo con 10+ tablas

## 📁 ESTRUCTURA DE DIRECTORIOS

```
C:\
├── Tickets\                    # Backend
│   ├── index.py               # Archivo principal (clase GrupLomiAPI)
│   ├── vercel.json            # Configuración de Vercel
│   ├── requirements.txt       # Dependencias Python
│   └── CONTEXTO_PROYECTO_COMPLETO.md
│
└── tickets-frontend\           # Frontend
    ├── src\
    │   ├── services\
    │   │   └── api.js         # Configuración API
    │   ├── pages\             # Páginas React
    │   └── components\        # Componentes React
    └── CONTEXTO_PROYECTO_COMPLETO.md
```

## 🌐 URLs DE PRODUCCIÓN

- **Frontend**: https://tickets.gruplomi.com ✅
- **Backend**: https://tickets-alpha-pink.vercel.app ✅
- **Proxy PostgreSQL**: http://185.194.59.40:3001 ✅

## 🔑 CONFIGURACIÓN CRÍTICA

### Base de Datos (vía Proxy)
```python
PROXY_URL = "http://185.194.59.40:3001"
PROXY_API_KEY = "GrupLomi2024ProxySecureKey_XyZ789"
```

### Variables de Entorno en Vercel
- `PROXY_URL`: http://185.194.59.40:3001
- `PROXY_API_KEY`: GrupLomi2024ProxySecureKey_XyZ789
- `JWT_SECRET_KEY`: GrupLomi_JWT_Secret_Key_2024_Very_Secure_Hash
- `JWT_ALGORITHM`: HS256
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: 1440

### Credenciales Admin
- Email: admin@gruplomi.com
- Password: AdminGrupLomi2025

## ⚠️ REGLAS CRÍTICAS - NUNCA OLVIDAR

### 1. **SIEMPRE usar conversation_search**
Antes de hacer CUALQUIER cambio, buscar conversaciones anteriores sobre el tema.

### 2. **NUNCA eliminar endpoints existentes**
Los endpoints funcionando son sagrados. Solo agregar, nunca eliminar.

### 3. **Proxy es OBLIGATORIO**
- El backend NO puede conectarse directamente a PostgreSQL
- SIEMPRE usar el proxy HTTP en puerto 3001
- Incluir header `x-api-key` en todas las peticiones al proxy

### 4. **Estructura del Backend**
- Archivo principal: `index.py` en la raíz
- Usar clase `GrupLomiAPI(BaseHTTPRequestHandler)`
- Al final del archivo: `handler = GrupLomiAPI`
- NO usar FastAPI (causa errores en Vercel)

### 5. **Verificación antes de deploy**
1. Probar localmente primero
2. Hacer backup del código actual
3. Commit con mensaje descriptivo
4. Push a GitHub
5. Verificar despliegue en Vercel

## 🔄 FLUJO DE TRABAJO

### Para hacer cambios:

1. **Buscar contexto**:
```python
conversation_search("tema del cambio")
```

2. **Backup actual**:
```powershell
copy C:\Tickets\index.py C:\Tickets\index_backup_$(Get-Date -Format "yyyyMMdd_HHmm").py
```

3. **Hacer cambios**:
- Editar archivos necesarios
- Mantener todos los endpoints existentes

4. **Probar localmente**:
```powershell
# Backend
cd C:\Tickets
python index.py

# Frontend
cd C:\tickets-frontend
npm start
```

5. **Deploy**:
```powershell
# Backend
cd C:\Tickets
git add .
git commit -m "Descripción del cambio"
git push origin main

# Frontend
cd C:\tickets-frontend
git add .
git commit -m "Descripción del cambio"
git push origin main
```

## 📊 ENDPOINTS PRINCIPALES

### Autenticación
- `POST /auth/login` - Login de usuarios
- `GET /auth/me` - Usuario actual

### Gastos
- `GET /gastos` - Listar gastos
- `POST /gastos` - Crear gasto (con foto)
- `PUT /gastos/{id}` - Actualizar gasto
- `DELETE /gastos/{id}` - Eliminar gasto

### Usuarios
- `GET /usuarios` - Listar usuarios (admin)
- `POST /usuarios` - Crear usuario
- `PUT /usuarios/{id}` - Actualizar usuario
- `DELETE /usuarios/{id}` - Eliminar usuario

### Configuración
- `GET /config/sistema` - Configuración del sistema
- `PUT /config/sistema` - Actualizar configuración
- `GET /roles` - Listar roles y permisos
- `PUT /roles/{id}` - Actualizar permisos de rol

### Reportes
- `GET /reportes/dashboard` - KPIs del dashboard
- `GET /reportes/gastos` - Reporte de gastos

## 🐛 PROBLEMAS COMUNES Y SOLUCIONES

### 1. Error de conexión a BD
**Problema**: "Error de conexión a la base de datos"
**Solución**: Verificar que el proxy esté funcionando en puerto 3001

### 2. Error 500 en Vercel
**Problema**: "FUNCTION_INVOCATION_FAILED"
**Solución**: NO usar `handler = app` con FastAPI. Usar BaseHTTPRequestHandler

### 3. Fotos no se suben
**Problema**: Payload too large
**Solución**: Comprimir imágenes antes de enviar (max 4.5MB)

### 4. Login no funciona
**Problema**: Token inválido o expirado
**Solución**: Verificar JWT_SECRET_KEY en variables de entorno

## 📝 COMANDOS ÚTILES

### Verificar estado del sistema:
```powershell
# Backend
curl https://tickets-alpha-pink.vercel.app/health

# Frontend
curl https://tickets.gruplomi.com

# Proxy
curl http://185.194.59.40:3001/health
```

### Logs de Vercel:
```powershell
vercel logs tickets-alpha-pink.vercel.app --follow
```

### Test de login:
```powershell
Invoke-WebRequest -Method POST -Uri "https://tickets-alpha-pink.vercel.app/auth/login" -Body '{"email":"admin@gruplomi.com","password":"AdminGrupLomi2025"}' -ContentType "application/json"
```

## 🚀 FUNCIONALIDADES IMPLEMENTADAS

✅ Sistema completo de autenticación con JWT
✅ Gestión de usuarios con roles (admin, supervisor, empleado, contabilidad)
✅ Gestión de gastos con fotos
✅ Sistema de aprobación de gastos
✅ Dashboard con KPIs
✅ Configuración del sistema
✅ Sistema de permisos granular
✅ Soporte multi-idioma (ES, EN, CA, DE, IT, PT)
✅ Compresión automática de fotos
✅ Exportación de reportes

## 📅 HISTORIAL DE CAMBIOS IMPORTANTES

- **30/10/2025**: Migración completa a BaseHTTPRequestHandler
- **26/10/2025**: Implementación de compresión de fotos
- **18/10/2025**: Solución de errores de Vercel con FastAPI
- **17/10/2025**: Configuración del proxy PostgreSQL
- **08/10/2025**: Implementación de sistema de permisos
- **06/10/2025**: Despliegue inicial en Vercel

## ⚡ RECORDATORIOS FINALES

1. **NUNCA** modificar sin buscar contexto primero
2. **SIEMPRE** mantener endpoints existentes
3. **VERIFICAR** el proxy antes de intentar conexión a BD
4. **PROBAR** localmente antes de deploy
5. **DOCUMENTAR** cambios en este archivo

---

**Última verificación del sistema**: 06/11/2025 - TODO FUNCIONANDO ✅
