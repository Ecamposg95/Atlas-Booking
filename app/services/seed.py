from datetime import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AvailabilityRule, Service, StaffMember


def seed(db: Session) -> None:
    if db.scalar(select(StaffMember.id).limit(1)):
        return
    roberto = StaffMember(name="Roberto Rodríguez", slug="roberto-rodriguez", email="rerdzmtz00@gmail.com")
    damian = StaffMember(name="Damián Medina", slug="damian-medina", email="damianmedinaiturbe86@gmail.com")
    db.add_all([roberto, damian]); db.flush()
    for staff in (roberto, damian):
        db.add(Service(staff_member_id=staff.id, name="Consultoría inicial", slug=f"consultoria-inicial-{staff.slug}", description="Sesión inicial personalizada.", duration_minutes=60))
    rules = [(roberto, 0, 9, 13), (roberto, 0, 16, 18), (roberto, 4, 9, 13), (roberto, 4, 16, 18), (damian, 1, 9, 10), (damian, 1, 11, 13), (damian, 3, 9, 10), (damian, 3, 11, 13), (damian, 2, 15, 18), (damian, 4, 9, 11), (damian, 4, 14, 18)]
    for staff, weekday, start, end in rules:
        db.add(AvailabilityRule(staff_member_id=staff.id, weekday=weekday, start_time=time(start), end_time=time(end), timezone="America/Mexico_City"))
    db.commit()
