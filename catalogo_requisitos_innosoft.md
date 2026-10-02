# Catálogo de Requisitos — Agente de sugerencias estilísticas para Innosoft

**Producto:** Agente de IA integrado con Open Journal Systems que revisa el estilo de los manuscritos enviados a la Revista *Innovación y Software* (Innosoft) y propone correcciones que el editor valida antes de comunicarlas al autor.
**Versión:** 1.1 · **Fecha:** 29-sep-2026 (replanificación; v1.0 del 11-sep-2026) · **Metodología:** Scrum (sprints de 2 semanas) + Spec-Driven Development + Flow Engineering
**Documentos relacionados:** `metodologia_desarrollo.md` (Capítulo III) · `priorizacion_rice_sprint1.xlsx` (RICE y Sprint 1)

---

## 1. Contexto del producto

| Aspecto | Definición |
|---|---|
| Revista | *Innovación y Software* (Innosoft), Universidad La Salle, Arequipa |
| Plataforma | OJS 3.1.2.1 con acceso completo (base de datos, API REST, plugins) |
| Disparador | Plugin de OJS que se activa cuando un autor completa un envío |
| Etapa cubierta | Corrección de estilo en la evaluación editorial inicial, antes de la revisión por pares |
| Entrada | PDF del manuscrito (el equipo editorial convierte DOCX y LaTeX a PDF) |
| Idioma de los manuscritos | Español |
| Salida | Un comentario en la discusión del envío en OJS, visible para el autor, con las sugerencias aprobadas por el editor |
| Problemas prioritarios | Figuras con etiquetas incorrectas, demasiado pequeñas o recortadas; referencias que no siguen el formato IEEE |
| Marco normativo | Ley N.º 29733 de Protección de Datos Personales (Perú); Declaración de privacidad y Política editorial de la revista |
| Plantillas oficiales | `Plantilla_Final_InnoSoft.docx` e `innosoft_template.tex` (clase `innosoft.cls`) |
| Equipo | Dos investigadores-developers; Product Owner y Scrum Master asumidos por los mismos integrantes |

### Objetivo del producto

> Desarrollar un agente de inteligencia artificial integrado con Open Journal Systems que analice los manuscritos enviados a Innosoft en formato PDF, identifique incumplimientos respecto de las normas editoriales de la revista y genere sugerencias estilísticas claras, trazables y revisables por un editor.

### Nomenclatura

| Prefijo | Significado |
|---|---|
| `US-nn` | Historia de usuario (unidad de planificación en el backlog) |
| `RE-nn` | Regla editorial de Innosoft (unidad que evalúa el motor de validación) |
| `RNF-nn` | Requisito no funcional |
| `ALT-nn` | Flujo alternativo o de excepción |
| `AC` | Criterio de aceptación |

Cada historia tendrá su especificación en `specs/US-nn.md` antes de implementarse, siguiendo el ciclo Spec-Driven Development definido en el Capítulo III.

---

## 2. Actores

| Actor | Descripción |
|---|---|
| **Autor** | Envía el manuscrito por OJS. Recibe comentarios de estilo aprobados por el editor. No interactúa con el agente. |
| **Editor / Editor de sección** | Revisa las sugerencias generadas, las acepta, rechaza o edita, y las publica como comentario en OJS. |
| **Administrador** | Gestiona reglas editoriales, credenciales de OJS y Gemini, y consulta registros. |
| **Plugin OJS** | Actor de sistema. Detecta el envío, entrega PDF + metadatos al agente y publica el comentario final. |
| **Agente** | Actor de sistema. Extrae, valida, genera sugerencias y expone la cola de revisión. |

---

## 3. User Story Map

### 3.1 Backbone (actividades) y flujo principal (happy path)

```
 A. Recibir envío  →  B. Extraer documento  →  C. Validar reglas  →  D. Generar sugerencias  →  E. Revisar (editor)  →  F. Publicar en OJS  →  G. Administrar y observar
```

**Happy path narrado:**
Un autor envía un artículo original a Innosoft → el plugin detecta el envío, obtiene el PDF y los metadatos (sección, idioma, autor) y lo entrega al agente → el agente extrae texto, secciones, figuras (con dimensiones y pies) y referencias → el motor aplica las reglas de Innosoft y produce incumplimientos con ubicación (página, sección, figura n.º) → Gemini redacta cada incumplimiento como una sugerencia clara en español, conservando el ID de la regla → el editor abre la cola de revisión, ve las sugerencias agrupadas por tipo con su evidencia, acepta la mayoría, edita una y descarta otra → el agente publica un único comentario ordenado en la discusión del envío en OJS, visible para el autor → queda registrado quién decidió qué, el tiempo total y el consumo de la API.

### 3.2 Mapa completo

Historias agrupadas por actividad del backbone, en orden de prioridad dentro de cada actividad. Las marcadas con ★ forman el **walking skeleton**: el flujo mínimo de punta a punta que debe existir antes de profundizar en cualquier actividad.

**A. Recibir envío**
- ★ US-01 Recibir PDF por API
- US-02 Plugin OJS: hook al completar un envío
- US-03 Obtener metadatos del envío (sección, título, idioma)
- US-31 Detectar reenvío (versión 2 del manuscrito)

**B. Extraer documento**
- ★ US-04 Extraer texto y páginas
- ★ US-05 Detectar secciones IMRyD
- ★ US-06 Extraer figuras: posición, tamaño, pie
- ★ US-07 Extraer citas en texto `[n]`
- ★ US-08 Extraer lista de referencias
- US-34 Detectar tablas y sus títulos
- US-35 Detectar figuras recortadas o fuera de margen

**C. Validar reglas**
- ★ US-09 Cargar reglas Innosoft desde YAML
- ★ US-10 Validar figuras: tamaño y proporción
- US-11 Validar figuras: pie, numeración y orden
- ★ US-12 Validar citas IEEE en el texto
- ★ US-13 Validar referencias IEEE (formato, orden, mínimo)
- US-14 Validar estructura, resumen y palabras clave
- US-36 Validar formato de página (fuente, márgenes, numeración)

**D. Generar sugerencias**
- ★ US-15 Redactar sugerencia con Gemini
- ★ US-16 Validar el esquema de respuesta del LLM
- US-17 Anonimizar el contexto antes de enviarlo al LLM
- US-18 Reintentos, límite de tokens y fallback determinístico

**E. Revisar (editor)**
- ★ US-19 Ver cola de manuscritos pendientes
- ★ US-20 Ver sugerencias con su evidencia
- ★ US-21 Aceptar, rechazar o editar cada sugerencia
- US-22 Agregar una sugerencia manual
- US-23 Marcar manuscrito como "sin observaciones"

**F. Publicar en OJS**
- ★ US-24 Publicar comentario en la discusión del envío
- US-25 Reintento y cola si OJS no responde
- US-26 Vincular el comentario a la versión del manuscrito
- US-27 Notificar al editor por correo de OJS

**G. Administrar y observar**
- ★ US-28 Registro de ejecución por manuscrito
- US-29 Registro de consumo y latencia de Gemini
- US-30 Editar reglas sin redespliegue
- US-32 Panel de métricas (tasa de aceptación, tiempos)
- US-33 Auditoría de decisiones editoriales

### 3.3 Flujos alternativos y de excepción

| ID | Flujo alternativo | Actividad | Historia que lo cubre |
|---|---|---|---|
| ALT-01 | PDF sin capa de texto (escaneado) o corrupto | B | US-04 (criterio: rechazo controlado + aviso al editor) |
| ALT-02 | No se detectan secciones estándar (artículo mal estructurado) | B/C | US-05, US-14 (se reporta como incumplimiento, no como error) |
| ALT-03 | Manuscrito sin figuras | B/C | US-06 (las reglas de figura se omiten, no fallan) |
| ALT-04 | Referencias sin numerar o con formato mixto (APA + IEEE) | C | US-12, US-13 |
| ALT-05 | Gemini no responde, excede cuota o devuelve JSON inválido | D | US-16, US-18 (fallback: sugerencia plantilla determinística) |
| ALT-06 | Editor rechaza todas las sugerencias | E/F | US-23 (no se publica comentario; se registra) |
| ALT-07 | Sección OJS no mapeada (p. ej., editorial, carta) | A | US-03 (se ignora el envío y se registra) |
| ALT-08 | Manuscrito en inglés | A/B | US-03 (se marca fuera de alcance y se notifica al editor) |
| ALT-09 | Autor reenvía versión corregida | A/F | US-31, US-26 |
| ALT-10 | API de OJS caída al publicar | F | US-25 |
| ALT-11 | PDF contiene datos personales (nombres, correos, afiliaciones) | D | US-17 (se envía a Gemini solo el fragmento anonimizado) |
| ALT-12 | Dos editores revisan el mismo manuscrito | E | US-21 (bloqueo optimista / último gana con registro) |

---

## 4. Catálogo de historias de usuario

### Épica A — Recepción del envío

**US-01 · Recibir PDF por API**
Como *plugin OJS*, quiero enviar un PDF y sus metadatos a un endpoint del agente, para iniciar el análisis.
AC: `POST /manuscripts` acepta multipart (PDF ≤ 25 MB + JSON de metadatos); responde 202 con `manuscript_id`; rechaza con 400 archivos que no sean PDF; persiste el archivo y el estado `received`.

**US-02 · Plugin OJS: hook al crear envío**
Como *editor*, quiero que el análisis se dispare solo al completar un envío, para no hacer nada manual.
AC: plugin genérico OJS 3.1.2.1 escucha el hook de envío completado; obtiene el archivo de envío (galerada original) y lo remite a US-01; si falla, registra en el log de OJS sin bloquear el envío del autor.

**US-03 · Obtener metadatos del envío**
Como *agente*, quiero conocer sección (corto/original/revisión), idioma y título, para aplicar el conjunto de reglas correcto.
AC: se mapean las tres secciones de Innosoft; secciones no mapeadas o idioma ≠ español se registran como `out_of_scope` y se notifica al editor (ALT-07, ALT-08).

**US-31 · Detectar reenvío (versión 2)**
Como *editor*, quiero que una nueva versión del mismo envío se analice como revisión, para comparar qué se corrigió.
AC: mismo `submission_id` + nueva revisión → nuevo análisis vinculado al anterior; el comentario indica "Revisión 2".

### Épica B — Extracción documental

**US-04 · Extraer texto y páginas**
Como *agente*, quiero el texto por página con coordenadas, para ubicar cada hallazgo.
AC: PyMuPDF; salida JSON `{page, blocks[{bbox, text, font, size}]}`; PDF sin texto → estado `unreadable` + aviso (ALT-01); tiempo < 10 s para 30 páginas.

**US-05 · Detectar secciones IMRyD**
Como *agente*, quiero identificar Resumen/Abstract, Palabras clave, Introducción, Materiales y métodos, Resultados y discusión, Conclusiones, Agradecimientos y Referencias, para validar la estructura.
AC: detección por heurística (mayúsculas, numeración, tamaño de fuente) con tolerancia a variantes ("Metodología computacional", "Desarrollo"); secciones no encontradas se reportan como `missing`, no como error.

**US-06 · Extraer figuras: bbox, tamaño, pie**
Como *agente*, quiero para cada imagen su página, bbox, dimensiones en píxeles, DPI efectivo y pie de figura asociado, para validar las reglas de figuras.
AC: se recuperan imágenes rasterizadas y vectoriales; se asocia el pie por proximidad ("Figura n." debajo); se calcula el DPI efectivo (px / tamaño impreso en pulgadas).

**US-07 · Extraer citas en texto `[n]`**
AC: regex + contexto: `[1]`, `[3, 4]`, `[1]–[5]`; se registra posición y puntuación adyacente; se detectan citas tipo autor-año (APA) como candidatas a incumplimiento.

**US-08 · Extraer lista de referencias**
AC: se segmenta la sección Referencias en entradas numeradas; cada entrada se parsea en campos (autores, título, fuente, año, URL) con un parser tolerante; se conserva el texto crudo.

**US-34 · Detectar tablas y sus títulos** · **US-35 · Detectar figuras recortadas / fuera de margen** (release 2)

### Épica C — Motor de validación (reglas Innosoft)

**US-09 · Cargar reglas Innosoft desde YAML**
AC: cada regla tiene `id, categoría, descripción, condición, severidad, mensaje, sección_aplicable, fuente (URL de la directriz)`; se validan contra un JSON Schema al arrancar; se puede cargar un archivo de reglas por sección.

**US-10 · Validar figuras: tamaño y proporción** (RE-20, RE-21, RE-22)
**US-11 · Validar figuras: pie, numeración, orden** (RE-23, RE-24, RE-25)
**US-12 · Validar citas IEEE en texto** (RE-40, RE-41, RE-42, RE-43)
**US-13 · Validar referencias IEEE** (RE-44 a RE-49)
**US-14 · Validar estructura, resumen y palabras clave** (RE-01 a RE-15, RE-66)
**US-36 · Validar formato de página** (RE-60 a RE-65) (release 2)

AC común: cada incumplimiento produce `{rule_id, severidad, página, ubicación, evidencia, valor_encontrado, valor_esperado}`; un error en una regla no detiene las demás; suite Pytest con al menos un caso positivo y uno negativo por regla.

### Épica D — Generación de sugerencias (Gemini)

**US-15 · Redactar sugerencia con Gemini**
Como *editor*, quiero que cada incumplimiento se convierta en una sugerencia redactada en español claro y cordial, para poder enviarla al autor casi sin editar.
AC: prompt versionado en repositorio; salida JSON estructurada `{rule_id, sugerencia, ejemplo_corregido?}`; `temperature ≤ 0.3`; toda sugerencia conserva su `rule_id`.

**US-16 · Validar esquema de respuesta del LLM**
AC: respuesta que no cumpla el esquema o cambie `rule_id` se descarta y se reintenta una vez; si persiste, se usa el `mensaje` determinístico de la regla (ALT-05).

**US-17 · Anonimizar contexto antes de enviar al LLM**
AC: al modelo solo se envía el fragmento relevante (≤ 600 caracteres alrededor del hallazgo); se enmascaran nombres de autores, correos, ORCID y afiliaciones detectados en la primera página; queda registrado qué se envió.

**US-18 · Reintentos, límite de tokens y fallback**
AC: backoff exponencial (3 intentos); límite de tokens por manuscrito configurable; si se excede, el resto de sugerencias usa fallback determinístico y se avisa al editor.

### Épica E — Revisión editorial

**US-19 · Ver cola de manuscritos pendientes**
AC: lista con título, sección, fecha, n.º de sugerencias por severidad y estado; acceso solo con rol editor (sesión OJS o token).

**US-20 · Ver sugerencias con evidencia**
AC: agrupadas por categoría (figuras, referencias, estructura, formato); cada una muestra regla, página, fragmento/miniatura de la figura y texto propuesto.

**US-21 · Aceptar / rechazar / editar sugerencia**
AC: tres acciones por sugerencia + "aceptar todas de la categoría"; edición conserva original y versión editada; se registra usuario y hora (ALT-12).

**US-22 · Agregar sugerencia manual** · **US-23 · Marcar "sin observaciones"** (ALT-06)

### Épica F — Publicación en OJS

**US-24 · Publicar comentario en discusión OJS**
Como *autor*, quiero recibir un único comentario ordenado con las observaciones de estilo, para corregir mi manuscrito antes de la revisión por pares.
AC: se crea una discusión en la etapa "Envío" vía API REST de OJS 3.1.2.1 (o inserción directa vía plugin si la API no lo permite en esa versión); el comentario contiene solo sugerencias aprobadas, agrupadas por categoría, con página y referencia a la directriz; firma "Revisión asistida por IA, validada por el editor".

**US-25 · Reintento y cola si OJS no responde** (ALT-10) · **US-26 · Vincular comentario a versión** · **US-27 · Notificar al editor**

### Épica G — Administración y observabilidad

**US-28 · Registro de ejecución por manuscrito**
AC: tabla `runs` con tiempos por etapa, reglas evaluadas, n.º de hallazgos, errores; consultable por `manuscript_id`.
**US-29 · Registro de consumo y latencia de Gemini** · **US-30 · Editar reglas sin redeploy** · **US-32 · Panel de métricas** · **US-33 · Auditoría de decisiones**

## 5. Requisitos no funcionales

| ID | Requisito | Verificación |
|---|---|---|
| RNF-01 | Ninguna sugerencia llega al autor sin aprobación humana | Prueba E2E: sin acción del editor no existe comentario en OJS |
| RNF-02 | Datos personales no salen a Gemini (Ley 29733) | Prueba US-17 + inspección de logs de prompts |
| RNF-03 | Análisis completo de un artículo original (15 pág.) < 3 min | Medición en US-28 |
| RNF-04 | Trazabilidad regla → hallazgo → sugerencia → decisión → comentario | Matriz de trazabilidad por IDs |
| RNF-05 | Reglas editables sin cambiar código | US-09, US-30 |
| RNF-06 | Fallo de una etapa no pierde el manuscrito ni bloquea el envío en OJS | ALT-01, ALT-05, ALT-10 |
| RNF-07 | Todo versionado en GitHub: código, specs, prompts, reglas | Revisión de repositorio |

---

## 6. Catálogo de reglas editoriales Innosoft (RE)

Fuentes: (a) *Directrices para autores* de la revista, (b) `Plantilla_Final_InnoSoft.docx`, (c) `innosoft_template.tex`. La columna **Fuente** indica de dónde sale cada valor; la columna **Detectable** indica si la regla puede evaluarse sobre el PDF de forma determinística (D), requiere apoyo del LLM (L) o es solo informativa para el editor (I).

### 6.1 Estructura y metadatos

| ID | Regla | Severidad | Fuente | Detectable |
|---|---|---|---|---|
| RE-01 | Título en español (negritas, 18 pt) **y** título en inglés (negritas, cursiva, 18 pt) | Alta | b, c | D |
| RE-02 | Título en español **≤ 15 palabras** | Media | b, c | D |
| RE-03 | Resumen en español en **un solo párrafo**, 200–250 palabras, 11 pt | Alta | a, b, c | D |
| RE-04 | Resumen redactado en tercera persona y tiempo pasado; **sin referencias, abreviaturas ni ecuaciones** | Media | b, c | L |
| RE-05 | Abstract en inglés en un solo párrafo, ≤ 250 palabras, cursiva | Alta | b, c | D |
| RE-06 | 3–5 palabras clave en español, **ordenadas alfabéticamente**; Keywords en inglés en cursiva | Alta | a, b, c | D |
| RE-07 | Autores: nombre y apellidos 11 pt negritas, superíndice de afiliación, ORCID entre corchetes; **un solo** autor de correspondencia con asterisco | Media | a, b, c | D |
| RE-08 | Afiliación institucional completa + dirección postal + correo por cada autor | Media | a, b, c | D/L |
| RE-09 | Secciones obligatorias en orden: Introducción · Materiales y métodos (o Metodología computacional) · Resultados y discusión · Conclusiones · Contribución de Autoría · Referencias (Agradecimientos opcional entre Conclusiones y Contribución) | Alta | a, b, c | D |
| RE-10 | Sección **Contribución de Autoría** con roles CRediT por cada autor | Alta | b, c, política editorial | D/L |
| RE-11 | Declaración de uso de IA generativa después de Contribución de Autoría, cuando aplique | Baja | política editorial | I |
| RE-12 | Extensión por tipo: corto ≤ 5 pág.; original 10–15; revisión 15–30 | Media | a | D |
| RE-13 | Temática declarada pertenece a la lista de 12 temáticas de la revista | Baja | c | D |
| RE-14 | Siglas y abreviaturas definidas en su primera aparición | Baja | a, b, c | L |
| RE-15 | Redacción en tercera persona ("se presenta", "se evaluó") | Baja | b, c | L |

### 6.2 Figuras y tablas

| ID | Regla | Severidad | Fuente | Detectable |
|---|---|---|---|---|
| RE-20 | Imagen ≥ 531 × 1328 px (alto × ancho) o proporción 200 × 500 si es panorámica | Alta | a | D |
| RE-21 | Resolución efectiva ≥ 300 dpi | Alta | a | D |
| RE-22 | Figura contenida en los márgenes de página (no recortada, no desbordada); en LaTeX ancho de referencia 0,9\textwidth | Alta | a, c | D |
| RE-23 | Pie de figura **debajo**, centrado, Times New Roman 10 pt, formato "Figura n. Título" | Media | a, b, c | D |
| RE-24 | Numeración secuencial de figuras por orden de aparición | Media | a, b, c | D |
| RE-25 | Toda figura referenciada en el texto como "Figura n" (no "figura de abajo", "la siguiente imagen") | Media | b, c | D |
| RE-26 | Texto interno de la figura legible y en el idioma del artículo; fuentes Times/Arial/Courier/Symbol | Baja | a | L/I |
| RE-27 | Formato preferido vectorial (SVG/EPS); aceptables TIFF/PNG | Baja | a | I |
| RE-28 | Título de tabla **arriba**, centrado, 10 pt, "Tabla n. Título"; numeración secuencial | Media | a, b, c | D |
| RE-29 | Notas al pie de tabla a 9 pt | Baja | b, c | D |
| RE-30 | Toda tabla referenciada en el texto como "Tabla n" | Media | b, c | D |
| RE-31 | Ecuaciones numeradas secuencialmente a la derecha "(n)" y referenciadas como "Ecuación n" | Baja | b, c | D |

### 6.3 Citas y referencias (IEEE)

| ID | Regla | Severidad | Fuente | Detectable |
|---|---|---|---|---|
| RE-40 | Citas numéricas entre corchetes `[n]`, precedidas de espacio y **antes** de la puntuación | Alta | a, b, c | D |
| RE-41 | Numeración por orden de primera aparición; el mismo número se reutiliza en citas posteriores | Alta | a, b, c | D |
| RE-42 | Citas múltiples como `[1], [3], [5]` o `[1]–[5]`; no `[1,3,5]` ni "en la referencia [2]" | Media | a, b, c | D |
| RE-43 | Sin citas autor-año (APA) ni notas al pie bibliográficas | Alta | a | D |
| RE-44 | Mínimo de referencias: corto 7 · original 15 · revisión 25 | Alta | a | D |
| RE-45 | Cada entrada cumple el patrón IEEE de su tipo (iniciales + apellido, título entre comillas, fuente en cursiva, vol./no./pp., año; "[Online]. Available: URL [Accessed: fecha]" para web) | Alta | a, b, c | D/L |
| RE-46 | Correspondencia total: toda referencia está citada y toda cita tiene referencia | Alta | a | D |
| RE-47 | La lista de referencias sigue el orden de citación (no alfabético) | Media | a | D |
| RE-48 | URL o DOI cuando exista | Baja | a | D |
| RE-49 | Sección "Información sobre las Referencias" de la plantilla eliminada (texto de ejemplo residual) | Media | c | D |

### 6.4 Formato de página

| ID | Regla | Severidad | Fuente | Detectable |
|---|---|---|---|---|
| RE-60 | Cuerpo en Times New Roman 11 pt | Baja | a, b, c | D |
| RE-61 | Interlineado 1,5 y línea en blanco entre párrafos/secciones | Baja | a, b, c | D |
| RE-62 | Papel carta 21,59 × 27,94 cm | Baja | a | D |
| RE-63 | Márgenes: superior/inferior 3,81 cm; izquierdo 2 cm; derecho 1,2 cm | Baja | a | D |
| RE-64 | Páginas numeradas en esquina inferior derecha | Baja | a | D |
| RE-65 | Sistema Internacional de Unidades y coma decimal | Baja | a, b, c | L |
| RE-66 | Texto de instrucciones de la plantilla no eliminado (p. ej. "Los párrafos se escribirán en Times New Roman…", "Nombre y apellidos 1") | Media | b, c | D |

**Reglas por sprint (replanificación del 29-sep-2026):** **Sprint 2:** RE-20, RE-21 (supuesto aprobado: mínimo 531 × 1328 px). **Sprint 3:** RE-23, RE-24, RE-40..44, RE-46, RE-47, RE-49. **Fuera del MVP:** RE-22 (pasa a US-35), RE-25, RE-45, RE-48 y las reglas de US-14 y US-36.

---

## 7. Replanificación del 29-sep-2026

El Sprint 1 (14–25 sep) produjo especificación y diseño, pero no código. Su objetivo (walking skeleton) pasa al Sprint 2 y el resto del plan se comprime en los Sprints 3 a 5; el Sprint 6 queda para evaluación. El detalle está en la hoja *Replan 29-sep* de `priorizacion_rice_sprint1.xlsx`.

| Sprint | Fechas | Historias |
|---|---|---|
| 2 | 28-sep – 9-oct | US-00, US-01, US-04, US-09, US-06, US-10 |
| 3 | 12-oct – 23-oct | US-03, US-05\*, US-07, US-08\*, US-11\*, US-12, US-13\* + spike API OJS |
| 4 | 26-oct – 6-nov | US-17, US-15, US-16, US-18\*, US-28, US-19, US-20 |
| 5 | 9-nov – 20-nov | US-21, US-24, US-02 |
| 6 | 23-nov – 4-dic | Evaluación, buffer, manuales |

\* Alcance reducido para el MVP:

- **US-05:** solo Resumen, Palabras clave y Referencias.
- **US-08:** segmentación y numeración, sin parseo por campos.
- **US-11:** RE-23 y RE-24.
- **US-13:** RE-44, RE-46, RE-47 y RE-49.
- **US-18:** sin presupuesto de tokens.

**Sacadas del plan (backlog R2):** US-14, US-22, US-23, US-25, US-27 y US-29.

