import os
from pathlib import Path

import pytest
from argon2 import PasswordHasher
from fastapi.testclient import TestClient

os.environ.setdefault("ADMIN_PASSWORD_HASH", PasswordHasher().hash("secreta"))
os.environ.setdefault("SESSION_SECRET", "test-session-secret-is-long-enough")

from app.config import Settings, load_catalog
from app.database import Response, ResponseSlot, make_session_factory
from app.main import create_app


@pytest.fixture
def client(tmp_path):
    settings = Settings(tmp_path / "data.sqlite3", os.environ["ADMIN_PASSWORD_HASH"], os.environ["SESSION_SECRET"], False, Path("catalog.yml"))
    factory, _ = make_session_factory(settings.database_path)
    return TestClient(create_app(settings=settings, catalog=load_catalog(Path("catalog.yml")), session_factory=factory))


def payload(**changes):
    value = {"name":"Ada Lovelace", "email":"ada@udd.cl", "preference_1":"gamedev", "preference_2":"inventores", "additional_idea":"", "busy_slots":[{"day_id":"lunes","slot_id":"h1"}]}
    value.update(changes)
    return value


def test_submission_replacement_and_matrix(client):
    assert client.post("/api/responses", json=payload()).status_code == 200
    assert client.post("/api/responses", json=payload()).status_code == 409
    assert client.post("/api/responses", json=payload(replace_existing=True, name="Ada Byron", busy_slots=[])).json()["replaced"]
    session = client.app.state.session_factory()
    response = session.query(Response).one()
    assert response.name == "Ada Byron" and session.query(ResponseSlot).filter_by(response_id=response.id).count() == 45
    assert not any(slot.busy for slot in response.slots)


@pytest.mark.parametrize("bad", [payload(email="x@gmail.com"), payload(preference_1="gamedev", preference_2="gamedev"), payload(busy_slots=[{"day_id":"domingo","slot_id":"h1"}])])
def test_api_validation(client, bad):
    assert client.post("/api/responses", json=bad).status_code == 422


def test_admin_auth_and_heatmap(client):
    response = client.get("/admin", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"
    assert client.post("/admin/login", data={"password":"wrong"}).status_code == 401
    assert client.post("/admin/login", data={"password":"secreta"}).status_code == 200
    client.post("/api/responses", json=payload())
    data = client.get("/api/admin/heatmap?metric=occupancy").json()
    assert data["total"] == 1
    assert next(c for c in data["cells"] if c["day_id"] == "lunes" and c["slot_id"] == "h1")["percent"] == 100
    assert client.post("/admin/logout").status_code == 200
    assert client.get("/api/admin/summary").status_code == 401
