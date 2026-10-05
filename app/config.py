import os
from datetime import time
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Bogota")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./citas.db")

# clave simple para las rutas de la recepcion. En Render se pone como variable de entorno
ADMIN_KEY = os.getenv("ADMIN_KEY", "dev-key-cambiame")

SLOT_MINUTES = 30

# weekday(): 0 = lunes ... 6 = domingo. None = cerrado
OPENING_HOURS = {
    0: (time(7, 0), time(20, 0)),
    1: (time(7, 0), time(20, 0)),
    2: (time(7, 0), time(20, 0)),
    3: (time(7, 0), time(20, 0)),
    4: (time(7, 0), time(20, 0)),
    5: (time(8, 0), time(14, 0)),
    6: None,
}

# mismos servicios que la landing (precios en COP)
SERVICES = {
    "valoracion": {"name": "Valoración general", "price": 0, "minutes": 30},
    "limpieza": {"name": "Limpieza dental", "price": 90000, "minutes": 30},
    "ortodoncia": {"name": "Ortodoncia (control)", "price": 150000, "minutes": 30},
    "blanqueamiento": {"name": "Blanqueamiento", "price": 450000, "minutes": 60},
    "implantes": {"name": "Implantes (valoración)", "price": 0, "minutes": 30},
    "urgencia": {"name": "Urgencia", "price": 120000, "minutes": 30},
}
