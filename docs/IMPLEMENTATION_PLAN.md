# Atlas Booking — Implementation Plan

## Product decisions confirmed

- Public flow starts at a premium, mobile-first landing page where a visitor chooses a professional.
- Roberto Rodríguez is available Monday and Friday, 09:00–13:00 and 16:00–18:00.
- Damián Medina is available Tuesday and Thursday, 09:00–10:00 and 11:00–13:00; Wednesday, 15:00–18:00; and Friday, 09:00–11:00 and 14:00–18:00.
- The operating timezone is `America/Mexico_City`.
- Each professional has an email address reserved for future notifications and calendar configuration. Calendar credentials and IDs are configured solely through environment variables.

## Delivery phases

1. Bootstrap the monorepo, configuration, FastAPI application, React/Vite application, lint-safe secret handling, and Railway build configuration.
2. Implement PostgreSQL models, Alembic migration, development seed data, and availability rules scoped to staff.
3. Implement the availability engine, calendar adapter, concurrency-safe booking transaction, cancellation flow, and API tests.
4. Build the public booking interface: professional selection, service/date/slot selection, customer details, and confirmation.
5. Run migrations, backend tests, frontend production build, review Git state, and document deployment and remaining integration work.

## Acceptance criteria

The public flow must select a professional, select a service and date, show backend-calculated slots, revalidate availability during booking, create an appointment and calendar event when configured, and display a confirmation. External calendar calls are mocked in tests and never silently mocked in production.
