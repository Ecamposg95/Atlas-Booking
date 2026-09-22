import hashlib
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session, joinedload

from app.models import Appointment, AppointmentStatus, Customer, Service
from app.schemas import AppointmentCreate
from app.services.availability import available_slots
from app.services.google_calendar import CalendarGateway

logger = logging.getLogger(__name__)


def _lock(db: Session, staff_id: str, start: datetime) -> None:
    if db.bind and db.bind.dialect.name == "postgresql":
        key = int(hashlib.sha256(f"{staff_id}:{start.date()}".encode()).hexdigest()[:15], 16)
        db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})


def create_appointment(db: Session, payload: AppointmentCreate, calendar: CalendarGateway) -> Appointment:
    local_start = payload.start_at if payload.start_at.tzinfo else payload.start_at.replace(tzinfo=ZoneInfo(payload.timezone))
    requested_day = local_start.astimezone(ZoneInfo(payload.timezone)).date()
    service = db.scalar(select(Service).options(joinedload(Service.staff_member)).where(Service.id == payload.service_id, Service.staff_member_id == payload.staff_member_id, Service.active.is_(True)))
    if not service:
        raise HTTPException(404, "Service not found for this professional")
    _lock(db, str(payload.staff_member_id), local_start)
    slots = available_slots(db, service, requested_day, payload.timezone, calendar)
    start_utc = local_start.astimezone(ZoneInfo("UTC"))
    match = next((end for start, end in slots if start == start_utc), None)
    if not match:
        raise HTTPException(409, "This time is no longer available")
    customer = db.scalar(select(Customer).where(Customer.email == str(payload.customer.email)))
    if customer is None:
        customer = Customer(name=payload.customer.name, email=str(payload.customer.email), phone=payload.customer.phone)
        db.add(customer)
        db.flush()
    else:
        customer.name, customer.phone = payload.customer.name, payload.customer.phone
    appointment = Appointment(staff_member_id=service.staff_member_id, service_id=service.id, customer_id=customer.id, start_at=start_utc, end_at=match, timezone=payload.timezone, notes=payload.notes, status=AppointmentStatus.pending)
    db.add(appointment)
    db.flush()
    try:
        appointment.google_event_id = calendar.create_event(service.staff_member.calendar_id, f"Atlas Booking: {service.name}", start_utc, match, payload.timezone, f"Cliente: {customer.name}")
        appointment.google_calendar_id = service.staff_member.calendar_id
        appointment.status = AppointmentStatus.confirmed
        db.commit()
    except Exception as error:
        db.rollback()
        logger.exception("calendar_event_creation_failed", extra={"appointment_id": str(appointment.id)})
        raise HTTPException(502, "Unable to confirm the appointment right now") from error
    db.refresh(appointment)
    return appointment
