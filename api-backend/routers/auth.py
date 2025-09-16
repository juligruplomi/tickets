import os
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import jwt
from models import user as usuario_model
from .deps import _norm_role, get_current_user

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN")
COOKIE_NAME = "access_token"
COOKIE_MAX_AGE = 7 * 24 * 60 * 60

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

def create_access_token(data: dict, expires: timedelta | None = None) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + (expires or timedelta(days=7))
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/login", response_model=LoginResponse)
def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    user = usuario_model.get_usuario(form_data.username)
    if not user or not usuario_model.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuari o contrasenya invàlids")
    role = _norm_role(user.rol)
    token = create_access_token({"sub": user.email, "rol": role})

    response.set_cookie(
        key=COOKIE_NAME, value=token, max_age=COOKIE_MAX_AGE,
        httponly=True, secure=True, samesite="none", path="/",
        domain=COOKIE_DOMAIN if COOKIE_DOMAIN else None,
    )
    return LoginResponse(access_token=token)

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/", domain=COOKIE_DOMAIN if COOKIE_DOMAIN else None)
    return {"detail":"logout ok"}

def _me_payload(current):
    return {"email": current.get("sub"), "role": current.get("role")}

@router.get("/me")
def auth_me(current=Depends(get_current_user)):
    return _me_payload(current)