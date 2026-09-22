import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StaffOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    slug: str
    booking_url: str | None = None


class ServiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    staff_member_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    duration_minutes: int
    price: float | None
    currency: str


class SlotOut(BaseModel):
    start_at: datetime
    end_at: datetime


class AvailabilityOut(BaseModel):
    date: date
    timezone: str
    slots: list[SlotOut]


class CustomerInput(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=50)


class AppointmentCreate(BaseModel):
    staff_member_id: uuid.UUID
    service_id: uuid.UUID
    start_at: datetime
    timezone: str = "America/Mexico_City"
    customer: CustomerInput
    notes: str | None = Field(default=None, max_length=2000)


class AppointmentOut(BaseModel):
    id: uuid.UUID
    status: str
    start_at: datetime
    end_at: datetime
    timezone: str
    service: ServiceOut
    staff_member: StaffOut
    customer_name: str


class CancelInput(BaseModel):
    cancellation_token: uuid.UUID
