from datetime import date as Date, datetime, time as Time, timezone

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from app.config import SERVICES


class AppointmentBase(SQLModel):
    patient_name: str = Field(min_length=3, max_length=80)
    phone: str = Field(description="Celular colombiano, ej: 3001234567")
    service: str
    date: Date
    time: Time

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: str) -> str:
        digits = "".join(c for c in v if c.isdigit())
        if digits.startswith("57") and len(digits) == 12:
            digits = digits[2:]
        if len(digits) != 10 or not digits.startswith("3"):
            raise ValueError("El celular debe tener 10 dígitos y empezar por 3")
        return digits

    @field_validator("service")
    @classmethod
    def check_service(cls, v: str) -> str:
        if v not in SERVICES:
            raise ValueError(f"Servicio no existe. Opciones: {', '.join(SERVICES)}")
        return v


class Appointment(AppointmentBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    status: str = Field(default="confirmada")  # confirmada | cancelada
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentPublic(AppointmentBase):
    id: int
    status: str
