@echo off
cls
echo ═══════════════════════════════════════════════════════════════
echo    PUSH CORRECCIÓN #2: Arreglar ruta de index.py
echo ═══════════════════════════════════════════════════════════════
echo.
echo Problema encontrado: vercel.json apuntaba a api/index.py
echo pero el archivo está en index.py (raíz)
echo.
echo Presiona ENTER para hacer push de la corrección...
pause > nul
echo.
cd C:\Tickets
echo Agregando cambios...
git add vercel.json
echo.
echo Haciendo commit...
git commit -m "Fix: Change vercel.json to point to index.py in root (not api/index.py)"
echo.
echo Haciendo push...
git push origin main
echo.
if %ERRORLEVEL% EQU 0 (
    echo ═══════════════════════════════════════════════════════════════
    echo ✓ PUSH EXITOSO
    echo ═══════════════════════════════════════════════════════════════
    echo.
    echo Vercel desplegará en 1-2 minutos.
    echo El error de CORS debería solucionarse.
    echo.
    echo Verifica: https://vercel.com/juligruplomis-projects/tickets
    echo.
) else (
    echo ═══════════════════════════════════════════════════════════════
    echo ✗ ERROR EN PUSH
    echo ═══════════════════════════════════════════════════════════════
)
pause
