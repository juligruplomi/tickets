# 🚀 GUÍA RÁPIDA DE DEPLOY A VERCEL

## ✅ CHECKLIST PRE-DEPLOY

### 1️⃣ Verificar Archivos Creados
```bash
cd C:\Tickets\backend-fastapi
dir
```

Debes ver:
- ✅ `api/index.py` (versión Vercel)
- ✅ `main.py` (versión local intacta)
- ✅ `init_db.py` (inicializador de DB)
- ✅ `vercel.json` (configuración actualizada)
- ✅ `requirements.txt`
- ✅ `.gitignore`
- ✅ `README.md`

### 2️⃣ Inicializar Base de Datos
```bash
# IMPORTANTE: Ejecutar SOLO UNA VEZ antes del primer deploy
python init_db.py
```

Esto creará:
- ✅ Todas las tablas
- ✅ Usuarios por defecto (admin, supervisor, empleado, contabilidad)
- ✅ Configuración del sistema

### 3️⃣ Preparar Git
```bash
cd C:\Tickets\backend-fastapi

# Agregar todos los archivos nuevos
git add .

# Commit
git commit -m "✨ Backend compatible con Vercel - Sin eventos de startup"

# Push
git push origin main
```

---

## 🌐 DEPLOY EN VERCEL

### Opción A: Auto-Deploy (Recomendado)
1. Vercel detectará el push automáticamente
2. Iniciará el build
3. Desplegará la nueva versión

### Opción B: Manual Deploy
```bash
# Usando Vercel CLI
vercel --prod
```

---

## ⚙️ CONFIGURAR VARIABLES DE ENTORNO EN VERCEL

1. Ve a: https://vercel.com/dashboard
2. Selecciona tu proyecto "tickets"
3. Ve a **Settings** → **Environment Variables**
4. Agregar:

```
DATABASE_URL = postgresql://gruplomi_user:GrupLomi2024%23Secure!@tu-host:puerto/gruplomi_tickets
SECRET_KEY = GrupLomi2024SecretKey
```

5. Click **Save**
6. **Redeploy** el proyecto para aplicar cambios

---

## 🧪 PROBAR EL DEPLOY

### 1. Health Check
```bash
curl https://tickets-alpha-pink.vercel.app/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-08T..."
}
```

### 2. Root Endpoint
```bash
curl https://tickets-alpha-pink.vercel.app/
```

Respuesta esperada:
```json
{
  "message": "API de Gastos GrupLomi v1.0 - Vercel",
  "status": "online",
  "version": "1.0.0"
}
```

### 3. Login Test
```bash
curl -X POST https://tickets-alpha-pink.vercel.app/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@gruplomi.com",
    "password": "admin123"
  }'
```

Si recibes un token JWT, ¡está funcionando! 🎉

---

## 🔧 SOLUCIÓN DE PROBLEMAS

### ❌ Error: 500 Internal Server Error

**Causa probable:** Variables de entorno no configuradas

**Solución:**
1. Verifica que las variables estén en Vercel
2. Haz un **Redeploy** después de agregar variables

### ❌ Error: No se puede conectar a la base de datos

**Causa probable:** URL de base de datos incorrecta o DB no accesible

**Solución:**
1. Verifica que la base de datos PostgreSQL sea accesible públicamente
2. Verifica las credenciales en DATABASE_URL
3. Ejecuta `init_db.py` si no lo has hecho

### ❌ Error: Tablas no existen

**Causa probable:** No se ejecutó `init_db.py`

**Solución:**
```bash
python init_db.py
```

---

## 📊 VERIFICAR LOGS EN VERCEL

1. Ve a https://vercel.com/dashboard
2. Selecciona tu proyecto
3. Click en el último deployment
4. Ve a **Function Logs** para ver errores

---

## ✅ DEPLOYMENT EXITOSO

Si ves:
- ✅ `/health` retorna `{"status": "healthy"}`
- ✅ `/` retorna mensaje de bienvenida
- ✅ `/auth/login` retorna un token JWT

**¡Tu backend está funcionando correctamente en Vercel!** 🎉

---

## 📝 SIGUIENTE PASO

Actualizar el frontend para apuntar a la nueva URL del backend:

```javascript
// En tu frontend (React)
const API_URL = "https://tickets-alpha-pink.vercel.app";
```

---

## 🎯 RESUMEN DE CAMBIOS

### ¿Qué cambió?

1. ✅ **`main.py`**: Intacto para desarrollo local
2. ✅ **`api/index.py`**: Nueva versión sin eventos de startup
3. ✅ **`init_db.py`**: Script de inicialización externa
4. ✅ **`vercel.json`**: Actualizado para apuntar a `api/index.py`

### ¿Por qué estos cambios?

- Vercel NO soporta eventos `@app.on_event("startup")`
- Entornos serverless necesitan inicialización externa
- Separar código de desarrollo del código de producción
- Mejor control sobre la inicialización de la DB

---

**¡Listo para deploy!** 🚀
