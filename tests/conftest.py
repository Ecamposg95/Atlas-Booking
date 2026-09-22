import os
import asyncio
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///./test_atlas_booking.db"
os.environ["GOOGLE_CALENDAR_MODE"] = "disabled"
os.environ["SEED_DATA"] = "false"

import pytest
import httpx

from app.database import Base, SessionLocal, engine
from app.main import app
from app.routers.api import calendar
from app.services.google_calendar import DisabledCalendarGateway
from app.services.seed import seed


async def disabled_calendar():
    return DisabledCalendarGateway()


@pytest.fixture(autouse=True)
def database():
    Base.metadata.drop_all(engine); Base.metadata.create_all(engine)
    with SessionLocal() as db: seed(db)
    app.dependency_overrides[calendar] = disabled_calendar
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


@pytest.fixture
def client():
    class ApiClient:
        app = app

        def request(self, method, url, **kwargs):
            async def send():
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as http_client:
                    return await http_client.request(method, url, **kwargs)
            return asyncio.run(send())

        def get(self, url, **kwargs): return self.request("GET", url, **kwargs)
        def post(self, url, **kwargs): return self.request("POST", url, **kwargs)
    yield ApiClient()
