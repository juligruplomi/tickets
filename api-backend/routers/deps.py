import os, logging
from typing import Optional, Set, Callable
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from models import user as usuario_model
from models import role as role_model

SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

_ROLE_MAP = {
    "operario":"operari","operaria":"operari",
    "contabilidad":"comptabilitat","comptable":"comptabilitat",
    "contable":"comptabilitat","finance":"comptabilitat",
    "administrador":"admin","administradora":"admin","supervisora":"supervisor",
}
def _norm_role(v: Optional[str]) -> str:
    v = (v or "").strip().lower()
    return _ROLE_MAP.get(v, v)

def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    cred_exc = HTTPException(status_code=401, detail="No autenticado")
    if not token:
        token = request.cookies.get("access_token")
    if not token:
        raise cred_exc
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        role_claim = _norm_role(payload.get("rol") or payload.get("role"))
        if not email:
            raise cred_exc
    except JWTError:
        raise cred_exc

    user = usuario_model.get_usuario(email)
    if not user:
        raise cred_exc

    db_role = _norm_role(user.rol)
    role = db_role or role_claim
    return {"sub": user.email, "role": role, "db_role": db_role, "token_role": role_claim}

def require_permissions(*perms_required: str) -> Callable:
    required = set(perms_required)
    def _dep(request: Request, current=Depends(get_current_user)):
        role = _norm_role(current.get("role"))
        r = role_model.get_role(role)
        perms = set((r.permissions if r else []) or [])
        if not required.issubset(perms):
            logging.warning("RBAC deny user=%s role=%s need=%s have=%s path=%s",
                            current.get("sub"), role, sorted(required), sorted(perms), request.url.path)
            raise HTTPException(status_code=403, detail="Forbidden")
        return current
    return _dep