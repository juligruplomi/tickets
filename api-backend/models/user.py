from sqlalchemy import Column, String
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from .db import Base, SessionLocal

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    email = Column(String, primary_key=True, index=True)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    employee_code = Column(String, nullable=True)
    rol = Column(String, nullable=False)  # nombre de rol

def create_usuario(email: str, password: str, rol: str, **extra):
    with SessionLocal() as db:
        u = db.get(User, email)
        if u:
            return u
        u = User(
            email=email,
            hashed_password=pwd_context.hash(password),
            rol=rol,
            **extra
        )
        db.add(u)
        db.commit()
        db.refresh(u)
        return u

def get_usuario(email: str):
    with SessionLocal() as db:
        return db.get(User, email)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def set_password(email: str, new_password: str):
    with SessionLocal() as db:
        u = db.get(User, email)
        if not u:
            return False
        u.hashed_password = pwd_context.hash(new_password)
        db.commit()
        return True