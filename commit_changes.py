import subprocess
import os

os.chdir(r"C:\Tickets")

# Git commands para subir los cambios
commands = [
    ["git", "add", "api-backend/main.py"],
    ["git", "commit", "-m", "Fix Vercel CORS and file system issues\n\n- Update CORS origins for production\n- Remove file system operations that cause errors in Vercel\n- Force redeploy to fix cached issues"],
    ["git", "push", "origin", "main"]
]

for cmd in commands:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✓ {' '.join(cmd)}")
        if result.stdout:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"✗ Error en {' '.join(cmd)}: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        break
else:
    print("\n✅ Cambios subidos a GitHub correctamente!")
    print("🚀 Vercel debería redesplegar automáticamente")
    print("📍 Verifica en: https://tickets-alpha-pink.vercel.app/health")
