# API Consultorio Sonrisa Viva 🦷

Backend para agendar citas en un consultorio odontológico. Es la parte "de atrás" de la
[landing del consultorio](https://santiagohdezlamprea-source.github.io/consultorio-odontologico/)
que hice antes: la landing manda a WhatsApp, y esta API es el paso siguiente, guardar las citas
de verdad y no dejar que dos personas tomen la misma hora.

🔗 **Docs en vivo:** https://api-consultorio-qifn.onrender.com/docs  
🔗 **Landing conectada:** https://santiagohdezlamprea-source.github.io/consultorio-odontologico/#agendar

> El servidor gratis de Render se duerme; la primera petición puede tardar unos 50 s.

## Qué hace

| Método | Ruta | Quién | Para qué |
|---|---|---|---|
| GET | `/servicios` | público | Lista de servicios y precios |
| GET | `/disponibilidad?fecha=2026-10-20` | público | Horas libres de un día |
| POST | `/citas` | público | Agendar una cita |
| GET | `/citas?fecha=...` | recepción 🔒 | Ver la agenda del día |
| PATCH | `/citas/{id}/cancelar` | recepción 🔒 | Cancelar y liberar la hora |

Las rutas 🔒 piden el header `X-API-Key`.

### Reglas que valida

- Citas cada 30 min dentro del horario (L-V 7 a. m.–8 p. m., sáb 8 a. m.–2 p. m., domingo cerrado)
- No deja agendar en el pasado ni a más de 60 días
- No deja dos citas a la misma hora (responde `409`)
- El celular tiene que ser colombiano (10 dígitos, empieza por 3). Acepta `300 123 4567` o `+57 3001234567` y lo guarda limpio
- Usa la hora de Bogotá, no la del servidor (el servidor de Render está en UTC, así que sin esto las citas de la noche quedarían en el día equivocado)

## Correrlo en local

```bash
python -m venv venv
venv\Scripts\activate        # en Windows  (en Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Abrir http://127.0.0.1:8000/docs y probar desde ahí.

Ejemplo para agendar:

```bash
curl -X POST http://127.0.0.1:8000/citas \
  -H "Content-Type: application/json" \
  -d '{"patient_name":"María Gómez","phone":"3001234567","service":"limpieza","date":"2026-10-20","time":"10:00"}'
```

## Tests

```bash
pytest
```

Son 11 tests: casos normales, hora repetida, domingo, hora fuera de horario, fecha pasada,
celular inválido, servicio que no existe, disponibilidad y cancelación. Cada test usa una
base de datos en memoria para no ensuciar la real.

## Estructura

```
app/
  main.py        rutas
  models.py      tablas y validaciones (SQLModel + Pydantic)
  scheduling.py  reglas de horario
  config.py      horarios, servicios, variables de entorno
  database.py    conexión a la base de datos
tests/
  test_citas.py
```

## Tecnologías

Python · FastAPI · SQLModel · SQLite · pytest · desplegada en Render

## Pendientes

- [x] Conectar el formulario de la landing a `POST /citas`
- [ ] Pasar de SQLite a PostgreSQL (en Render gratis el SQLite se borra cuando el servicio se reinicia)
- [ ] Recordatorio por WhatsApp un día antes de la cita
