@echo off
cd C:\Tickets
git add vercel.json
git commit -m "Fix: Remove secret references from vercel.json - use Dashboard env vars instead"
git push origin main
echo.
echo ========================================
echo Push completado! Vercel desplegara automaticamente
echo ========================================
pause
