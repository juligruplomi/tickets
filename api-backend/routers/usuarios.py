from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from models.db import get_db
from models.user import User, create_usuario, get_usuario, set_password
from models.user_preferences import get_user_preferences, update_user_preferences
from .deps import require_permissions, get_current_user

router = APIRouter()

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    rol: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    employee_code: Optional[str] = None

class UserResponse(BaseModel):
    email: str
    rol: str
    first_name: Optional[str]
    last_name: Optional[str]
    employee_code: Optional[str]

class UserUpdate(BaseModel):
    rol: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    employee_code: Optional[str] = None

class PreferencesUpdate(BaseModel):
    theme: Optional[str] = None
    language: Optional[str] = None
    notifications: Optional[bool] = None
    currency: Optional[str] = None

@router.post("/", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    current_user=Depends(require_permissions("users:manage")),
    db: Session = Depends(get_db)
):
    """Crear un nuevo usuario (solo admin)"""
    existing_user = get_usuario(user_data.email)
    if existing_user:
        raise HTTPException(400, "El usuario ya existe")
    
    user = create_usuario(
        email=user_data.email,
        password=user_data.password,
        rol=user_data.rol,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        employee_code=user_data.employee_code
    )
    
    return UserResponse(
        email=user.email,
        rol=user.rol,
        first_name=user.first_name,
        last_name=user.last_name,
        employee_code=user.employee_code
    )

@router.get("/", response_model=List[UserResponse])
def list_users(
    current_user=Depends(require_permissions("users:manage")),
    db: Session = Depends(get_db)
):
    """Listar todos los usuarios"""
    users = db.query(User).all()
    return [
        UserResponse(
            email=user.email,
            rol=user.rol,
            first_name=user.first_name,
            last_name=user.last_name,
            employee_code=user.employee_code
        )
        for user in users
    ]

@router.get("/{email}", response_model=UserResponse)
def get_user(
    email: str,
    current_user=Depends(require_permissions("users:manage")),
    db: Session = Depends(get_db)
):
    """Obtener un usuario específico"""
    user = get_usuario(email)
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    
    return UserResponse(
        email=user.email,
        rol=user.rol,
        first_name=user.first_name,
        last_name=user.last_name,
        employee_code=user.employee_code
    )

@router.put("/{email}", response_model=UserResponse)
def update_user(
    email: str,
    user_data: UserUpdate,
    current_user=Depends(require_permissions("users:manage")),
    db: Session = Depends(get_db)
):
    """Actualizar un usuario"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    
    if user_data.rol is not None:
        user.rol = user_data.rol
    if user_data.first_name is not None:
        user.first_name = user_data.first_name
    if user_data.last_name is not None:
        user.last_name = user_data.last_name
    if user_data.employee_code is not None:
        user.employee_code = user_data.employee_code
    
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        email=user.email,
        rol=user.rol,
        first_name=user.first_name,
        last_name=user.last_name,
        employee_code=user.employee_code
    )

@router.delete("/{email}")
def delete_user(
    email: str,
    current_user=Depends(require_permissions("users:manage")),
    db: Session = Depends(get_db)
):
    """Eliminar un usuario"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    
    if email == current_user["sub"]:
        raise HTTPException(400, "No puedes eliminar tu propio usuario")
    
    db.delete(user)
    db.commit()
    
    return {"message": "Usuario eliminado correctamente"}

@router.get("/{email}/preferences")
def get_user_prefs(
    email: str,
    current_user=Depends(get_current_user)
):
    """Obtener preferencias de usuario"""
    if email != current_user["sub"] and current_user.get("role") != "admin":
        raise HTTPException(403, "No tienes permisos para ver estas preferencias")
    
    prefs = get_user_preferences(email)
    return {
        "theme": prefs.theme,
        "language": prefs.language,
        "notifications": prefs.notifications,
        "currency": prefs.currency
    }

@router.put("/{email}/preferences")
def update_user_prefs(
    email: str,
    preferences: PreferencesUpdate,
    current_user=Depends(get_current_user)
):
    """Actualizar preferencias de usuario"""
    if email != current_user["sub"]:
        raise HTTPException(403, "Solo puedes actualizar tus propias preferencias")
    
    prefs_dict = {k: v for k, v in preferences.dict().items() if v is not None}
    updated_prefs = update_user_preferences(email, prefs_dict)
    
    return {
        "theme": updated_prefs.theme,
        "language": updated_prefs.language,
        "notifications": updated_prefs.notifications,
        "currency": updated_prefs.currency
    }