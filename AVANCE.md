# Avance del proyecto — fuente única

Tesis: *Agente de IA de sugerencias estilísticas integrado con OJS* (caso Innosoft). Este archivo es el primer lugar donde
mirar el estado del proyecto, tanto del software como del documento de tesis.

- **Secciones manuales** (arriba): foco actual, bloqueos y próximos pasos. Se editan a mano en cada Sprint Review.
- **Bloque automático** (abajo): se regenera con `python scripts/avance.py` (desde la raíz) a partir de `agente/`
  (specs, código, pruebas, reglas YAML, Excel RICE) y de `Tesis-Doc/` (cabecera y marcas `\pendiente` de cada `.tex`).
  No lo edites a mano.

| Si buscas… | Ve a |
|---|---|
| Qué es el producto y cómo funciona | [`agente/specs/00-producto.md`](agente/specs/00-producto.md) |
| Qué hace una historia concreta | `agente/specs/US-nn.md` (índice en el bloque automático) |
| Cómo se escriben las reglas editoriales | [`agente/specs/formato-reglas.md`](agente/specs/formato-reglas.md) |
| Requisitos y reglas RE-nn originales | [`agente/catalogo_requisitos_innosoft.md`](agente/catalogo_requisitos_innosoft.md) |
| Prioridades RICE y tareas del sprint | `agente/priorizacion_rice_sprint1.xlsx` |
| El documento de tesis (LaTeX, se compila en local con MiKTeX) | [`Tesis-Doc/README.md`](Tesis-Doc/README.md) |
| Decisiones vigentes y preguntas abiertas | [`agente/specs/00-producto.md` §17–§18](agente/specs/00-producto.md) · [registro de sincronización de la tesis](Tesis-Doc/README.md#registro-de-sincronización) |
| Informes del revisor multiagente de specs | `agente/specs/revisiones/US-nn.md` · [`agente/tools/spec_review/README.md`](agente/tools/spec_review/README.md) |
| Cómo trabaja Claude en cada parte | `CLAUDE.md` (mapa) · `agente/CLAUDE.md` (código) · `Tesis-Doc/CLAUDE.md` (tesis) |

## Ahora (actualizado 10-nov-2026)

**Sprint 5 (09-nov → 20-nov), día 2 de 10.** El 10-nov se decidió entregar en dos fases (D-05 de `00-producto.md` v1.1):

- **Fase 1, hasta el 04-dic-2026 (cierre de Tesis II):** agente *headless*. Entra un PDF por la API y salen hallazgos y
  sugerencias con Gemini por la API. Sin plugin de OJS ni interfaz de editor.
- **Fase 2, del 04-ene al 26-mar-2027 (Sprints 7-12):** plugin de OJS, revisión del editor, publicación, pruebas de
  integración y evaluación con editores.

El plan está en la hoja *Replan 10-nov* del Excel RICE y en el Capítulo III. Es una propuesta: falta validarla con el asesor.

**Resumen del avance**

- **Software:** sin historias nuevas desde el Sprint 2. Hay 6 de 37 implementadas, 89 de 89 casos en verde en local (84
  del producto y 5 de la herramienta de revisión) y 96 % de cobertura de líneas. Ninguna historia está verificada.
- **Sprints 3 y 4:** no cumplieron su meta. Sus historias pasan a los Sprints 5 y 6.
- **Revisor multiagente de specs** (`agente/tools/spec_review/`, D-07): Google ADK sobre Gemini en Vertex AI, con tres
  revisores y un coordinador. Una spec con veredicto favorable pasa a `Revisada (IA)` y se puede implementar; el equipo
  la ratifica después.
- **Primera revisión (10-nov):** US-05, US-07 y US-08 salieron **bloqueantes**. Informes en `agente/specs/revisiones/`.
- **Google Cloud:** proyecto `gen-lang-client-0866871931`, Vertex AI habilitado, credenciales locales con `gcloud`.
  Alerta de presupuesto de S/ 35 al mes (≈ 10 USD) al 50, 90 y 100 %; la alerta avisa, no corta el gasto.
- **Tesis:** el Capítulo III tiene el plan en dos fases, la revisión multiagente y 14 capturas de las pruebas
  (`Tesis-Doc/figuras/pruebas/`). Capítulo II y resumen ajustados. Compila sin errores (91 páginas).

**Bloqueos**

- US-05, US-07 y US-08 no se pueden implementar hasta corregir sus observaciones bloqueantes. Varias son decisiones de
  alcance (qué secciones detecta US-05 en R1, qué campos extrae US-08), no de redacción.
- Las otras 28 specs siguen en `Borrador` y aún no pasaron por el revisor.
- Sin acceso al servidor de OJS. Ya no bloquea la Fase 1; hay que resolverlo antes del 04-ene-2027.
- La hoja de tareas del Sprint 5 aún no existe en el Excel RICE.
- D-05, D-06 y D-07 están pendientes de ratificar por el otro developer y de validar con el asesor.
- **CI desactivado (D-08).** GitHub no ejecuta Actions por un bloqueo de facturación de la cuenta sin causa visible. El
  flujo quedó desactivado el 10-nov; las historias se cierran con el `pytest` del ciclo SDD y se asume que pasarían en
  Actions. Falta pedir a GitHub Support que quite el bloqueo y reactivar con `gh workflow enable ci.yml`.
- Sin cerrar: *stakeholder* editorial, corpus anotado y hosting (00-producto §18).

**Próximos pasos**

1. Decidir las observaciones bloqueantes de US-05, US-07 y US-08, corregir las specs y volver a revisarlas.
2. Pasar por el revisor US-03, US-11, US-12 y US-13, e implementar las que queden en `Revisada (IA)`.
3. Integrar la rama `tesis/avance-30-oct` a `main` y agregar los casos de borde exacto de RE-20, RE-21 y US-01.
4. Sprint 6: revisar e implementar US-15 a US-18, US-20 y US-28 (sugerencias con Gemini por la API).
5. Validar con el asesor el plan en dos fases y el calendario de 2027.

<!-- AUTO:INICIO (generado por scripts/avance.py; no editar a mano) -->

_Generado el 2026-11-10._

### Tablero

| Indicador | Valor |
|---|---|
| Sprint en curso | **Sprint 5** (09-nov → 20-nov): Agente headless: citas y referencias IEEE detectadas por API; specs revisadas por el sistema multiagente |
| Historias implementadas | 6 / 37 — US-00, US-01, US-04, US-06, US-09, US-10 |
| Historias en borrador | 31 / 37 |
| Walking skeleton ★ | 5 / 17 implementadas |
| Reglas con evaluador | 2 de 8 declaradas en YAML · 44 en el catálogo — RE-20, RE-21 |
| Endpoints canónicos (§8.3) | 4 / 13 — `POST /manuscripts`, `GET /manuscripts/{id}/findings`, `GET /rules`, `GET /health` |
| Funciones de prueba | 85 en `tests/` |
| Tesis: archivos revisados | 0 / 9 · marcas \pendiente abiertas: 13 |

### Sprint 5 — historias comprometidas

| ID | Historia | Estado spec | Fase SDD |
|---|---|---|---|
| [US-03](agente/specs/US-03.md) | Obtener metadatos del envío (sección, título, idioma) | Borrador | Especificar |
| [US-05](agente/specs/US-05.md) | Detectar secciones IMRyD | Borrador | Especificar |
| [US-07](agente/specs/US-07.md) | Extraer citas en texto [n] | Borrador | Especificar |
| [US-08](agente/specs/US-08.md) | Extraer lista de referencias | Borrador | Especificar |
| [US-11](agente/specs/US-11.md) | Validar figuras: pie, numeración y orden | Borrador | Especificar |
| [US-12](agente/specs/US-12.md) | Validar citas IEEE en el texto | Borrador | Especificar |
| [US-13](agente/specs/US-13.md) | Validar referencias IEEE (formato, orden y mínimo) | Borrador | Especificar |

### Historias

| ID | Historia | Ép. | Rel. | Sprint | ★ | Estado spec | Fase SDD | Pruebas | Commits |
|---|---|---|---|---|---|---|---|---|---|
| [US-00](agente/specs/US-00.md) | Especificación general del producto y configuración del entorno | T | R1 | 2 |  | Implementada | Implementar | 6 | 1 |
| [US-01](agente/specs/US-01.md) | Recibir PDF por API | A | R1 | 2 | ★ | Implementada | Implementar | 11 | 1 |
| [US-02](agente/specs/US-02.md) | Plugin OJS: hook al completar un envío | A | R1 | 7 |  | Borrador | Especificar |  |  |
| [US-03](agente/specs/US-03.md) | Obtener metadatos del envío (sección, título, idioma) | A | R1 | 5 |  | Borrador | Especificar |  |  |
| [US-04](agente/specs/US-04.md) | Extraer texto y páginas | B | R1 | 2 | ★ | Implementada | Implementar | 11 | 1 |
| [US-05](agente/specs/US-05.md) | Detectar secciones IMRyD | B | R1 | 5 | ★ | Borrador | Especificar |  |  |
| [US-06](agente/specs/US-06.md) | Extraer figuras: posición, tamaño y pie | B | R1 | 2 | ★ | Implementada | Implementar | 13 | 1 |
| [US-07](agente/specs/US-07.md) | Extraer citas en texto [n] | B | R1 | 5 | ★ | Borrador | Especificar |  |  |
| [US-08](agente/specs/US-08.md) | Extraer lista de referencias | B | R1 | 5 | ★ | Borrador | Especificar |  |  |
| [US-09](agente/specs/US-09.md) | Cargar reglas Innosoft desde YAML | C | R1 | 2 | ★ | Implementada | Implementar | 15 | 1 |
| [US-10](agente/specs/US-10.md) | Validar figuras: tamaño y proporción | C | R1 | 2 | ★ | Implementada | Implementar | 14 | 2 |
| [US-11](agente/specs/US-11.md) | Validar figuras: pie, numeración y orden | C | R1 | 5 |  | Borrador | Especificar |  |  |
| [US-12](agente/specs/US-12.md) | Validar citas IEEE en el texto | C | R1 | 5 | ★ | Borrador | Especificar |  |  |
| [US-13](agente/specs/US-13.md) | Validar referencias IEEE (formato, orden y mínimo) | C | R1 | 5 | ★ | Borrador | Especificar |  |  |
| [US-14](agente/specs/US-14.md) | Validar estructura, resumen y palabras clave | C | R2 | — |  | Borrador | Especificar |  |  |
| [US-15](agente/specs/US-15.md) | Redactar sugerencia con Gemini | D | R1 | 6 | ★ | Borrador | Especificar |  |  |
| [US-16](agente/specs/US-16.md) | Validar el esquema de respuesta del LLM | D | R1 | 6 | ★ | Borrador | Especificar |  |  |
| [US-17](agente/specs/US-17.md) | Anonimizar el contexto antes de enviarlo al LLM | D | R1 | 6 |  | Borrador | Especificar |  |  |
| [US-18](agente/specs/US-18.md) | Reintentos, límite de tokens y fallback determinístico | D | R1 | 6 |  | Borrador | Especificar |  |  |
| [US-19](agente/specs/US-19.md) | Ver cola de manuscritos pendientes | E | R1 | 8 | ★ | Borrador | Especificar |  |  |
| [US-20](agente/specs/US-20.md) | Ver sugerencias con su evidencia | E | R1 | 6 | ★ | Borrador | Especificar |  |  |
| [US-21](agente/specs/US-21.md) | Aceptar, rechazar o editar cada sugerencia | E | R1 | 8 | ★ | Borrador | Especificar |  |  |
| [US-22](agente/specs/US-22.md) | Agregar una sugerencia manual | E | R2 | — |  | Borrador | Especificar |  |  |
| [US-23](agente/specs/US-23.md) | Marcar manuscrito como "sin observaciones" | E | R2 | — |  | Borrador | Especificar |  |  |
| [US-24](agente/specs/US-24.md) | Publicar comentario en la discusión del envío | F | R1 | 9 | ★ | Borrador | Especificar |  |  |
| [US-25](agente/specs/US-25.md) | Reintento y cola si OJS no responde | F | R2 | — |  | Borrador | Especificar |  |  |
| [US-26](agente/specs/US-26.md) | Vincular el comentario a la versión del manuscrito | F | R2 | — |  | Borrador | Especificar |  |  |
| [US-27](agente/specs/US-27.md) | Notificar al editor por correo de OJS | F | R2 | — |  | Borrador | Especificar |  |  |
| [US-28](agente/specs/US-28.md) | Registro de ejecución por manuscrito | G | R1 | 6 | ★ | Borrador | Especificar |  |  |
| [US-29](agente/specs/US-29.md) | Registro de consumo y latencia de Gemini | G | R2 | — |  | Borrador | Especificar |  |  |
| [US-30](agente/specs/US-30.md) | Editar reglas sin redespliegue | G | R2 | — |  | Borrador | Especificar |  |  |
| [US-31](agente/specs/US-31.md) | Detectar reenvío (versión 2 del manuscrito) | A | R2 | — |  | Borrador | Especificar |  |  |
| [US-32](agente/specs/US-32.md) | Panel de métricas | G | R3 | — |  | Borrador | Especificar |  |  |
| [US-33](agente/specs/US-33.md) | Auditoría de decisiones editoriales | G | R3 | — |  | Borrador | Especificar |  |  |
| [US-34](agente/specs/US-34.md) | Detectar tablas y sus títulos | B | R3 | — |  | Borrador | Especificar |  |  |
| [US-35](agente/specs/US-35.md) | Detectar figuras recortadas o fuera de margen | B | R3 | — |  | Borrador | Especificar |  |  |
| [US-36](agente/specs/US-36.md) | Validar formato de página (fuente, márgenes, numeración) | C | R3 | — |  | Borrador | Especificar |  |  |

### Reglas declaradas en YAML

| Regla | Archivo | Descripción | Evaluador | Implementada | Pruebas |
|---|---|---|---|---|---|
| RE-20 | `figuras.yaml` | Imagen de al menos 531 × 1328 px (alto × ancho), o proporción 200 × 500 si es panorámica | `figure_min_pixels` | sí | 4 |
| RE-21 | `figuras.yaml` | Resolución efectiva de la imagen ≥ 300 dpi | `figure_min_dpi` | sí | 4 |
| RE-22 | `figuras.yaml` | Figura contenida en los márgenes de página (no recortada, no desbordada); en LaTeX ancho de referencia 0,9\textwidth | `figure_within_margins` | no |  |
| RE-23 | `figuras.yaml` | Pie de figura debajo, centrado, Times New Roman 10 pt, con el formato "Figura n. Título" | `figure_caption_format` | no |  |
| RE-24 | `figuras.yaml` | Numeración secuencial de figuras por orden de aparición | `figure_numbering_sequence` | no |  |
| RE-25 | `figuras.yaml` | Toda figura referenciada en el texto como "Figura n" (no "figura de abajo" ni "la siguiente imagen") | `figure_referenced_in_text` | no |  |
| RE-26 | `figuras.yaml` | Texto interno de la figura legible y en el idioma del artículo; fuentes Times, Arial, Courier o Symbol | `llm_figure_text_legibility` | no |  |
| RE-27 | `figuras.yaml` | Formato preferido vectorial (SVG o EPS); aceptables TIFF y PNG | `figure_format_notice` | no |  |

### Calendario de sprints (fuente: Excel RICE, hoja *Replan 10-nov*)

| Sprint | Fechas | Historias | Meta |
|---|---|---|---|
| 2 | 29-sep → 09-oct | US-00, US-01, US-04, US-09, US-06, US-10 | Walking skeleton con RE-20/RE-21 (cumplido) |
| 3 | 12-oct → 23-oct | Sin historias cerradas (specs en borrador, sin acceso a OJS) | No cumplió su meta; sus historias pasan al Sprint 5 |
| 4 | 26-oct → 06-nov | Sin historias cerradas: diseño de pruebas (58 casos) y avance de tesis | No cumplió su meta; sus historias pasan al Sprint 6 |
| 5 ◀ en curso | 09-nov → 20-nov | US-03, US-05*, US-07, US-08*, US-11*, US-12, US-13* | Agente headless: citas y referencias IEEE detectadas por API; specs revisadas por el sistema multiagente |
| 6 | 23-nov → 04-dic | US-17, US-15, US-16, US-18*, US-28, US-20 | Agente headless: sugerencias con Gemini consultables por API; evaluación preliminar y entrega de Tesis II |
| 7 | 04-ene → 15-ene | US-02 + spike OJS | Instancia de OJS de prueba y plugin que entrega el envío al agente |
| 8 | 18-ene → 29-ene | US-19, US-21 | Cola de revisión y decisiones del editor |
| 9 | 01-feb → 12-feb | US-24 | Flujo completo: OJS → agente → editor → comentario en OJS |
| 10 | 15-feb → 26-feb | Sin historias nuevas | Pruebas de integración con OJS (4 casos) y con editor (2 casos) |
| 11 | 01-mar → 12-mar | Sin historias nuevas | Evaluación con editores: precisión, recall, F1 y tasa de aceptación |
| 12 | 15-mar → 26-mar | Sin historias nuevas | Buffer, manuales y versión final de la tesis |

### Tesis (Tesis-Doc/)

| Parte | Archivo | Estado | Actualizado | \pendiente |
|---|---|---|---|---|
| Preliminares (dedicatoria, siglas, resumen, abstract) | [Tesis-Doc/capitulos/00-preliminares.tex](Tesis-Doc/capitulos/00-preliminares.tex) | borrador | 2026-11-10 | 4 |
| Capítulo I – Problemática del proyecto | [Tesis-Doc/capitulos/01-problematica.tex](Tesis-Doc/capitulos/01-problematica.tex) | borrador | 2026-10-19 |  |
| Capítulo II – Planteamiento del proyecto | [Tesis-Doc/capitulos/02-planteamiento.tex](Tesis-Doc/capitulos/02-planteamiento.tex) | borrador | 2026-11-10 | 2 |
| Capítulo III – Metodología de desarrollo | [Tesis-Doc/capitulos/03-metodologia.tex](Tesis-Doc/capitulos/03-metodologia.tex) | borrador | 2026-11-10 | 4 |
| Conclusiones | [Tesis-Doc/capitulos/04-conclusiones.tex](Tesis-Doc/capitulos/04-conclusiones.tex) | pendiente | 2026-10-19 | 1 |
| Referencias | [Tesis-Doc/capitulos/referencias.tex](Tesis-Doc/capitulos/referencias.tex) | borrador | 2026-10-30 |  |
| Anexo A – Ficha de búsqueda | [Tesis-Doc/anexos/A-ficha-busqueda.tex](Tesis-Doc/anexos/A-ficha-busqueda.tex) | borrador | 2026-10-19 | 2 |
| Anexo A – Fichas de lectura crítica | [Tesis-Doc/anexos/fichas-lectura.tex](Tesis-Doc/anexos/fichas-lectura.tex) | no incluido | 2026-10-19 |  |
| Anexo B – Matriz de trazabilidad | [Tesis-Doc/anexos/matriz-trazabilidad.tex](Tesis-Doc/anexos/matriz-trazabilidad.tex) | borrador | 2026-10-19 |  |

<!-- AUTO:FIN -->
