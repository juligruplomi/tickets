import os
import shutil
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.db import get_db
from models.ticket import (
    Ticket, create_ticket, get_tickets_by_user, get_all_tickets,
    update_ticket_status, get_user_pending_amount, get_tickets_stats
)
from .deps import get_current_user, require_permissions

router = APIRouter()

class TicketResponse(BaseModel):
    id: int
    date: str
    tipus: str
    description: str
    project: str
    total: float
    kilometers: Optional[float] = None
    price_per_km: Optional[float] = None
    image: Optional[str] = None
    status: str
    created_by: str
    validated_by: Optional[str] = None
    paid_by: Optional[str] = None
    rejected_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: str
    updated_at: str

class TicketCreate(BaseModel):
    tipus: List[str]  # ["Dieta", "Parking"] o ["Gasolina"]
    description: str
    project: str
    total: Optional[float] = None
    kilometers: Optional[float] = None
    price_per_km: Optional[float] = None

class TicketActionRequest(BaseModel):
    action: str  # validate, pay, reject, unvalidate, unpay
    reason: Optional[str] = None

def ticket_to_response(ticket: Ticket) -> TicketResponse:
    return TicketResponse(
        id=ticket.id,
        date=ticket.date.isoformat(),
        tipus=ticket.tipus,
        description=ticket.description,
        project=ticket.project,
        total=ticket.total,
        kilometers=ticket.kilometers,
        price_per_km=ticket.price_per_km,
        image=f"/uploads/{ticket.image}" if ticket.image else None,
        status=ticket.status,
        created_by=ticket.created_by,
        validated_by=ticket.validated_by,
        paid_by=ticket.paid_by,
        rejected_by=ticket.rejected_by,
        rejection_reason=ticket.rejection_reason,
        created_at=ticket.created_at.isoformat(),
        updated_at=ticket.updated_at.isoformat()
    )

@router.post("/", response_model=TicketResponse)
def create_new_ticket(
    ticket_data: TicketCreate,
    current_user=Depends(require_permissions("tickets:create")),
    db: Session = Depends(get_db)
):
    """Crear un nuevo ticket"""
    
    # Validaciones
    if not ticket_data.tipus:
        raise HTTPException(400, "Debe seleccionar al menos un tipo de ticket")
    
    # Si es gasolina, calcular total automáticamente
    if "Gasolina" in ticket_data.tipus:
        if not ticket_data.kilometers or not ticket_data.price_per_km:
            raise HTTPException(400, "Para tickets de gasolina se requieren kilómetros y precio por km")
        ticket_data.total = ticket_data.kilometers * ticket_data.price_per_km
    else:
        if not ticket_data.total or ticket_data.total <= 0:
            raise HTTPException(400, "Se requiere un importe válido")
    
    # Crear ticket
    ticket_dict = ticket_data.dict()
    ticket = create_ticket(ticket_dict, current_user["sub"])
    
    return ticket_to_response(ticket)

@router.post("/{ticket_id}/image")
def upload_ticket_image(
    ticket_id: int,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Subir imagen para un ticket"""
    
    # Verificar que el ticket existe y pertenece al usuario
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404, "Ticket no encontrado")
    
    # Solo el propietario o admin pueden subir imagen
    if ticket.created_by != current_user["sub"] and current_user.get("role") != "admin":
        raise HTTPException(403, "No tienes permisos para modificar este ticket")
    
    # Validar tipo de archivo
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "Solo se permiten archivos de imagen")
    
    # Crear nombre de archivo único
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"ticket_{ticket_id}_{timestamp}.{file_extension}"
    
    # Guardar archivo
    upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Actualizar ticket con ruta de imagen
    ticket.image = filename
    db.commit()
    
    return {"message": "Imagen subida correctamente", "filename": filename}

@router.get("/", response_model=List[TicketResponse])
def list_tickets(
    status: Optional[str] = Query(None, description="Filtrar por estado: pending, validated, paid, rejected"),
    user: Optional[str] = Query(None, description="Filtrar por usuario"),
    project: Optional[str] = Query(None, description="Filtrar por proyecto"),
    current_user=Depends(require_permissions("tickets:view")),
    db: Session = Depends(get_db)
):
    """Listar tickets con filtros"""
    
    user_role = current_user.get("role")
    user_email = current_user["sub"]
    
    # Los operarios solo ven sus propios tickets
    if user_role == "operari":
        tickets = get_tickets_by_user(user_email, db)
    else:
        # Supervisores, contabilidad y admin pueden ver todos
        tickets = get_all_tickets(db, status, user)
    
    # Filtro adicional por proyecto
    if project:
        tickets = [t for t in tickets if t.project == project]
    
    return [ticket_to_response(ticket) for ticket in tickets]

@router.get("/my-tickets", response_model=List[TicketResponse])
def get_my_tickets(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener mis tickets"""
    tickets = get_tickets_by_user(current_user["sub"], db)
    return [ticket_to_response(ticket) for ticket in tickets]

@router.get("/pending-amount")
def get_pending_amount(current_user=Depends(get_current_user)):
    """Obtener importe pendiente de pago del usuario actual"""
    amount = get_user_pending_amount(current_user["sub"])
    return {"pending_amount": amount, "user": current_user["sub"]}

@router.get("/stats")
def get_statistics(
    current_user=Depends(require_permissions("tickets:view"))
):
    """Obtener estadísticas de tickets"""
    stats = get_tickets_stats()
    return stats

@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener un ticket específico"""
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404, "Ticket no encontrado")
    
    # Verificar permisos
    user_role = current_user.get("role")
    if user_role == "operari" and ticket.created_by != current_user["sub"]:
        raise HTTPException(403, "No tienes permisos para ver este ticket")
    
    return ticket_to_response(ticket)

@router.put("/{ticket_id}/action")
def update_ticket_action(
    ticket_id: int,
    action_request: TicketActionRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Realizar acción sobre un ticket (validar, pagar, rechazar, etc.)"""
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404, "Ticket no encontrado")
    
    action = action_request.action
    user_role = current_user.get("role")
    user_email = current_user["sub"]
    
    # Verificar permisos según acción
    if action in ["validate", "unvalidate"] and user_role not in ["supervisor", "admin"]:
        raise HTTPException(403, "No tienes permisos para validar tickets")
    
    if action in ["pay", "unpay"] and user_role not in ["comptabilitat", "admin"]:
        raise HTTPException(403, "No tienes permisos para pagar tickets")
    
    if action == "reject" and user_role not in ["supervisor", "comptabilitat", "admin"]:
        raise HTTPException(403, "No tienes permisos para rechazar tickets")
    
    # Validaciones de estado
    if action == "validate" and ticket.status != "pending":
        raise HTTPException(400, "Solo se pueden validar tickets pendientes")
    
    if action == "pay" and ticket.status != "validated":
        raise HTTPException(400, "Solo se pueden pagar tickets validados")
    
    if action == "reject" and action_request.reason is None:
        raise HTTPException(400, "Se requiere motivo para rechazar")
    
    # Actualizar ticket
    updated_ticket = update_ticket_status(
        ticket_id, action, user_email, action_request.reason, db
    )
    
    return ticket_to_response(updated_ticket)

@router.delete("/{ticket_id}")
def delete_ticket(
    ticket_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar un ticket (solo si está pendiente)"""
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404, "Ticket no encontrado")
    
    # Solo el creador o admin pueden eliminar
    if ticket.created_by != current_user["sub"] and current_user.get("role") != "admin":
        raise HTTPException(403, "No tienes permisos para eliminar este ticket")
    
    # Solo se pueden eliminar tickets pendientes
    if ticket.status != "pending":
        raise HTTPException(400, "Solo se pueden eliminar tickets pendientes")
    
    # Eliminar imagen asociada si existe
    if ticket.image:
        upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
        image_path = os.path.join(upload_dir, ticket.image)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.delete(ticket)
    db.commit()
    
    return {"message": "Ticket eliminado correctamente"}

@router.get("/{ticket_id}/image")
def get_ticket_image(
    ticket_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener imagen de un ticket"""
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket or not ticket.image:
        raise HTTPException(404, "Imagen no encontrada")
    
    # Verificar permisos
    user_role = current_user.get("role")
    if user_role == "operari" and ticket.created_by != current_user["sub"]:
        raise HTTPException(403, "No tienes permisos para ver esta imagen")
    
    upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    image_path = os.path.join(upload_dir, ticket.image)
    
    if not os.path.exists(image_path):
        raise HTTPException(404, "Archivo de imagen no encontrado")
    
    return FileResponse(image_path)