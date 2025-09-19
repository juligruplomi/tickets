import os
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Boolean, Date, Float, DateTime, Text
from sqlalchemy.orm import Session
from .db import Base, SessionLocal

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
# os.makedirs(UPLOAD_DIR, exist_ok=True)

class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    tipus = Column(String, nullable=False)  # CSV: "Dieta,Parking,Gasolina"
    description = Column(Text, nullable=False)
    project = Column(String, nullable=False)
    total = Column(Float, nullable=False, default=0.0)
    kilometers = Column(Float, nullable=True)  # Solo para gasolina
    price_per_km = Column(Float, nullable=True)  # Solo para gasolina
    image = Column(String, nullable=True)  # Ruta al archivo
    validated = Column(Boolean, default=False)
    paid = Column(Boolean, default=False)
    rejected = Column(Boolean, default=False)
    created_by = Column(String, nullable=False)  # email usuario
    validated_by = Column(String, nullable=True)  # email supervisor
    paid_by = Column(String, nullable=True)  # email contabilidad
    rejected_by = Column(String, nullable=True)  # email quien rechaza
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def status(self):
        if self.rejected:
            return "rejected"
        elif self.paid:
            return "paid"
        elif self.validated:
            return "validated"
        else:
            return "pending"

def create_ticket(data: dict, created_by: str):
    """Crear un nuevo ticket"""
    with SessionLocal() as db:
        ticket = Ticket(
            date=data.get('date', date.today()),
            tipus=','.join(data.get('tipus', [])) if isinstance(data.get('tipus'), list) else data.get('tipus', ''),
            description=data['description'],
            project=data['project'],
            total=float(data['total']),
            kilometers=float(data['kilometers']) if data.get('kilometers') else None,
            price_per_km=float(data['price_per_km']) if data.get('price_per_km') else None,
            image=data.get('image_path'),
            created_by=created_by
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return ticket

def get_tickets_by_user(email: str, db: Session):
    """Obtener tickets de un usuario"""
    return db.query(Ticket).filter(Ticket.created_by == email).order_by(Ticket.created_at.desc()).all()

def get_all_tickets(db: Session, status_filter: str = None, user_filter: str = None):
    """Obtener todos los tickets con filtros opcionales"""
    query = db.query(Ticket)
    
    if user_filter:
        query = query.filter(Ticket.created_by == user_filter)
    
    if status_filter and status_filter != 'all':
        if status_filter == 'pending':
            query = query.filter(Ticket.validated == False, Ticket.rejected == False)
        elif status_filter == 'validated':
            query = query.filter(Ticket.validated == True, Ticket.paid == False, Ticket.rejected == False)
        elif status_filter == 'paid':
            query = query.filter(Ticket.paid == True)
        elif status_filter == 'rejected':
            query = query.filter(Ticket.rejected == True)
    
    return query.order_by(Ticket.created_at.desc()).all()

def update_ticket_status(ticket_id: int, action: str, user_email: str, reason: str = None, db: Session = None):
    """Actualizar estado de ticket"""
    if not db:
        db = SessionLocal()
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        return None
    
    if action == 'validate':
        ticket.validated = True
        ticket.validated_by = user_email
    elif action == 'pay':
        ticket.paid = True
        ticket.paid_by = user_email
    elif action == 'reject':
        ticket.rejected = True
        ticket.rejected_by = user_email
        ticket.rejection_reason = reason
    elif action == 'unvalidate':
        ticket.validated = False
        ticket.validated_by = None
    elif action == 'unpay':
        ticket.paid = False
        ticket.paid_by = None
    
    ticket.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(ticket)
    return ticket

def get_user_pending_amount(email: str):
    """Calcular importe pendiente de pago de un usuario"""
    with SessionLocal() as db:
        tickets = db.query(Ticket).filter(
            Ticket.created_by == email,
            Ticket.paid == False,
            Ticket.rejected == False
        ).all()
        return sum(ticket.total for ticket in tickets)

def get_tickets_stats():
    """Obtener estadísticas generales"""
    with SessionLocal() as db:
        total = db.query(Ticket).count()
        pending = db.query(Ticket).filter(
            Ticket.validated == False,
            Ticket.rejected == False
        ).count()
        validated = db.query(Ticket).filter(
            Ticket.validated == True,
            Ticket.paid == False,
            Ticket.rejected == False
        ).count()
        paid = db.query(Ticket).filter(Ticket.paid == True).count()
        rejected = db.query(Ticket).filter(Ticket.rejected == True).count()
        
        return {
            'total': total,
            'pending': pending,
            'validated': validated,
            'paid': paid,
            'rejected': rejected
        }