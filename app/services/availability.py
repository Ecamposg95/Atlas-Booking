from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models import Appointment, AppointmentStatus, AvailabilityRule, BlockedPeriod, Service
from app.services.google_calendar import CalendarGateway


UTC = ZoneInfo("UTC")


def as_utc(value: datetime) -> datetime:
    """Normalize DB datetimes; SQLite test storage drops tzinfo while PostgreSQL does not."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def overlaps(start: datetime, end: datetime, intervals: list[tuple[datetime, datetime]]) -> bool:
    return any(start < interval_end and end > interval_start for interval_start, interval_end in intervals)


def available_slots(db: Session, service: Service, requested_date: date, timezone: str, calendar: CalendarGateway) -> list[tuple[datetime, datetime]]:
    zone = ZoneInfo(timezone)
    rules = db.scalars(select(AvailabilityRule).where(AvailabilityRule.staff_member_id == service.staff_member_id, AvailabilityRule.weekday == requested_date.weekday(), AvailabilityRule.active.is_(True))).all()
    if not rules:
        return []
    day_start = datetime.combine(requested_date, time.min, tzinfo=zone).astimezone(ZoneInfo("UTC"))
    day_end = day_start + timedelta(days=1)
    appointments = db.scalars(select(Appointment).where(Appointment.staff_member_id == service.staff_member_id, Appointment.status.in_([AppointmentStatus.pending, AppointmentStatus.confirmed]), Appointment.start_at < day_end, Appointment.end_at > day_start)).all()
    blocked = db.scalars(select(BlockedPeriod).where(BlockedPeriod.start_at < day_end, BlockedPeriod.end_at > day_start, or_(BlockedPeriod.staff_member_id.is_(None), BlockedPeriod.staff_member_id == service.staff_member_id))).all()
    busy = [(as_utc(a.start_at) - timedelta(minutes=service.buffer_before_minutes), as_utc(a.end_at) + timedelta(minutes=service.buffer_after_minutes)) for a in appointments]
    busy += [(as_utc(b.start_at), as_utc(b.end_at)) for b in blocked]
    busy += calendar.busy_intervals(service.staff_member.calendar_id, day_start, day_end)
    slots: list[tuple[datetime, datetime]] = []
    total = timedelta(minutes=service.duration_minutes)
    before, after = timedelta(minutes=service.buffer_before_minutes), timedelta(minutes=service.buffer_after_minutes)
    interval = timedelta(minutes=30)
    for rule in rules:
        cursor = datetime.combine(requested_date, rule.start_time, tzinfo=zone)
        rule_end = datetime.combine(requested_date, rule.end_time, tzinfo=zone)
        while cursor + total <= rule_end:
            start, end = cursor.astimezone(ZoneInfo("UTC")), (cursor + total).astimezone(ZoneInfo("UTC"))
            if not overlaps(start - before, end + after, busy):
                slots.append((start, end))
            cursor += interval
    return slots
