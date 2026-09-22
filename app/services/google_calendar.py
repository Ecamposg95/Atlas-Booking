import logging
from datetime import datetime
from typing import Protocol

from fastapi import HTTPException

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class CalendarGateway(Protocol):
    def busy_intervals(self, calendar_id: str | None, start: datetime, end: datetime) -> list[tuple[datetime, datetime]]: ...
    def create_event(self, calendar_id: str | None, summary: str, start: datetime, end: datetime, timezone: str, description: str) -> str | None: ...
    def cancel_event(self, calendar_id: str | None, event_id: str) -> None: ...


class DisabledCalendarGateway:
    def busy_intervals(self, calendar_id, start, end):
        return []

    def create_event(self, calendar_id, summary, start, end, timezone, description):
        return None

    def cancel_event(self, calendar_id, event_id):
        return None


class OAuthCalendarGateway:
    def __init__(self, settings: Settings):
        if not all([settings.google_calendar_id, settings.google_client_id, settings.google_client_secret, settings.google_refresh_token]):
            raise RuntimeError("Google Calendar OAuth configuration is incomplete")
        self.settings = settings

    def _service(self):
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        credentials = Credentials(
            token=None,
            refresh_token=self.settings.google_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.settings.google_client_id,
            client_secret=self.settings.google_client_secret,
        )
        return build("calendar", "v3", credentials=credentials, cache_discovery=False)

    def _id(self, calendar_id: str | None) -> str:
        return calendar_id or self.settings.google_calendar_id  # type: ignore[return-value]

    def busy_intervals(self, calendar_id, start, end):
        result = self._service().freebusy().query(body={"timeMin": start.isoformat(), "timeMax": end.isoformat(), "items": [{"id": self._id(calendar_id)}]}).execute()
        return [(datetime.fromisoformat(item["start"].replace("Z", "+00:00")), datetime.fromisoformat(item["end"].replace("Z", "+00:00"))) for item in result["calendars"][self._id(calendar_id)].get("busy", [])]

    def create_event(self, calendar_id, summary, start, end, timezone, description):
        event = self._service().events().insert(calendarId=self._id(calendar_id), body={"summary": summary, "description": description, "start": {"dateTime": start.isoformat(), "timeZone": timezone}, "end": {"dateTime": end.isoformat(), "timeZone": timezone}}).execute()
        return event["id"]

    def cancel_event(self, calendar_id, event_id):
        self._service().events().delete(calendarId=self._id(calendar_id), eventId=event_id).execute()


def get_calendar_gateway(settings: Settings | None = None) -> CalendarGateway:
    settings = settings or get_settings()
    if settings.google_calendar_mode == "disabled":
        if settings.is_production:
            raise RuntimeError("Google Calendar cannot be disabled in production")
        return DisabledCalendarGateway()
    return OAuthCalendarGateway(settings)
