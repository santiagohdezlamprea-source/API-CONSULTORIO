from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.config import ADMIN_KEY
from app.database import get_session
from app.main import app


@pytest.fixture
def client():
    # base de datos en memoria, nueva para cada test
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def override():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def next_weekday(weekday: int) -> date:
    """Proximo dia de la semana pedido (0 = lunes), siempre en el futuro."""
    d = date.today() + timedelta(days=1)
    while d.weekday() != weekday:
        d += timedelta(days=1)
    return d


def booking(**changes):
    data = {
        "patient_name": "María Gómez",
        "phone": "300 123 4567",
        "service": "limpieza",
        "date": next_weekday(1).isoformat(),  # martes
        "time": "10:00",
    }
    data.update(changes)
    return data


def test_create_appointment(client):
    r = client.post("/citas", json=booking())
    assert r.status_code == 201
    assert r.json()["phone"] == "3001234567"  # lo limpia
    assert r.json()["status"] == "confirmada"


def test_same_slot_twice_is_rejected(client):
    client.post("/citas", json=booking())
    r = client.post("/citas", json=booking(patient_name="Otra Persona"))
    assert r.status_code == 409


def test_sunday_is_closed(client):
    r = client.post("/citas", json=booking(date=next_weekday(6).isoformat()))
    assert r.status_code == 400
    assert "cerrado" in r.json()["detail"]


def test_time_outside_hours(client):
    r = client.post("/citas", json=booking(time="21:00"))
    assert r.status_code == 400


def test_odd_minutes_not_allowed(client):
    r = client.post("/citas", json=booking(time="10:15"))
    assert r.status_code == 400


def test_past_date(client):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    r = client.post("/citas", json=booking(date=yesterday))
    assert r.status_code == 400


def test_bad_phone(client):
    r = client.post("/citas", json=booking(phone="12345"))
    assert r.status_code == 422


def test_unknown_service(client):
    r = client.post("/citas", json=booking(service="cirugia"))
    assert r.status_code == 422


def test_availability_hides_taken_slot(client):
    day = next_weekday(1).isoformat()
    before = client.get("/disponibilidad", params={"fecha": day}).json()["libres"]
    client.post("/citas", json=booking(time="10:00"))
    after = client.get("/disponibilidad", params={"fecha": day}).json()["libres"]

    assert "10:00" in before
    assert "10:00" not in after
    assert len(after) == len(before) - 1


def test_admin_routes_need_key(client):
    assert client.get("/citas").status_code == 401


def test_cancel_frees_the_slot(client):
    appt = client.post("/citas", json=booking()).json()
    headers = {"X-API-Key": ADMIN_KEY}

    r = client.patch(f"/citas/{appt['id']}/cancelar", headers=headers)
    assert r.json()["status"] == "cancelada"

    # ahora otra persona puede tomar esa hora
    r = client.post("/citas", json=booking(patient_name="Juan Pérez"))
    assert r.status_code == 201
