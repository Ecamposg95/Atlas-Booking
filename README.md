# Atlas Booking

Atlas Booking is a mobile-first booking MVP for selecting a professional, finding real availability, and confirming an appointment. FastAPI serves its API under `/api/*` and the built React application from the same deployable service.

## Architecture

- FastAPI, SQLAlchemy 2, PostgreSQL, Alembic, and Pydantic v2.
- React 18, TypeScript, and Vite.
- Availability combines staff working rules, service duration/buffers, confirmed local appointments, blocked periods, and Google Calendar busy intervals.
- PostgreSQL transaction advisory locks serialize competing bookings for one professional/day. See [architecture decisions](docs/ARCHITECTURE.md).

## Local setup

```bash
cp .env.example .env
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
createdb atlas_booking
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload
cd frontend && npm install && npm run dev
```

The API is at `http://localhost:8000/api`; Vite runs at `http://localhost:5173`. Development seeding creates Roberto Rodríguez and Damián Medina, each with the confirmed business hours and an initial 60-minute consultation.

## Environment

Copy `.env.example`; never commit `.env`, refresh tokens, OAuth downloads, or service account JSON. `GOOGLE_CALENDAR_MODE=disabled` is allowed only outside production. For production set it to `oauth` and provide `GOOGLE_CALENDAR_ID`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REFRESH_TOKEN` through Railway Variables.

## Google Calendar

The public landing uses each consultant's Google Appointment Schedule: choose a consultant, open the modal, then continue to Google Calendar. Configure the public links through `ROBERTO_BOOKING_URL` and `DAMIAN_BOOKING_URL` in Railway Variables. These links are not secrets. The API calendar gateway remains isolated for a future server-to-server integration; tests supply a fake gateway and never call Google.

## Tests and build

```bash
pytest
cd frontend && npm install && npm run build
```

## Railway deployment

Create/link a Railway project, add PostgreSQL, then configure the variables listed in `.env.example`. Set `DATABASE_URL` to `${{Postgres.DATABASE_URL}}`; the application normalizes it for SQLAlchemy's Psycopg driver. The Dockerfile builds React with Node and runs FastAPI with Python in one service. Railway runs migrations and idempotent development seed data as its pre-deploy step; `/api/health` is the health check.

## Current MVP Scope

Premium public consultant selection and a Google Calendar reservation handoff, plus the retained API foundations for a future first-party booking flow.

## Future Roadmap

- Staff and multiple calendars
- Branches
- Organizations / multi-tenancy
- WhatsApp and email
- Payments
- Reminders
- Rescheduling
- Analytics
- Atlas ONE integration
