from sqlalchemy import Column, String
from sqlalchemy.types import JSON
from .db import Base, SessionLocal

# Catálogo base de permisos
GLOBAL_PERMISSIONS = [
    "tickets:create","tickets:delete","tickets:view",
    "tickets:validate","tickets:unvalidate","tickets:reject",
    "tickets:pay","tickets:unpay",
    "roles:manage","users:manage","config:manage",
]

class Role(Base):
    __tablename__ = "roles"
    name = Column(String, primary_key=True, index=True)
    permissions = Column(JSON, nullable=False, default=list)

def create_role(name: str, permissions: list[str]):
    with SessionLocal() as db:
        r = db.get(Role, name)
        if not r:
            r = Role(name=name, permissions=permissions)
            db.add(r)
        else:
            r.permissions = permissions
        db.commit()
        db.refresh(r)
        return r

def get_role(name: str):
    with SessionLocal() as db:
        return db.get(Role, name)

def list_roles():
    with SessionLocal() as db:
        return db.query(Role).order_by(Role.name.asc()).all()

def delete_role(name: str) -> bool:
    with SessionLocal() as db:
        r = db.get(Role, name)
        if not r:
            return False
        db.delete(r)
        db.commit()
        return True

def ensure_base_roles():
    create_role("operari", ["tickets:create","tickets:delete","tickets:view"])
    base_super = ["tickets:validate","tickets:unvalidate","tickets:reject","tickets:pay","tickets:unpay","tickets:view"]
    create_role("supervisor", ["tickets:create","tickets:delete"] + base_super)
    create_role("comptabilitat", base_super)
    create_role("admin", GLOBAL_PERMISSIONS)