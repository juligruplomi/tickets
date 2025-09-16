from sqlalchemy import Column, String, Boolean
from .db import Base, SessionLocal

class UserPreferences(Base):
    __tablename__ = "user_preferences"
    
    user_email = Column(String, primary_key=True)
    theme = Column(String, default="light")  # light, dark
    language = Column(String, default="es")  # es, ca, en, fr, de
    notifications = Column(Boolean, default=True)
    currency = Column(String, default="EUR")

def get_user_preferences(email: str):
    """Obtener preferencias de usuario"""
    with SessionLocal() as db:
        prefs = db.query(UserPreferences).filter(UserPreferences.user_email == email).first()
        if not prefs:
            # Crear preferencias por defecto
            prefs = UserPreferences(user_email=email)
            db.add(prefs)
            db.commit()
            db.refresh(prefs)
        return prefs

def update_user_preferences(email: str, preferences: dict):
    """Actualizar preferencias de usuario"""
    with SessionLocal() as db:
        prefs = db.query(UserPreferences).filter(UserPreferences.user_email == email).first()
        if not prefs:
            prefs = UserPreferences(user_email=email)
            db.add(prefs)
        
        for key, value in preferences.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)
        
        db.commit()
        db.refresh(prefs)
        return prefs