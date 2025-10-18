Set-Location "C:\Tickets"
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   EJECUTANDO PUSH A GITHUB" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Write-Host "Verificando estado de Git..." -ForegroundColor Green
git status
Write-Host ""

Write-Host "Agregando vercel.json..." -ForegroundColor Green
git add vercel.json
Write-Host ""

Write-Host "Haciendo commit..." -ForegroundColor Green
git commit -m "Fix: Remove secret references from vercel.json - use Dashboard env vars instead"
Write-Host ""

Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "Haciendo PUSH a GitHub..." -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "✓✓✓ PUSH EXITOSO ✓✓✓" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    Write-Host "El cambio se ha subido a GitHub correctamente." -ForegroundColor White
    Write-Host "Vercel desplegará automáticamente en 1-2 minutos." -ForegroundColor White
    Write-Host ""
    Write-Host "Verifica el deployment en:" -ForegroundColor Cyan
    Write-Host "https://vercel.com/juligruplomis-projects/tickets" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Red
    Write-Host "✗✗✗ ERROR EN PUSH ✗✗✗" -ForegroundColor Red
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Red
    Write-Host ""
    Write-Host "Código de error: $LASTEXITCODE" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Presiona ENTER para continuar"
