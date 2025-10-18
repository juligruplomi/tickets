@echo off
cls
echo ═══════════════════════════════════════════════════════════════
echo    RESTAURAR BACKEND REAL CON POSTGRESQL
echo ═══════════════════════════════════════════════════════════════
echo.
echo Cambios:
echo 1. Reemplazado index.py (demo) con backend FastAPI real
echo 2. Actualizado requirements.txt con SQLAlchemy + psycopg2
echo 3. Backend se conectará a PostgreSQL externo
echo.
echo Presiona ENTER para hacer push...
pause > nul
echo.
cd C:\Tickets
echo [1/3] Agregando cambios...
git add index.py requirements.txt
echo.
echo [2/3] Haciendo commit...
git commit -m "Replace demo backend with real FastAPI+PostgreSQL backend"
echo.
echo [3/3] Haciendo push...
git push origin main
echo.
if %ERRORLEVEL% EQU 0 (
    echo ═══════════════════════════════════════════════════════════════
    echo ✓ PUSH EXITOSO
    echo ═══════════════════════════════════════════════════════════════
    echo.
    echo El backend ahora se conectará a PostgreSQL.
    echo.
    echo Espera 2 minutos para el deployment en Vercel.
    echo Luego prueba el login en: https://tickets.gruplomi.com
    echo.
    echo Credenciales: admin@gruplomi.com / AdminGrupLomi2025
    echo.
) else (
    echo ═══════════════════════════════════════════════════════════════
    echo ✗ ERROR EN PUSH
    echo ═══════════════════════════════════════════════════════════════
)
pause
