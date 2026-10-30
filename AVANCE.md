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
| Cómo trabaja Claude en cada parte | `CLAUDE.md` (mapa) · `agente/CLAUDE.md` (código) · `Tesis-Doc/CLAUDE.md` (tesis) |

## Ahora (actualizado 30-oct-2026)

**Sprint 4 (26-oct → 06-nov), día 5 de 10.** El plan se ajustó porque no hay acceso al servidor de OJS. El plan ajustado es
una propuesta: está en el Capítulo III de la tesis y falta validarlo con el asesor y pasarlo al Excel RICE.

**Resumen del avance**

- **Software:** sin cambios desde el Sprint 2. Hay 6 de 37 historias implementadas, 84 de 84 casos en verde en local y 96 %
  de cobertura de líneas del código existente. Ninguna historia está verificada.
- **Sprint 3:** no cumplió su meta. Sus 7 historias no se implementaron porque las specs siguen en `Borrador`, y el *spike*
  de OJS no se hizo por falta de acceso.
- **Tesis:** el Capítulo III tiene ahora un corte de avance fechado y una sección nueva de diseño de pruebas. El Capítulo II
  ya no afirma que haya acceso a OJS. Se añadieron resumen, abstract y 7 referencias.
- **Diseño de pruebas:** cubre niveles, técnicas, corpus, dobles de prueba y 58 casos para las 17 historias R1 pendientes:
  52 se ejecutan en local, 4 requieren OJS y 2 requieren un editor.

**Bloqueos**

- Sin acceso al servidor de OJS: el *spike*, US-02 y la publicación real de US-24 quedan a la espera. El resto se hace en
  local, con un doble de `OjsGateway`.
- Las 31 specs restantes siguen en `Borrador`. Según el ciclo SDD no se pueden implementar hasta que el otro developer las
  revise y pasen a `Aprobada`.
- CI en rojo: el trabajo `avance` falla aunque se regenere este archivo. `--check` cuenta commits y `actions/checkout` clona
  con profundidad 1; además, el bloque automático cambia solo al pasar de sprint.
- La instancia de OJS de prueba que prevé US-02 T-01 usa Docker, que no está instalado.
- La hoja de tareas del Sprint 3 aún no existe en el Excel RICE.
- Sin cerrar: *stakeholder* editorial, corpus anotado, hosting y presupuesto de Gemini (00-producto §18).

**Próximos pasos**

1. Revisión cruzada y aprobación de las specs (empezar por US-05, US-07 y US-08, de las que dependen US-12 y US-13).
2. Corregir el trabajo `avance` del CI y agregar los casos de borde exacto de RE-20, RE-21 y US-01 para pasar US-00..US-10 a
   `Verificada`.
3. Implementar en el Sprint 4 las historias locales de citas y referencias, ampliando el corpus sintético.
4. Validar con el asesor el plan ajustado y la sincronización S-01..S-15, y pasar el plan al Excel RICE.
5. Gestionar el acceso al servidor de OJS. Si no llega antes del Sprint 6, la integración real queda como limitación declarada.

<!-- AUTO:INICIO (generado por scripts/avance.py; no editar a mano) -->

_Generado el 2026-10-30._

### Tablero

| Indicador | Valor |
|---|---|
| Sprint en curso | **Sprint 4** (26-oct → 06-nov): Sugerencias con Gemini anonimizadas y visibles para el editor |
| Historias implementadas | 6 / 37 — US-00, US-01, US-04, US-06, US-09, US-10 |
| Historias en borrador | 31 / 37 |
| Walking skeleton ★ | 5 / 17 implementadas |
| Reglas con evaluador | 2 de 8 declaradas en YAML · 44 en el catálogo — RE-20, RE-21 |
| Endpoints canónicos (§8.3) | 4 / 13 — `POST /manuscripts`, `GET /manuscripts/{id}/findings`, `GET /rules`, `GET /health` |
| Funciones de prueba | 80 en `tests/` |
| Tesis: archivos revisados | 0 / 9 · marcas \pendiente abiertas: 12 |

### Sprint 4 — historias comprometidas

| ID | Historia | Estado spec | Fase SDD |
|---|---|---|---|
| [US-15](agente/specs/US-15.md) | Redactar sugerencia con Gemini | Borrador | Especificar |
| [US-16](agente/specs/US-16.md) | Validar el esquema de respuesta del LLM | Borrador | Especificar |
| [US-17](agente/specs/US-17.md) | Anonimizar el contexto antes de enviarlo al LLM | Borrador | Especificar |
| [US-18](agente/specs/US-18.md) | Reintentos, límite de tokens y fallback determinístico | Borrador | Especificar |
| [US-19](agente/specs/US-19.md) | Ver cola de manuscritos pendientes | Borrador | Especificar |
| [US-20](agente/specs/US-20.md) | Ver sugerencias con su evidencia | Borrador | Especificar |
| [US-28](agente/specs/US-28.md) | Registro de ejecución por manuscrito | Borrador | Especificar |

### Historias

| ID | Historia | Ép. | Rel. | Sprint | ★ | Estado spec | Fase SDD | Pruebas | Commits |
|---|---|---|---|---|---|---|---|---|---|
| [US-00](agente/specs/US-00.md) | Especificación general del producto y configuración del entorno | T | R1 | 2 |  | Implementada | Implementar | 6 | 1 |
| [US-01](agente/specs/US-01.md) | Recibir PDF por API | A | R1 | 2 | ★ | Implementada | Implementar | 11 | 1 |
| [US-02](agente/specs/US-02.md) | Plugin OJS: hook al completar un envío | A | R1 | 5 |  | Borrador | Especificar |  |  |
| [US-03](agente/specs/US-03.md) | Obtener metadatos del envío (sección, título, idioma) | A | R1 | 3 |  | Borrador | Especificar |  |  |
| [US-04](agente/specs/US-04.md) | Extraer texto y páginas | B | R1 | 2 | ★ | Implementada | Implementar | 11 | 1 |
| [US-05](agente/specs/US-05.md) | Detectar secciones IMRyD | B | R1 | 3 | ★ | Borrador | Especificar |  |  |
| [US-06](agente/specs/US-06.md) | Extraer figuras: posición, tamaño y pie | B | R1 | 2 | ★ | Implementada | Implementar | 13 | 1 |
| [US-07](agente/specs/US-07.md) | Extraer citas en texto [n] | B | R1 | 3 | ★ | Borrador | Especificar |  |  |
| [US-08](agente/specs/US-08.md) | Extraer lista de referencias | B | R1 | 3 | ★ | Borrador | Especificar |  |  |
| [US-09](agente/specs/US-09.md) | Cargar reglas Innosoft desde YAML | C | R1 | 2 | ★ | Implementada | Implementar | 15 | 1 |
| [US-10](agente/specs/US-10.md) | Validar figuras: tamaño y proporción | C | R1 | 2 | ★ | Implementada | Implementar | 14 | 2 |
| [US-11](agente/specs/US-11.md) | Validar figuras: pie, numeración y orden | C | R1 | 3 |  | Borrador | Especificar |  |  |
| [US-12](agente/specs/US-12.md) | Validar citas IEEE en el texto | C | R1 | 3 | ★ | Borrador | Especificar |  |  |
| [US-13](agente/specs/US-13.md) | Validar referencias IEEE (formato, orden y mínimo) | C | R1 | 3 | ★ | Borrador | Especificar |  |  |
| [US-14](agente/specs/US-14.md) | Validar estructura, resumen y palabras clave | C | R2 | — |  | Borrador | Especificar |  |  |
| [US-15](agente/specs/US-15.md) | Redactar sugerencia con Gemini | D | R1 | 4 | ★ | Borrador | Especificar |  |  |
| [US-16](agente/specs/US-16.md) | Validar el esquema de respuesta del LLM | D | R1 | 4 | ★ | Borrador | Especificar |  |  |
| [US-17](agente/specs/US-17.md) | Anonimizar el contexto antes de enviarlo al LLM | D | R1 | 4 |  | Borrador | Especificar |  |  |
| [US-18](agente/specs/US-18.md) | Reintentos, límite de tokens y fallback determinístico | D | R1 | 4 |  | Borrador | Especificar |  |  |
| [US-19](agente/specs/US-19.md) | Ver cola de manuscritos pendientes | E | R1 | 4 | ★ | Borrador | Especificar |  |  |
| [US-20](agente/specs/US-20.md) | Ver sugerencias con su evidencia | E | R1 | 4 | ★ | Borrador | Especificar |  |  |
| [US-21](agente/specs/US-21.md) | Aceptar, rechazar o editar cada sugerencia | E | R1 | 5 | ★ | Borrador | Especificar |  |  |
| [US-22](agente/specs/US-22.md) | Agregar una sugerencia manual | E | R2 | — |  | Borrador | Especificar |  |  |
| [US-23](agente/specs/US-23.md) | Marcar manuscrito como "sin observaciones" | E | R2 | — |  | Borrador | Especificar |  |  |
| [US-24](agente/specs/US-24.md) | Publicar comentario en la discusión del envío | F | R1 | 5 | ★ | Borrador | Especificar |  |  |
| [US-25](agente/specs/US-25.md) | Reintento y cola si OJS no responde | F | R2 | — |  | Borrador | Especificar |  |  |
| [US-26](agente/specs/US-26.md) | Vincular el comentario a la versión del manuscrito | F | R2 | — |  | Borrador | Especificar |  |  |
| [US-27](agente/specs/US-27.md) | Notificar al editor por correo de OJS | F | R2 | — |  | Borrador | Especificar |  |  |
| [US-28](agente/specs/US-28.md) | Registro de ejecución por manuscrito | G | R1 | 4 | ★ | Borrador | Especificar |  |  |
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

### Calendario de sprints (fuente: Excel RICE, hoja *Replan 29-sep*)

| Sprint | Fechas | Historias | Meta |
|---|---|---|---|
| 2 | 29-sep → 09-oct | US-00, US-01, US-04, US-09, US-06, US-10 | Walking skeleton en Docker con RE-20/RE-21 |
| 3 | 12-oct → 23-oct | US-03, US-05*, US-07, US-08*, US-11*, US-12, US-13* + spike OJS | Citas y referencias IEEE detectadas; decisión técnica sobre OJS |
| 4 ◀ en curso | 26-oct → 06-nov | US-17, US-15, US-16, US-18*, US-28, US-19, US-20 | Sugerencias con Gemini anonimizadas y visibles para el editor |
| 5 | 09-nov → 20-nov | US-21, US-24, US-02 | Flujo completo: OJS → agente → editor → comentario en OJS |
| 6 | 23-nov → 04-dic | Sin historias nuevas | Buffer, evaluación (precisión, recall, F1, aceptación), manuales, tesis |

### Tesis (Tesis-Doc/)

| Parte | Archivo | Estado | Actualizado | \pendiente |
|---|---|---|---|---|
| Preliminares (dedicatoria, siglas, resumen, abstract) | [Tesis-Doc/capitulos/00-preliminares.tex](Tesis-Doc/capitulos/00-preliminares.tex) | borrador | 2026-10-30 | 4 |
| Capítulo I – Problemática del proyecto | [Tesis-Doc/capitulos/01-problematica.tex](Tesis-Doc/capitulos/01-problematica.tex) | borrador | 2026-10-19 |  |
| Capítulo II – Planteamiento del proyecto | [Tesis-Doc/capitulos/02-planteamiento.tex](Tesis-Doc/capitulos/02-planteamiento.tex) | borrador | 2026-10-30 | 2 |
| Capítulo III – Metodología de desarrollo | [Tesis-Doc/capitulos/03-metodologia.tex](Tesis-Doc/capitulos/03-metodologia.tex) | borrador | 2026-10-30 | 3 |
| Conclusiones | [Tesis-Doc/capitulos/04-conclusiones.tex](Tesis-Doc/capitulos/04-conclusiones.tex) | pendiente | 2026-10-19 | 1 |
| Referencias | [Tesis-Doc/capitulos/referencias.tex](Tesis-Doc/capitulos/referencias.tex) | borrador | 2026-10-30 |  |
| Anexo A – Ficha de búsqueda | [Tesis-Doc/anexos/A-ficha-busqueda.tex](Tesis-Doc/anexos/A-ficha-busqueda.tex) | borrador | 2026-10-19 | 2 |
| Anexo A – Fichas de lectura crítica | [Tesis-Doc/anexos/fichas-lectura.tex](Tesis-Doc/anexos/fichas-lectura.tex) | no incluido | 2026-10-19 |  |
| Anexo B – Matriz de trazabilidad | [Tesis-Doc/anexos/matriz-trazabilidad.tex](Tesis-Doc/anexos/matriz-trazabilidad.tex) | borrador | 2026-10-19 |  |

<!-- AUTO:FIN -->
