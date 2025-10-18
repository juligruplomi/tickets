@echo off
echo ========================================
echo Fixing vercel.json and pushing to GitHub
echo ========================================
echo.

cd C:\Tickets

echo Current git status:
git status
echo.

echo Adding vercel.json...
git add vercel.json
echo.

echo Committing changes...
git commit -m "Fix: Remove secret references from vercel.json - use Dashboard env vars"
echo.

echo Pushing to GitHub...
git push origin main
echo.

echo ========================================
echo DONE! Check GitHub and Vercel
echo ========================================
pause
