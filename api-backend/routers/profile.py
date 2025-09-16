from fastapi import APIRouter, Depends
from .deps import get_current_user, _norm_role
from models.role import get_role

router = APIRouter()

@router.get("/me")
def root_me(current=Depends(get_current_user)):
    role_name = _norm_role(current.get("role"))
    r = get_role(role_name)
    perms = (r.permissions if r else []) or []
    return {"email": current.get("sub"), "role": role_name, "permissions": perms}