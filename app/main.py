from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from app.config import ADMIN_KEY, SERVICES
from app.database import create_tables, get_session
from app.models import Appointment, AppointmentCreate, AppointmentPublic
from app.scheduling import check_bookable, now_bogota, slots_for_day


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(
    title="API Consultorio Sonrisa Viva",
    description="Agenda de citas para el consultorio odontológico (proyecto de portafolio).",
    version="1.0.0",
    lifespan=lifespan,
)

# para que la landing en GitHub Pages pueda llamar a la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://santiagohdezlamprea-source.github.io",
        "http://localhost:5500",  # Live Server de VS Code
        "http://127.0.0.1:5500",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_admin(x_api_key: str = Header(default="")):
    if x_api_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Falta la clave de recepción (header X-API-Key)")


@app.get("/", tags=["info"])
def root():
    return {"api": "Consultorio Sonrisa Viva", "docs": "/docs", "hora_bogota": now_bogota().isoformat(timespec="minutes")}


@app.get("/servicios", tags=["público"])
def list_services():
    return [{"id": key, **data} for key, data in SERVICES.items()]


@app.get("/disponibilidad", tags=["público"])
def availability(fecha: date, session: Session = Depends(get_session)):
    """Horas libres de un día. Ej: /disponibilidad?fecha=2026-10-20"""
    taken = session.exec(
        select(Appointment.time).where(Appointment.date == fecha, Appointment.status == "confirmada")
    ).all()

    now = now_bogota()
    free = [
        s.strftime("%H:%M")
        for s in slots_for_day(fecha)
        if s not in taken and (fecha > now.date() or (fecha == now.date() and s > now.time()))
    ]
    return {"fecha": fecha, "libres": free}


@app.post("/citas", response_model=AppointmentPublic, status_code=201, tags=["público"])
def create_appointment(data: AppointmentCreate, session: Session = Depends(get_session)):
    error = check_bookable(data.date, data.time)
    if error:
        raise HTTPException(status_code=400, detail=error)

    already = session.exec(
        select(Appointment).where(
            Appointment.date == data.date,
            Appointment.time == data.time,
            Appointment.status == "confirmada",
        )
    ).first()
    if already:
        raise HTTPException(status_code=409, detail="Esa hora ya está ocupada, escoge otra")

    appt = Appointment.model_validate(data)
    session.add(appt)
    session.commit()
    session.refresh(appt)
    return appt


@app.get("/citas", response_model=list[AppointmentPublic], tags=["recepción"], dependencies=[Depends(require_admin)])
def list_appointments(
    fecha: date | None = Query(default=None, description="Si no se manda, trae las de hoy"),
    session: Session = Depends(get_session),
):
    day = fecha or now_bogota().date()
    query = select(Appointment).where(Appointment.date == day).order_by(Appointment.time)
    return session.exec(query).all()


@app.patch("/citas/{appt_id}/cancelar", response_model=AppointmentPublic, tags=["recepción"], dependencies=[Depends(require_admin)])
def cancel_appointment(appt_id: int, session: Session = Depends(get_session)):
    appt = session.get(Appointment, appt_id)
    if not appt:
        raise HTTPException(status_code=404, detail="No existe esa cita")
    if appt.status == "cancelada":
        raise HTTPException(status_code=400, detail="La cita ya estaba cancelada")

    appt.status = "cancelada"
    session.add(appt)
    session.commit()
    session.refresh(appt)
    return appt
