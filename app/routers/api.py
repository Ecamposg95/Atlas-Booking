import logging
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Appointment, AppointmentStatus, Service, StaffMember
from app.schemas import AppointmentCreate, AppointmentOut, AvailabilityOut, CancelInput, ServiceOut, SlotOut, StaffOut
from app.services.availability import available_slots
from app.services.booking import create_appointment
from app.services.google_calendar import CalendarGateway, get_calendar_gateway

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)


async def calendar() -> CalendarGateway:
    return get_calendar_gateway()


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/staff", response_model=list[StaffOut])
async def list_staff(db: Session = Depends(get_db)):
    return db.scalars(select(StaffMember).where(StaffMember.active.is_(True)).order_by(StaffMember.name)).all()


@router.get("/services", response_model=list[ServiceOut])
async def list_services(staff_slug: str | None = None, db: Session = Depends(get_db)):
    query = select(Service).join(StaffMember).where(Service.active.is_(True), StaffMember.active.is_(True))
    if staff_slug:
        query = query.where(StaffMember.slug == staff_slug)
    return db.scalars(query.order_by(Service.name)).all()


@router.get("/services/{slug}", response_model=ServiceOut)
async def get_service(slug: str, db: Session = Depends(get_db)):
    service = db.scalar(select(Service).where(Service.slug == slug, Service.active.is_(True)))
    if not service:
        raise HTTPException(404, "Service not found")
    return service


@router.get("/availability", response_model=AvailabilityOut)
async def availability(service_id: uuid.UUID, date_value: date = Query(alias="date"), timezone: str = "America/Mexico_City", db: Session = Depends(get_db), gateway: CalendarGateway = Depends(calendar)):
    service = db.scalar(select(Service).options(joinedload(Service.staff_member)).where(Service.id == service_id, Service.active.is_(True)))
    if not service:
        raise HTTPException(404, "Service not found")
    slots = available_slots(db, service, date_value, timezone, gateway)
    logger.info("availability_requested", extra={"service_id": str(service_id), "date": str(date_value), "slots": len(slots)})
    return AvailabilityOut(date=date_value, timezone=timezone, slots=[SlotOut(start_at=start, end_at=end) for start, end in slots])


def appointment_out(appointment: Appointment) -> AppointmentOut:
    return AppointmentOut(id=appointment.id, status=appointment.status.value, start_at=appointment.start_at, end_at=appointment.end_at, timezone=appointment.timezone, service=ServiceOut.model_validate(appointment.service), staff_member=StaffOut.model_validate(appointment.staff_member), customer_name=appointment.customer.name)


@router.post("/appointments", response_model=AppointmentOut, status_code=201)
async def book(payload: AppointmentCreate, db: Session = Depends(get_db), gateway: CalendarGateway = Depends(calendar)):
    appointment = create_appointment(db, payload, gateway)
    appointment = db.scalar(select(Appointment).options(joinedload(Appointment.service), joinedload(Appointment.staff_member), joinedload(Appointment.customer)).where(Appointment.id == appointment.id))
    logger.info("appointment_created", extra={"appointment_id": str(appointment.id)})
    return appointment_out(appointment)


@router.get("/appointments/{appointment_id}", response_model=AppointmentOut)
async def get_appointment(appointment_id: uuid.UUID, cancellation_token: uuid.UUID, db: Session = Depends(get_db)):
    appointment = db.scalar(select(Appointment).options(joinedload(Appointment.service), joinedload(Appointment.staff_member), joinedload(Appointment.customer)).where(Appointment.id == appointment_id, Appointment.cancellation_token == cancellation_token))
    if not appointment:
        raise HTTPException(404, "Appointment not found")
    return appointment_out(appointment)


@router.post("/appointments/{appointment_id}/cancel", response_model=AppointmentOut)
async def cancel_appointment(appointment_id: uuid.UUID, payload: CancelInput, db: Session = Depends(get_db), gateway: CalendarGateway = Depends(calendar)):
    appointment = db.scalar(select(Appointment).options(joinedload(Appointment.service), joinedload(Appointment.staff_member), joinedload(Appointment.customer)).where(Appointment.id == appointment_id, Appointment.cancellation_token == payload.cancellation_token))
    if not appointment:
        raise HTTPException(404, "Appointment not found")
    if appointment.status == AppointmentStatus.cancelled:
        return appointment_out(appointment)
    try:
        if appointment.google_event_id:
            gateway.cancel_event(appointment.google_calendar_id, appointment.google_event_id)
        appointment.status = AppointmentStatus.cancelled
        db.commit(); db.refresh(appointment)
    except Exception as error:
        db.rollback(); logger.exception("appointment_cancellation_failed", extra={"appointment_id": str(appointment_id)})
        raise HTTPException(502, "Unable to cancel appointment") from error
    logger.info("appointment_cancelled", extra={"appointment_id": str(appointment_id)})
    return appointment_out(appointment)
