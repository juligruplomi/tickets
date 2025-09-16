from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from models.role import list_roles, create_role, delete_role, get_role
from .deps import require_permissions

router = APIRouter()

class RoleIn(BaseModel):
    name: str
    permissions: list[str]

@router.get("/roles/")
def get_roles(current=Depends(require_permissions("roles:manage"))):
    return [{"name": r.name, "permissions": r.permissions} for r in list_roles()]

@router.post("/roles/")
def post_role(payload: RoleIn, current=Depends(require_permissions("roles:manage"))):
    r = create_role(payload.name, payload.permissions)
    return {"name": r.name, "permissions": r.permissions}

@router.put("/roles/{name}")
def put_role(name: str, payload: RoleIn, current=Depends(require_permissions("roles:manage"))):
    r = create_role(name, payload.permissions)
    return {"name": r.name, "permissions": r.permissions}

@router.delete("/roles/{name}")
def del_role(name: str, current=Depends(require_permissions("roles:manage"))):
    ok = delete_role(name)
    if not ok:
        raise HTTPException(404, "not found")
    return {"ok": True}