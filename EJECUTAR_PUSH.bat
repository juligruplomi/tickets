@echo off
cls
echo ═══════════════════════════════════════════════════════════════
echo    PUSH DE CORRECCIÓN A GITHUB
echo ═══════════════════════════════════════════════════════════════
echo.
echo Este script hará push del vercel.json corregido a GitHub.
echo.
echo Presiona ENTER para continuar o CTRL+C para cancelar...
pause > nul
echo.
echo ═══════════════════════════════════════════════════════════════
echo Cambiando al directorio del proyecto...
echo ═══════════════════════════════════════════════════════════════
cd C:\Tickets
echo.
echo Directorio actual: %CD%
echo.
echo ═══════════════════════════════════════════════════════════════
echo Verificando estado de Git...
echo ═══════════════════════════════════════════════════════════════
git status
echo.
echo ═══════════════════════════════════════════════════════════════
echo Agregando vercel.json...
echo ═══════════════════════════════════════════════════════════════
git add vercel.json
echo.
echo ═══════════════════════════════════════════════════════════════
echo Haciendo commit...
echo ═══════════════════════════════════════════════════════════════
git commit -m "Fix: Remove secret references from vercel.json - use Dashboard env vars instead"
if %ERRORLEVEL% EQU 0 (
    echo ✓ Commit exitoso
) else (
    echo ! No hay cambios para hacer commit (esto es normal si ya se hizo)
)
echo.
echo ═══════════════════════════════════════════════════════════════
echo Haciendo PUSH a GitHub...
echo ═══════════════════════════════════════════════════════════════
echo.
git push origin main
echo.
if %ERRORLEVEL% EQU 0 (
    echo ═══════════════════════════════════════════════════════════════
    echo ✓✓✓ PUSH EXITOSO ✓✓✓
    echo ═══════════════════════════════════════════════════════════════
    echo.
    echo El cambio se ha subido a GitHub correctamente.
    echo Vercel desplegará automáticamente en 1-2 minutos.
    echo.
    echo Verifica el deployment en:
    echo https://vercel.com/juligruplomis-projects/tickets
    echo.
    echo El error de GitHub debería desaparecer ahora.
    echo.
) else (
    echo ═══════════════════════════════════════════════════════════════
    echo ✗✗✗ ERROR EN PUSH ✗✗✗
    echo ═══════════════════════════════════════════════════════════════
    echo.
    echo Posibles causas:
    echo - No tienes acceso a internet
    echo - Necesitas autenticarte con GitHub
    echo - El repositorio requiere token de acceso personal
    echo.
    echo Intenta:
    echo 1. Verificar tu conexión a internet
    echo 2. Configurar credenciales de GitHub si es necesario
    echo.
)
echo.
echo ═══════════════════════════════════════════════════════════════
pause
