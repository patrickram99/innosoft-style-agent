# innosoft-style-agent

Agente de sugerencias estilísticas para la revista *Innovación y Software* (Innosoft, OJS 3.1.2.1).
Recibe manuscritos en PDF, extrae texto y figuras, aplica las reglas editoriales de `rules/innosoft/*.yaml`
y expone los hallazgos para que un editor los revise.

Fuentes de verdad: [`specs/00-producto.md`](specs/00-producto.md), [`specs/formato-reglas.md`](specs/formato-reglas.md)
y una spec por historia en `specs/US-nn.md`. El índice está en [`specs/README.md`](specs/README.md).

## Stack

| Capa | Tecnología |
|---|---|
| Lenguaje | Python 3.11+ (desarrollo local en 3.14; CI y Docker en 3.12) |
| API | FastAPI + Uvicorn, Pydantic v2 |
| Persistencia | PostgreSQL 16 (JSONB) con SQLAlchemy 2 y Alembic; SQLite en las pruebas |
| Extracción PDF | **PyMuPDF 1.28.0** (fijada en `requirements.txt`: la extracción de figuras depende de la versión) |
| Reglas | YAML + JSON Schema (`jsonschema`) |
| Asíncrono | `BackgroundTasks` de FastAPI (Celery + Redis llegan después, decisión D-04) |
| Pruebas | Pytest + GitHub Actions |

## Arranque local (Windows / PowerShell)

```powershell
.\scripts\dev.ps1
```

Crea `.venv`, instala dependencias, genera el corpus sintético y ejecuta `pytest`. Para solo preparar el entorno:

```powershell
.\scripts\dev.ps1 -SinTests
```

Levantar la API en desarrollo (SQLite por defecto si no hay `.env`):

```powershell
uvicorn app.main:app --reload --port 8000
```

Comprobar: `GET http://localhost:8000/health` → `{"status":"ok"}`. La documentación OpenAPI está en `/docs`.

## Arranque con Docker Compose

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Levanta `db` (PostgreSQL 16) y `api` (FastAPI en `:8000`). El contenedor `api` ejecuta `alembic upgrade head`
antes de arrancar. Variables en `.env.example`.

## Pruebas

```powershell
pytest
```

Las pruebas usan SQLite y los PDFs sintéticos de `tests/fixtures/pdfs/` (ver su [README](tests/fixtures/pdfs/README.md)).
Las que dependen de `muestras/` se saltan si la carpeta no existe.

Regenerar el corpus sintético:

```powershell
python tests/fixtures/generate_pdfs.py
```

## Demo (Sprint Review)

```powershell
.\scripts\demo.ps1
```

Levanta la API con SQLite local, sube `tests/fixtures/pdfs/figuras_baja_dpi.pdf`, espera el análisis e imprime
los hallazgos RE-20 y RE-21. Acepta `-Pdf <ruta>`, `-Port <n>` y `-NoStart` (contra una API ya levantada).

## Migraciones

```powershell
alembic revision --autogenerate -m "descripcion"
alembic upgrade head
```

`alembic/env.py` toma la URL de `DATABASE_URL`.

## Datos de muestra (privados)

`muestras/` contiene manuscritos reales y está en `.gitignore` (Ley N.º 29733). La API solo acepta PDF; los DOCX
se convierten con Word o LibreOffice:

```powershell
python scripts/convertir_docx.py
```

Deja los PDF en `muestras/pdf/`.

## Estructura

```text
app/            api, extraction, models, rules/evaluators, suggestion, review, ojs, workers
rules/          innosoft/*.yaml (reglas), schema/rule.schema.json
prompts/        plantillas de prompt versionadas
specs/          especificaciones (SDD)
tests/          test_us_NN.py, rules/test_RE-nn.py, fixtures/pdfs/
docs/           plantillas oficiales (Word, LaTeX, innosoft.cls) y diagramas
scripts/        dev.ps1, demo.ps1, convertir_docx.py
alembic/        migraciones
```
