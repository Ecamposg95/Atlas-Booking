from datetime import date, datetime
import uuid
from zoneinfo import ZoneInfo

from app.database import SessionLocal
from app.models import Service, StaffMember
from app.routers.api import calendar


def service_for(slug: str):
    with SessionLocal() as db:
        staff = db.query(StaffMember).filter_by(slug=slug).one()
        return db.query(Service).filter_by(staff_member_id=staff.id).one(), staff


def test_health(client):
    assert client.get('/api/health').json() == {'status': 'ok'}


def test_list_services(client):
    response = client.get('/api/services')
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_availability_and_outside_rules(client):
    service, _ = service_for('roberto-rodriguez')
    monday = '2026-09-28'
    response = client.get('/api/availability', params={'service_id': str(service.id), 'date': monday})
    assert response.status_code == 200 and len(response.json()['slots']) > 0
    sunday = client.get('/api/availability', params={'service_id': str(service.id), 'date': '2026-09-27'})
    assert sunday.json()['slots'] == []


def test_booking_collision_and_cancellation(client):
    service, staff = service_for('roberto-rodriguez')
    slots = client.get('/api/availability', params={'service_id': str(service.id), 'date': '2026-09-28'}).json()['slots']
    payload = {'staff_member_id': str(staff.id), 'service_id': str(service.id), 'start_at': slots[0]['start_at'], 'timezone': 'America/Mexico_City', 'customer': {'name': 'Ada Lovelace', 'email': 'ada@example.com', 'phone': '5551234567'}}
    created = client.post('/api/appointments', json=payload)
    assert created.status_code == 201
    assert client.post('/api/appointments', json=payload).status_code == 409
    # The cancellation token intentionally is only delivered via private cancellation channels;
    # obtain it from the database in this integration test.
    from app.models import Appointment
    with SessionLocal() as db: token = db.get(Appointment, uuid.UUID(created.json()['id'])).cancellation_token
    cancelled = client.post(f"/api/appointments/{created.json()['id']}/cancel", json={'cancellation_token': str(token)})
    assert cancelled.status_code == 200 and cancelled.json()['status'] == 'cancelled'


def test_google_busy_interval_blocks_slot(client):
    class BusyCalendar:
        def busy_intervals(self, calendar_id, start, end): return [(datetime(2026, 9, 28, 14, tzinfo=ZoneInfo('UTC')), datetime(2026, 9, 28, 16, tzinfo=ZoneInfo('UTC')))]
        def create_event(self, *args): return 'fake-event'
        def cancel_event(self, *args): return None
    async def busy_calendar(): return BusyCalendar()
    client.app.dependency_overrides[calendar] = busy_calendar
    service, _ = service_for('roberto-rodriguez')
    response = client.get('/api/availability', params={'service_id': str(service.id), 'date': '2026-09-28'})
    assert len(response.json()['slots']) < 12
