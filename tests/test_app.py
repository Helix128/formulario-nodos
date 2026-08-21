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
    value = {"name":"Ada Lovelace", "email":"ada@udd.cl", "preference_1":"robotica_educativa", "preference_2":"inventores", "additional_idea":"", "busy_slots":[{"day_id":"lunes","slot_id":"h1"}]}
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


@pytest.mark.parametrize("bad", [payload(email="x@gmail.com"), payload(preference_1="robotica_educativa", preference_2="robotica_educativa"), payload(busy_slots=[{"day_id":"domingo","slot_id":"h1"}])])
def test_api_validation(client, bad):
    assert client.post("/api/responses", json=bad).status_code == 422


<<<<<<< HEAD
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
=======
def test_delete_response(client):
    # Submit initial response
    assert client.post("/api/responses", json=payload()).status_code == 200
    session = client.app.state.session_factory()
    assert session.query(Response).count() == 1
    assert session.query(ResponseSlot).count() == 45

    # Delete response
    res = client.request("DELETE", "/api/responses", json={"email": "ada@udd.cl"})
    assert res.status_code == 200
    assert res.json() == {"ok": True, "deleted": True}

    # Verify cascading deletion in database
    assert session.query(Response).count() == 0
    assert session.query(ResponseSlot).count() == 0

    # Non-existent email returns 404
    res_404 = client.request("DELETE", "/api/responses", json={"email": "ada@udd.cl"})
    assert res_404.status_code == 404

    # Invalid email returns 422
    res_422 = client.request("DELETE", "/api/responses", json={"email": "invalid_email"})
    assert res_422.status_code == 422


def test_catalog_without_level():
    cat = load_catalog(Path("catalog.yml"))
    assert len(cat["nodes"]) >= 3
    for node in cat["nodes"]:
        assert "id" in node
        assert "name" in node
        assert "level" not in node


def test_admin_unauthenticated_redirects_to_login(client):
    res = client.get("/admin", follow_redirects=False)
    assert res.status_code == 303
    assert res.headers["location"] == "/admin/login"

    res_followed = client.get("/admin", follow_redirects=True)
    assert res_followed.status_code == 200
    assert "Ingresa la contraseña del panel" in res_followed.text


def test_admin_auth_and_logout_flow(client):
    bad_login = client.post("/admin/login", data={"password": "wrong-password"})
    assert bad_login.status_code == 401
    assert "Contraseña incorrecta" in bad_login.text

    good_login = client.post("/admin/login", data={"password": "secreta"}, follow_redirects=False)
    assert good_login.status_code == 303
    assert good_login.headers["location"] == "/admin"

    dashboard = client.get("/admin")
    assert dashboard.status_code == 200
    assert "Panel administrativo" in dashboard.text

    login_page = client.get("/admin/login", follow_redirects=False)
    assert login_page.status_code == 303
    assert login_page.headers["location"] == "/admin"

    logout = client.post("/admin/logout", follow_redirects=False)
    assert logout.status_code == 303
    assert logout.headers["location"] == "/admin/login"

    post_logout = client.get("/admin", follow_redirects=False)
    assert post_logout.status_code == 303
    assert post_logout.headers["location"] == "/admin/login"


def test_admin_api_requires_auth(client):
>>>>>>> 9cda9ea (cambios de formulario)
    assert client.get("/api/admin/summary").status_code == 401
    assert client.get("/api/admin/heatmap").status_code == 401
    assert client.get("/api/admin/responses").status_code == 401

    client.post("/admin/login", data={"password": "secreta"})
    assert client.get("/api/admin/summary").status_code == 200
    assert client.get("/api/admin/heatmap").status_code == 200
    assert client.get("/api/admin/responses").status_code == 200

