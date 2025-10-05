@echo off
echo ==========================================
echo     SISTEMA DE GASTOS GRUPLOMI
echo     Iniciando Backend y Frontend
echo ==========================================
echo.

echo PASO 1: Estableciendo túnel SSH...
echo Por favor, abre otra ventana de PowerShell y ejecuta:
echo.
echo     ssh -L 5433:localhost:5432 lomi@185.194.59.40
echo.
echo Presiona cualquier tecla cuando el túnel esté establecido...
pause > nul

echo.
echo PASO 2: Instalando dependencias del backend...
cd C:\Tickets\backend-fastapi
if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
)

echo Activando entorno virtual...
call venv\Scripts\activate.bat

echo Instalando paquetes...
pip install -r requirements.txt > nul 2>&1

echo.
echo PASO 3: Iniciando servidor backend...
echo El backend estará en: http://localhost:8000
echo.
start cmd /k "cd C:\Tickets\backend-fastapi && venv\Scripts\activate.bat && python main.py"

timeout /t 5 /nobreak > nul

echo.
echo PASO 4: Iniciando frontend React...
echo El frontend estará en: http://localhost:3000
echo.
cd C:\tickets-frontend

if not exist "node_modules" (
    echo Instalando dependencias de React...
    npm install
)

echo.
echo ==========================================
echo     SISTEMA LISTO!
echo ==========================================
echo.
echo Backend API: http://localhost:8000
echo Frontend:    http://localhost:3000
echo.
echo Usuarios de prueba:
echo   admin@gruplomi.com / admin123 (Administrador)
echo   supervisor@gruplomi.com / super123 (Supervisor)
echo   empleado@gruplomi.com / empleado123 (Empleado)
echo   contabilidad@gruplomi.com / conta123 (Contabilidad)
echo.
echo Iniciando aplicación...
npm start
