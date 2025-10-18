@echo off
cd C:\Tickets
echo.
echo Ejecutando git add...
git add vercel.json
echo.
echo Ejecutando git commit...
git commit -m "Fix: Remove secret references from vercel.json"
echo.
echo Ejecutando git push...
git push origin main
echo.
echo HECHO!
pause
