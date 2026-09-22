# Atlas Booking — Architecture Decisions

## One deployable web service

FastAPI owns `/api/*` and serves the built React single-page application for all non-API routes. Railway builds the frontend before starting Uvicorn, allowing one application service plus Railway PostgreSQL.

## Availability and time

Availability rules are attached to a staff member. User-facing times are interpreted in an explicit IANA timezone, initially `America/Mexico_City`; appointment instants are persisted as timezone-aware UTC timestamps. Slots are the intersection of local working rules and the absence of PostgreSQL appointments, blocked periods, and Google Calendar busy intervals.

## Booking integrity

The API uses a PostgreSQL transaction-scoped advisory lock keyed by staff member and appointment day while rechecking availability. This serializes competing bookings for the same professional/day and prevents the read-then-insert race without rejecting legitimate bookings for other staff or dates.

## Google Calendar

Routers depend only on a calendar service interface. The production adapter uses configured OAuth refresh-token credentials, suitable for unattended server-side operation. In development, explicit `GOOGLE_CALENDAR_MODE=disabled` is permitted; no implicit mock is used in production. Calendar creation happens before the database transaction commits; failure rolls back the pending appointment. If database commit fails after event creation, the service attempts compensating event deletion and logs the result.

## Future readiness

`StaffMember` is introduced now because availability is inherently person-specific. Appointments reference both service and staff. This is the minimal extension needed for later calendar-per-staff, locations, organizations, and multi-tenancy.
