# Formulario NODO

Aplicación FastAPI para registrar disponibilidad y consultar resultados desde un panel protegido.

## Arranque

1. Cree un entorno virtual e instale dependencias: `python -m venv .venv && .venv/bin/pip install -r requirements.txt`.
2. Copie `.env.example` a `.env`. Genere el hash con ` .venv/bin/python scripts/generate_password_hash.py` y defina también `SESSION_SECRET` como un valor largo y aleatorio.
3. Ejecute ` .venv/bin/alembic upgrade head` y luego ` .venv/bin/uvicorn app.main:app --reload`; abra `http://127.0.0.1:8000`.

La carpeta de datos y la base SQLite se crean automáticamente. La app no inicia si faltan secretos o el catálogo es inválido. La migración inicial también queda aplicada de forma segura al crear una base vacía.

## Operación

`catalog.yml` es la única fuente de verdad para Nodos, días y horarios. Los IDs no deben cambiar: se pueden modificar los nombres y etiquetas sin afectar los datos históricos.

Para producción, use `pm2 start ecosystem.config.cjs`. Coloque Gunicorn detrás de un proxy inverso HTTPS, configure `COOKIE_SECURE=true` y asegure que el proxy reenvíe el host y esquema originales. El panel se encuentra en `/admin`.

SQLite usa WAL y claves foráneas. Para un respaldo consistente, use `sqlite3 data/nodos.sqlite3 '.backup backup/nodos-YYYY-MM-DD.sqlite3'` (cree el directorio `backup` antes) o detenga brevemente el proceso antes de copiar la base y sus archivos WAL/SHM.

## Pruebas

Ejecute `pytest`. Las pruebas usan una base temporal y no modifican `data/nodos.sqlite3`.
