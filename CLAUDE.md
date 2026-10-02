# CLAUDE.md — Agente de sugerencias estilísticas para Innosoft

Agente que analiza manuscritos PDF enviados a la revista *Innovación y Software* (OJS 3.1.2.1), detecta incumplimientos de las normas editoriales y genera sugerencias que un editor aprueba antes de que lleguen al autor.

## Fuentes de verdad (léelas antes de programar)

| Archivo | Para qué |
|---|---|
| `specs/README.md` | Índice de historias y su estado (`Borrador`, `Aprobada`, `Implementada`, `Verificada`). |
| `specs/00-producto.md` | Visión, arquitectura, estados, API canónica (§8.3), modelo de datos (§8.4), estructura del repo (§13) y **decisiones vigentes (§17)**. Prevalece sobre las demás specs. |
| `specs/formato-reglas.md` | Contrato de `rules/innosoft/*.yaml`, JSON Schema, marcadores, formato del hallazgo y catálogo de evaluadores. |
| `specs/US-nn.md` | Una spec por historia: alcance, entradas, salidas, reglas, excepciones, criterios de aceptación (§8) y plan de pruebas (§9). |
| `catalogo_requisitos_innosoft.md` | Catálogo de requisitos y reglas RE-nn (solo lectura). |

**Solo se implementan las historias con `estado_spec: Aprobada`.** Las que están en `Borrador` no se tocan.

## Ciclo de trabajo por historia (Spec-Driven Development)

1. Relee la spec completa y lista las tareas antes de escribir código.
2. Implementa lo descrito en las secciones 3 a 7 de la spec, sin agregar alcance.
3. Escribe las pruebas a partir de los criterios de aceptación (§8) y del plan de pruebas (§9). Usa los nombres de archivo que indica la spec.
4. Ejecuta `pytest`. No avances a otra historia hasta que esté en verde.
5. Haz un commit con el mensaje `US-nn: <título>`. No hagas push salvo que te lo pida.
6. En la spec, cambia `estado_spec` a `Implementada` y marca la casilla **Implementar** de la §13. No modifiques nada más de la spec.
7. Actualiza la hoja de tareas del sprint en `priorizacion_rice_sprint1.xlsx` con openpyxl: escribe `Hecho` solo en la columna Estado de las tareas terminadas. No toques fórmulas ni otras hojas.

Si dos specs se contradicen, o si una decisión no está resuelta en la spec y cambia el comportamiento, **detente y pregunta**. No lo resuelvas en silencio.

## Convenciones técnicas

- La raíz del repositorio es esta carpeta. La estructura sigue `00-producto.md` §13: `app/`, `rules/`, `tests/`, `prompts/`, `scripts/`, `specs/`, `docs/`.
- Stack:
  - Python 3.11+, FastAPI, Pydantic v2.
  - SQLAlchemy 2 + Alembic para la base de datos.
  - PyMuPDF, PyYAML, jsonschema.
  - Pytest para las pruebas.
- PostgreSQL 16 mediante `docker-compose.yml`. Los modelos usan el tipo JSON de SQLAlchemy con variante JSONB en PostgreSQL, para que las pruebas también corran con SQLite y sin Docker.
- Procesamiento asíncrono con `BackgroundTasks` de FastAPI. Celery y Redis llegan más adelante (D-04): no los introduzcas sin una spec que lo pida.
- Umbrales, mensajes y reglas activas viven **solo** en YAML (RNF-05). Ningún número de una regla editorial va en el código.
- Cada hallazgo conserva un `rule_id` que existe en `rules/innosoft/*.yaml` (RNF-04).
- Los nombres de endpoints, estados y campos son los de `00-producto.md`. El código va en inglés; los mensajes al usuario, en español.
- Las credenciales van en `.env` (no versionado). Versiona solo `.env.example`.
- El entorno de desarrollo es **Windows**: los comandos del README y los scripts de demo van en PowerShell (`.ps1`). Evita scripts que solo funcionen en bash.

## Datos de prueba y privacidad (Ley N.º 29733)

- `muestras/pdf/` y `muestras/docx/` contienen manuscritos reales con posibles datos personales. Esa carpeta está en `.gitignore`: nunca copies su contenido a `tests/`, a commits, a logs ni a prompts.
- Las pruebas que dependen de `muestras/` deben saltarse con `pytest.skip` cuando la carpeta no existe.
- Las pruebas determinísticas usan PDFs sintéticos generados con PyMuPDF en `tests/fixtures/`: figuras de tamaño y DPI conocidos, figuras vectoriales, documentos sin figuras, una página solo imagen como "escaneado" y archivos corruptos.
- La API acepta **solo PDF** (US-01). Los DOCX sirven como caso negativo (deben devolver `400`) y se pueden convertir a PDF con `scripts/convertir_docx.py` (LibreOffice en modo headless) para ampliar el corpus local. No agregues soporte DOCX a la API sin una spec que lo indique.

## Qué no tocar

- `catalogo_requisitos_innosoft.md`, `Plantillas/`, `diagramas/`, `Requisitos_Tesis.pdf`, `informe_avance_innosoft.pdf`.
- Las specs, salvo los cambios del paso 6 del ciclo.
- El Excel, salvo la columna Estado de la hoja de tareas del sprint en curso.

## Pide permiso antes de

- Instalar software del sistema (Docker, LibreOffice, PostgreSQL).
- Hacer push o crear repositorios remotos.
- Modificar archivos fuera de las carpetas del repositorio que indica la §13.
