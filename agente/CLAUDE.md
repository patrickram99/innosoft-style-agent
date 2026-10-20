# CLAUDE.md — software del agente (código)

Agente que analiza manuscritos PDF enviados a la revista *Innovación y Software* (OJS 3.1.2.1), detecta incumplimientos
de las normas editoriales y genera sugerencias que un editor aprueba antes de que lleguen al autor.

**Esta carpeta es la raíz del software** (`innosoft-style-agent/` en `specs/00-producto.md` §13). Todos los comandos
de este archivo se ejecutan desde aquí (`cd agente`). El mapa general del repositorio y las reglas comunes están en
`../CLAUDE.md`; el avance, en `../AVANCE.md`.

## Qué leer, y en qué orden

| Archivo | Para qué | Cuándo |
|---|---|---|
| `../AVANCE.md` | Sprint en curso, bloqueos, estado de cada historia y regla. | Siempre, primero. |
| `specs/00-producto.md` | Visión, arquitectura, estados, API canónica (§8.3), modelo de datos (§8.4), estructura (§13) y **decisiones vigentes (§17)**. Prevalece sobre las demás specs. | Antes de tocar contratos, estados o estructura. Léelo por secciones, no entero. |
| `specs/formato-reglas.md` | Contrato de `rules/innosoft/*.yaml`, JSON Schema, marcadores, formato del hallazgo, catálogo de evaluadores. | Al crear o cambiar reglas o evaluadores. |
| `specs/US-nn.md` | Una spec por historia: alcance, entradas, salidas, reglas, excepciones, criterios de aceptación (§8) y plan de pruebas (§9). | Solo la de la historia en curso y las de `depende_de`. |
| `specs/README.md` | Índice de historias. Su columna de estado puede ir atrasada: el estado real es el `estado_spec` de cada spec. | Para ubicar una historia por épica o sprint. |
| `catalogo_requisitos_innosoft.md` | Catálogo original de requisitos y reglas RE-nn (solo lectura). | Si una spec cita una RE-nn que no entiendes. |
| `priorizacion_rice_sprint1.xlsx` | Priorización RICE, calendario de sprints (*Replan 29-sep*), hojas de tareas por sprint. | Al planificar o cerrar tareas. Léelo con openpyxl, no lo describas de memoria. |

**Solo se implementan las historias con `estado_spec: Aprobada`.** Las que están en `Borrador` no se tocan: si el
sprint las necesita, el bloqueo se anota en `../AVANCE.md` y se pide la revisión cruzada.

## Ciclo de trabajo por historia (Spec-Driven Development)

1. Relee la spec completa y lista las tareas antes de escribir código.
2. Implementa lo descrito en las secciones 3 a 7 de la spec, sin agregar alcance.
3. Escribe las pruebas a partir de los criterios de aceptación (§8) y del plan de pruebas (§9). Usa los nombres de
   archivo que indica la spec (`tests/test_us_NN.py`, `tests/rules/test_RE-nn.py`).
4. Ejecuta `pytest`. No avances a otra historia hasta que esté en verde.
5. Haz un commit con el mensaje `US-nn: <título>`. No hagas push salvo que te lo pida.
6. En la spec, cambia `estado_spec` a `Implementada` y marca la casilla **Implementar** de la §13. No modifiques nada
   más de la spec.
7. Actualiza la hoja de tareas del sprint en `priorizacion_rice_sprint1.xlsx` con openpyxl: escribe `Hecho` solo en la
   columna Estado de las tareas terminadas. No toques fórmulas ni otras hojas.
8. Desde la raíz del repositorio ejecuta `python scripts/avance.py` y revisa la sección **Ahora** de `../AVANCE.md`
   (bloqueos y próximos pasos). Si la historia cambia algo que la tesis resume (arquitectura, stack, flujo, plan),
   anótalo en `../Tesis-Doc/README.md` → "Pendiente de reflejar en la tesis"; no edites la tesis desde una tarea de código.

Si dos specs se contradicen, o si una decisión no está resuelta en la spec y cambia el comportamiento, **detente y
pregunta**. No lo resuelvas en silencio.

## Convenciones técnicas

- Estructura según `specs/00-producto.md` §13: `app/`, `rules/`, `tests/`, `prompts/`, `scripts/`, `specs/`, `docs/`,
  `alembic/`. `docs/` guarda las plantillas oficiales de la revista y los diagramas (fuente `.tex` + `.png/.svg`).
- Stack: Python 3.11+, FastAPI, Pydantic v2; SQLAlchemy 2 + Alembic; PyMuPDF (versión fijada en `requirements.txt`),
  PyYAML, jsonschema; Pytest.
- PostgreSQL 16 mediante `docker-compose.yml`. Los modelos usan el tipo JSON de SQLAlchemy con variante JSONB en
  PostgreSQL, para que las pruebas también corran con SQLite y sin Docker.
- Procesamiento asíncrono con `BackgroundTasks` de FastAPI. Celery y Redis llegan más adelante (D-04): no los
  introduzcas sin una spec que lo pida.
- Umbrales, mensajes y reglas activas viven **solo** en YAML (RNF-05). Ningún número de una regla editorial va en el código.
- Cada hallazgo conserva un `rule_id` que existe en `rules/innosoft/*.yaml` (RNF-04).
- Los nombres de endpoints, estados y campos son los de `00-producto.md`. El código va en inglés; los mensajes al
  usuario, en español.
- Las credenciales van en `.env` (no versionado). Versiona solo `.env.example`.
- Entorno de desarrollo **Windows**: los comandos del README y los scripts van en PowerShell (`.ps1`).

## Datos de prueba y privacidad (Ley N.º 29733)

- `muestras/pdf/` y `muestras/docx/` contienen manuscritos reales con posibles datos personales. Esa carpeta está en
  `.gitignore`: nunca copies su contenido a `tests/`, a commits, a logs ni a prompts.
- Las pruebas que dependen de `muestras/` deben saltarse con `pytest.skip` cuando la carpeta no existe.
- Las pruebas determinísticas usan PDFs sintéticos generados con PyMuPDF en `tests/fixtures/` (regenerar con
  `python tests/fixtures/generate_pdfs.py`; el resultado debe ser idéntico al versionado).
- La API acepta **solo PDF** (US-01). Los DOCX sirven como caso negativo (deben devolver `400`) y se pueden convertir a
  PDF con `scripts/convertir_docx.py` (LibreOffice en modo headless). No agregues soporte DOCX a la API sin una spec.

## Qué no tocar

- `catalogo_requisitos_innosoft.md`, `docs/plantillas/`, `docs/diagramas/` (salvo regenerar un diagrama desde su `.tex`).
- Las specs, salvo los cambios del paso 6 del ciclo.
- El Excel, salvo la columna Estado de la hoja de tareas del sprint en curso.
- `../Tesis-Doc/` desde una tarea de código (ver paso 8).

## Pide permiso antes de

- Instalar software del sistema (Docker, LibreOffice, PostgreSQL).
- Hacer push o crear repositorios remotos.
- Modificar archivos fuera de esta carpeta que no sean `../AVANCE.md` o la nota del paso 8.
