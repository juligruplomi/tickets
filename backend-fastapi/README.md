# 🚀 Backend FastAPI - Sistema de Gastos GrupLomi

## 📁 Estructura del Proyecto

```
backend-fastapi/
├── api/
│   └── index.py          # ✅ API para Vercel (SIN startup events)
├── main.py               # ✅ API para desarrollo local (CON startup events)
├── init_db.py            # ✅ Script de inicialización de DB
├── requirements.txt      # ✅ Dependencias Python
├── vercel.json          # ✅ Configuración de Vercel
├── .env                 # ⚙️ Variables de entorno (NO subir a Git)
└── README.md            # 📖 Este archivo
```

## 🔑 Diferencias entre Archivos

### **`main.py`** (Desarrollo Local)
- ✅ Incluye `@app.on_event("startup")` para inicializar DB automáticamente
- ✅ Perfecto para desarrollo local con `uvicorn`
- ✅ Ejecuta `Base.metadata.create_all()` al iniciar
- ✅ Crea usuarios por defecto automáticamente

### **`api/index.py`** (Vercel Production)
- ✅ **NO** incluye eventos de startup (incompatibles con Vercel)
- ✅ **NO** crea tablas automáticamente
- ✅ Requiere ejecutar `init_db.py` PRIMERO
- ✅ Optimizado para entornos serverless

### **`init_db.py`** (Inicialización Externa)
- ✅ Script standalone para inicializar la base de datos
- ✅ Crea todas las tablas
- ✅ Inserta usuarios por defecto
- ✅ Configura el sistema
- ✅ Se ejecuta UNA SOLA VEZ antes del primer deploy

---

## 🛠️ Configuración Inicial

### 1️⃣ **Instalar Dependencias**

```bash
pip install -r requirements.txt
```

### 2️⃣ **Configurar Variables de Entorno**

Crea un archivo `.env` con:

```env
DATABASE_URL=postgresql://usuario:contraseña@host:puerto/database
SECRET_KEY=tu_clave_secreta_super_segura
```

**Ejemplo:**
```env
DATABASE_URL=postgresql://gruplomi_user:GrupLomi2024%23Secure!@localhost:5433/gruplomi_tickets
SECRET_KEY=GrupLomi2024SecretKey
```

### 3️⃣ **Inicializar Base de Datos**

**⚠️ IMPORTANTE:** Ejecuta esto **UNA VEZ** antes del primer uso:

```bash
python init_db.py
```

Este script:
- ✅ Crea todas las tablas necesarias
- ✅ Inserta usuarios por defecto:
  - `admin@gruplomi.com` / `admin123`
  - `supervisor@gruplomi.com` / `super123`
  - `empleado@gruplomi.com` / `empleado123`
  - `contabilidad@gruplomi.com` / `conta123`
- ✅ Configura parámetros del sistema

---

## 🖥️ Desarrollo Local

### **Opción A: Usando `main.py`** (Recomendado)

```bash
python main.py
```

O con uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Ventajas:**
- ✅ Inicialización automática de DB
- ✅ Hot reload
- ✅ Fácil debugging

### **Opción B: Usando `api/index.py`**

```bash
# Primero inicializar DB
python init_db.py

# Luego ejecutar
uvicorn api.index:app --reload
```

**Nota:** Esta opción es más cercana al entorno de Vercel.

---

## 🌐 Deploy en Vercel

### **Paso 1: Preparar la Base de Datos**

Antes del deploy, asegúrate de:

1. Tener una base de datos PostgreSQL accesible públicamente
2. Ejecutar `init_db.py` **UNA VEZ** con la URL de producción:

```bash
# Temporal - actualizar DATABASE_URL en .env
DATABASE_URL=postgresql://user:pass@host:port/db python init_db.py
```

### **Paso 2: Configurar Variables de Entorno en Vercel**

En el dashboard de Vercel, agregar:

```
DATABASE_URL=postgresql://usuario:contraseña@host:puerto/database
SECRET_KEY=clave_secreta_super_segura
```

### **Paso 3: Deploy**

```bash
# Opción 1: Git push (auto-deploy)
git add .
git commit -m "Deploy backend"
git push origin main

# Opción 2: Vercel CLI
vercel --prod
```

### **Paso 4: Verificar**

```bash
curl https://tu-dominio.vercel.app/
curl https://tu-dominio.vercel.app/health
```

---

## 🧪 Testing de Endpoints

### **Health Check**

```bash
curl http://localhost:8000/health
```

### **Login**

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@gruplomi.com",
    "password": "admin123"
  }'
```

### **Obtener Gastos (con token)**

```bash
curl http://localhost:8000/gastos \
  -H "Authorization: Bearer TU_TOKEN_AQUI"
```

---

## 📚 Endpoints Disponibles

### **Autenticación**
- `POST /auth/login` - Iniciar sesión
- `GET /auth/me` - Obtener usuario actual

### **Usuarios** (Solo Admin)
- `GET /usuarios` - Listar usuarios
- `POST /usuarios` - Crear usuario
- `PUT /usuarios/{id}` - Actualizar usuario
- `DELETE /usuarios/{id}` - Desactivar usuario

### **Gastos**
- `GET /gastos` - Listar gastos (filtrados por rol)
- `POST /gastos` - Crear gasto
- `PUT /gastos/{id}` - Actualizar gasto
- `DELETE /gastos/{id}` - Eliminar gasto

### **Configuración**
- `GET /config/admin` - Configuración admin
- `GET /config/sistema` - Configuración del sistema

---

## 🔐 Roles y Permisos

### **Admin**
- ✅ Acceso total a todas las funciones
- ✅ Gestión de usuarios
- ✅ Ver todos los gastos
- ✅ Aprobar/rechazar gastos

### **Supervisor**
- ✅ Ver gastos propios y de empleados asignados
- ✅ Aprobar/rechazar gastos de empleados
- ❌ No puede gestionar usuarios

### **Contabilidad**
- ✅ Ver todos los gastos
- ✅ Aprobar/rechazar gastos
- ❌ No puede gestionar usuarios

### **Empleado**
- ✅ Ver solo gastos propios
- ✅ Crear nuevos gastos
- ✅ Editar gastos pendientes
- ❌ No puede aprobar gastos

---

## ⚠️ Solución de Problemas

### **Error: No se puede conectar a la base de datos**

```bash
# Verificar que PostgreSQL está corriendo
pg_isready -h localhost -p 5433

# Verificar credenciales en .env
cat .env
```

### **Error: Tablas no existen**

```bash
# Ejecutar inicialización
python init_db.py
```

### **Error en Vercel: 500 Internal Server Error**

1. Verificar variables de entorno en Vercel
2. Verificar que `init_db.py` se ejecutó con la URL de producción
3. Revisar logs en Vercel Dashboard

### **Error: Token inválido**

El token expira después de 24 horas. Hacer login nuevamente.

---

## 📝 Notas Importantes

1. **Nunca subir `.env` a Git** - Contiene credenciales sensibles
2. **Ejecutar `init_db.py` solo UNA VEZ** por base de datos
3. **En producción, cambiar `allow_origins=["*"]`** por dominios específicos
4. **Backup regular de la base de datos**
5. **Rotar `SECRET_KEY` periódicamente**

---

## 🚀 Próximos Pasos

1. [ ] Configurar dominio personalizado en Vercel
2. [ ] Implementar upload de archivos para recibos
3. [ ] Agregar notificaciones por email
4. [ ] Implementar reportes PDF
5. [ ] Agregar dashboard de analytics

---

## 📞 Soporte

Para problemas o preguntas, contactar al equipo de desarrollo.

---

**¡Listo para producción!** 🎉
