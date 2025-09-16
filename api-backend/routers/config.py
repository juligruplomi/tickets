from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any

from models.site_config import get_config, set_config, get_all_config
from .deps import require_permissions, get_current_user

router = APIRouter()

class ConfigUpdate(BaseModel):
    site_name: str = None
    company_name: str = None
    logo_url: str = None
    primary_color: str = None
    currency: str = None
    default_km_price: str = None
    auto_validate_under: str = None
    require_photo_for: str = None
    supported_languages: str = None
    default_language: str = None
    default_theme: str = None
    admin_email: str = None
    notifications_enabled: str = None
    backup_enabled: str = None
    max_file_size_mb: str = None

@router.get("/")
def get_site_config(current_user=Depends(get_current_user)):
    """Obtener configuración del sitio"""
    config = get_all_config()
    return config

@router.put("/")
def update_site_config(
    config_data: ConfigUpdate,
    current_user=Depends(require_permissions("config:manage"))
):
    """Actualizar configuración del sitio"""
    updated_config = {}
    
    for key, value in config_data.dict().items():
        if value is not None:
            set_config(key, value)
            updated_config[key] = value
    
    return {"message": "Configuración actualizada", "updated": updated_config}

@router.get("/{config_key}")
def get_config_value(
    config_key: str,
    current_user=Depends(get_current_user)
):
    """Obtener un valor de configuración específico"""
    value = get_config(config_key)
    return {config_key: value}

@router.put("/{config_key}")
def set_config_value(
    config_key: str,
    value: str,
    current_user=Depends(require_permissions("config:manage"))
):
    """Establecer un valor de configuración específico"""
    set_config(config_key, value)
    return {"message": f"Configuración {config_key} actualizada", config_key: value}