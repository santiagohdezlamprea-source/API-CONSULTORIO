"""Reglas de agenda: que horas existen y cuales estan libres."""
from datetime import date, datetime, time, timedelta

from app.config import OPENING_HOURS, SLOT_MINUTES, TZ


def now_bogota() -> datetime:
    return datetime.now(TZ).replace(tzinfo=None)


def slots_for_day(day: date) -> list[time]:
    """Todas las horas de cita posibles ese dia (sin mirar si estan ocupadas)."""
    hours = OPENING_HOURS[day.weekday()]
    if hours is None:
        return []

    start, end = hours
    current = datetime.combine(day, start)
    last = datetime.combine(day, end) - timedelta(minutes=SLOT_MINUTES)

    slots = []
    while current <= last:
        slots.append(current.time())
        current += timedelta(minutes=SLOT_MINUTES)
    return slots


def check_bookable(day: date, at: time) -> str | None:
    """Devuelve un mensaje de error si no se puede agendar, o None si todo bien."""
    if OPENING_HOURS[day.weekday()] is None:
        return "Ese día el consultorio está cerrado"
    if at not in slots_for_day(day):
        return f"Hora no válida. Las citas son cada {SLOT_MINUTES} min dentro del horario"
    if datetime.combine(day, at) <= now_bogota():
        return "No se puede agendar en el pasado"
    if day > now_bogota().date() + timedelta(days=60):
        return "Solo se agenda con máximo 60 días de anticipación"
    return None
