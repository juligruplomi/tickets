@echo off
echo ═══════════════════════════════════════════════════════════════
echo    VERIFICACIÓN Y CORRECCIÓN DEL ERROR DE VERCEL
echo ═══════════════════════════════════════════════════════════════
echo.
echo PASO 1: Verificando archivo vercel.json local...
echo.
type C:\Tickets\vercel.json
echo.
echo ═══════════════════════════════════════════════════════════════
echo.
echo El archivo vercel.json NO debe contener la seccion "env".
echo Si ves "env" en el archivo de arriba, hay un problema.
echo.
echo ¿El archivo se ve correcto (sin sección "env")? (S/N)
set /p continuar=
if /i "%continuar%" NEQ "S" goto :error
echo.
echo ═══════════════════════════════════════════════════════════════
echo PASO 2: Haciendo commit y push...
echo ═══════════════════════════════════════════════════════════════
echo.
cd C:\Tickets
git add vercel.json
git commit -m "Fix: Remove secret references from vercel.json - use Dashboard env vars instead"
echo.
echo Haciendo push a GitHub...
git push origin main
echo.
if %ERRORLEVEL% NEQ 0 goto :error_push
echo.
echo ═══════════════════════════════════════════════════════════════
echo ✓ PUSH EXITOSO
echo ═══════════════════════════════════════════════════════════════
echo.
echo Vercel desplegará automáticamente en 1-2 minutos.
echo.
echo Verifica el deployment en:
echo https://vercel.com/juligruplomis-projects/tickets
echo.
echo Backend: https://tickets-alpha-pink.vercel.app
echo Frontend: https://tickets.gruplomi.com
echo.
goto :end

:error
echo.
echo ❌ ERROR: El archivo vercel.json necesita corrección manual.
echo Por favor, edita C:\Tickets\vercel.json y elimina la sección "env".
echo.
goto :end

:error_push
echo.
echo ❌ ERROR: No se pudo hacer push a GitHub.
echo Verifica tu conexión y credenciales de Git.
echo.
goto :end

:end
echo ═══════════════════════════════════════════════════════════════
pause
