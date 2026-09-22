import enum
import uuid
from datetime import datetime, time

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.database import Base


def utcnow() -> datetime:
    return datetime.now().astimezone()


class AppointmentStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"
    no_show = "no_show"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class StaffMember(TimestampMixin, Base):
    __tablename__ = "staff_members"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    calendar_id: Mapped[str | None] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    services: Mapped[list["Service"]] = relationship(back_populates="staff_member")


class Service(TimestampMixin, Base):
    __tablename__ = "services"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    staff_member_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("staff_members.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    buffer_before_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    buffer_after_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3), default="MXN", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    staff_member: Mapped[StaffMember] = relationship(back_populates="services")


class Customer(TimestampMixin, Base):
    __tablename__ = "customers"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class Appointment(TimestampMixin, Base):
    __tablename__ = "appointments"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    staff_member_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("staff_members.id"), index=True, nullable=False)
    service_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("services.id"), index=True, nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id"), index=True, nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(Enum(AppointmentStatus), index=True, default=AppointmentStatus.confirmed, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    google_event_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    google_calendar_id: Mapped[str | None] = mapped_column(String(255))
    cancellation_token: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True, default=uuid.uuid4, nullable=False)
    staff_member: Mapped[StaffMember] = relationship()
    service: Mapped[Service] = relationship()
    customer: Mapped[Customer] = relationship()

    __table_args__ = (Index("ix_appointments_staff_interval", "staff_member_id", "start_at", "end_at"),)


class AvailabilityRule(Base):
    __tablename__ = "availability_rules"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    staff_member_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("staff_members.id"), index=True, nullable=False)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class BlockedPeriod(Base):
    __tablename__ = "blocked_periods"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    staff_member_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("staff_members.id"), index=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
