from sqlalchemy import Column, String, Text
from .db import Base, SessionLocal

class SiteConfig(Base):
    __tablename__ = "site_config"
    
    key = Column(String, primary_key=True)
    value = Column(Text, nullable=True)

# Configuraciones por defecto
DEFAULT_CONFIG = {
    'site_name': 'GestióGastos',
    'company_name': 'Grup Lomi',
    'logo_url': '',
    'primary_color': '#3B82F6',
    'currency': 'EUR',
    'default_km_price': '0.57',
    'auto_validate_under': '50',
    'require_photo_for': 'Dieta,Parking',
    'supported_languages': 'es,ca,en,fr,de',
    'default_language': 'es',
    'default_theme': 'light',
    'admin_email': 'admin@gruplomi.com',
    'notifications_enabled': 'true',
    'backup_enabled': 'true',
    'max_file_size_mb': '10'
}

def get_config(key: str, default=None):
    """Obtener configuración"""
    with SessionLocal() as db:
        config = db.query(SiteConfig).filter(SiteConfig.key == key).first()
        if config:
            return config.value
        return DEFAULT_CONFIG.get(key, default)

def set_config(key: str, value: str):
    """Establecer configuración"""
    with SessionLocal() as db:
        config = db.query(SiteConfig).filter(SiteConfig.key == key).first()
        if config:
            config.value = value
        else:
            config = SiteConfig(key=key, value=value)
            db.add(config)
        db.commit()
        return config

def get_all_config():
    """Obtener toda la configuración"""
    config = DEFAULT_CONFIG.copy()
    with SessionLocal() as db:
        db_configs = db.query(SiteConfig).all()
        for db_config in db_configs:
            config[db_config.key] = db_config.value
    return config

def init_default_config():
    """Inicializar configuración por defecto"""
    for key, value in DEFAULT_CONFIG.items():
        if not get_config(key):
            set_config(key, value)