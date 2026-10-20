---
id: formato-reglas
titulo: "Formato de las reglas editoriales"
tipo: spec transversal
historia: US-00 (definición) · US-09 (carga) · US-30 (edición sin redespliegue)
estado_spec: Aprobada   # Borrador → En revisión → Aprobada
version_spec: 1.0
fecha: 2026-09-29
---

# Formato de las reglas editoriales

> **Qué es este documento.** Es el contrato entre la **política editorial** de Innosoft (qué se exige a un manuscrito) y el
> **código** del motor (cómo se evalúa). Define cómo se escribe una regla en YAML, qué campos lleva, cómo se valida y qué
> produce cuando detecta un incumplimiento.
>
> **Por qué existe.** Las directrices de la revista cambian (tamaños mínimos de figura, número mínimo de referencias,
> mensajes). Con este formato, esos cambios se hacen editando un archivo YAML y no el código (RNF-05), y cada hallazgo queda
> trazable a una regla con ID (RNF-04, DoD n.º 4).

---

## 1. Principios

1. **Una regla = un ID del catálogo.** Cada `RE-nn` del catálogo de requisitos tiene exactamente una entrada YAML.
2. **La regla dice *qué*; el evaluador dice *cómo*.** La regla nombra un `evaluador` (función Python registrada) y le pasa `parametros`. Los números viven en el YAML; la lógica, en el código.
3. **Se valida al arrancar.** Un archivo inválido detiene el arranque con un mensaje claro; nunca se ejecuta un conjunto de reglas a medias.
4. **Una regla se puede definir antes de implementarse.** Si su evaluador aún no existe, se carga como `not_implemented` y se omite con aviso.
5. **Todo cambio de reglas pasa por pull request** y cambia el hash de versión que se registra en cada análisis.

## 2. Ubicación y organización

```text
rules/
├── schema/
│   └── rule.schema.json        # JSON Schema de este documento (§7)
└── innosoft/
    ├── estructura.yaml         # RE-01 … RE-15, RE-66
    ├── figuras.yaml            # RE-20 … RE-31
    ├── citas.yaml              # RE-40 … RE-43
    ├── referencias.yaml        # RE-44 … RE-49
    └── formato.yaml            # RE-60 … RE-65
```

- Un archivo por **categoría**. El Sprint 2 solo necesita `figuras.yaml`.
- Los archivos se leen en orden alfabético; el orden no altera el resultado.
- Codificación UTF-8; claves en español **sin tildes** (`categoria`, `seccion_aplicable`) para evitar problemas de codificación.

## 3. Estructura de un archivo

```yaml
schema_version: 1            # versión de este formato
categoria: figuras           # debe coincidir con la categoría de todas sus reglas
actualizado: "2026-09-29"   # entre comillas: YAML convertiría la fecha sin comillas en un objeto date
reglas:
  - id: RE-20
    # … campos de la §4
  - id: RE-21
    # …
```

## 4. Campos de una regla

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `id` | string `RE-nn` | Sí | Identificador del catálogo. Único en todo el conjunto. |
| `categoria` | enum | Sí | `estructura`, `figuras`, `tablas`, `ecuaciones`, `citas`, `referencias`, `formato`. Agrupa en la vista del editor y en el comentario. |
| `descripcion` | string | Sí | Enunciado de la regla tal como figura en el catálogo. |
| `condicion` | objeto | Sí | `evaluador` (nombre registrado), `parametros` (valores generales) y, opcionalmente, `parametros_por_tipo` (valores por tipo de artículo). |
| `severidad` | enum | Sí | `alta`, `media`, `baja` (§5). |
| `detectable` | enum | Sí | `D` determinística, `L` requiere LLM, `I` informativa (§6). |
| `mensaje` | string | Sí | Texto del fallback determinístico con marcadores (§8). ≤ 300 caracteres. |
| `seccion_aplicable` | lista | Sí | Subconjunto de `corto`, `original`, `revision`. |
| `fuente` | objeto | Sí | `documentos` (lista de `a`, `b`, `c`, `politica`), `url` de la directriz y `referencia` (apartado o página). |
| `activa` | boolean | No (por defecto `true`) | Permite desactivar una regla sin borrarla. |
| `notas` | string | No | Comentarios internos; no se muestran al autor. |

**Fuentes:** (a) Directrices para autores de la revista · (b) `Plantilla_Final_InnoSoft.docx` · (c) `innosoft_template.tex` ·
`politica` = Política editorial / Declaración de privacidad.

### 4.1 Parámetros por tipo de artículo

Cuando un umbral depende del tipo de artículo (RE-12, RE-44), se usa `parametros_por_tipo`. El motor combina
`parametros` con la entrada del tipo del manuscrito (la del tipo prevalece).

```yaml
condicion:
  evaluador: references_min_count
  parametros_por_tipo:
    corto:    {min: 7}
    original: {min: 15}
    revision: {min: 25}
```

## 5. Severidad

| Severidad | Criterio | Efecto |
|---|---|---|
| `alta` | Impide que el manuscrito pase a revisión por pares tal como está (figuras ilegibles, citas no IEEE, secciones obligatorias ausentes). | Se muestra primero; cuenta en el indicador rojo de la cola. |
| `media` | Incumplimiento visible de la plantilla que el autor debe corregir. | Orden intermedio. |
| `baja` | Detalle de formato o recomendación. | Se muestra al final; puede agregarse por manuscrito. |

La severidad **no** cambia si la sugerencia se publica o no: eso lo decide siempre el editor.

## 6. Tipo de detección

| Valor | Significado | Comportamiento del motor |
|---|---|---|
| `D` | Se evalúa sobre el PDF con reglas determinísticas. | El evaluador produce hallazgos. |
| `L` | Requiere interpretar lenguaje (tercera persona, siglas, legibilidad). | El evaluador produce **candidatos** con `requires_llm: true`; la sugerencia se marca para verificación del editor. Hasta que exista el evaluador L, la regla queda `not_implemented`. |
| `D/L` | Parte determinística y parte con LLM. | Se implementa la parte D; la parte L se marca como en `L`. |
| `I` | Solo informativa para el editor. | Genera como máximo un aviso por manuscrito, con severidad `baja`, que no se incluye por defecto en el comentario. |

## 7. JSON Schema

Archivo `rules/schema/rule.schema.json`. Valida cada archivo completo.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/innosoft-style-agent/rules/schema/rule.schema.json",
  "title": "Archivo de reglas editoriales de Innosoft",
  "type": "object",
  "required": ["schema_version", "categoria", "reglas"],
  "additionalProperties": false,
  "properties": {
    "schema_version": {"const": 1},
    "categoria": {"$ref": "#/$defs/categoria"},
    "actualizado": {"type": "string", "format": "date"},
    "reglas": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/regla"}}
  },
  "$defs": {
    "categoria": {
      "enum": ["estructura", "figuras", "tablas", "ecuaciones", "citas", "referencias", "formato"]
    },
    "tipoArticulo": {"enum": ["corto", "original", "revision"]},
    "regla": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "categoria", "descripcion", "condicion", "severidad",
                   "detectable", "mensaje", "seccion_aplicable", "fuente"],
      "properties": {
        "id": {"type": "string", "pattern": "^RE-[0-9]{2}$"},
        "categoria": {"$ref": "#/$defs/categoria"},
        "descripcion": {"type": "string", "minLength": 10},
        "condicion": {
          "type": "object",
          "additionalProperties": false,
          "required": ["evaluador"],
          "properties": {
            "evaluador": {"type": "string", "pattern": "^[a-z][a-z0-9_]*$"},
            "parametros": {"type": "object"},
            "parametros_por_tipo": {
              "type": "object",
              "propertyNames": {"$ref": "#/$defs/tipoArticulo"},
              "additionalProperties": {"type": "object"}
            }
          }
        },
        "severidad": {"enum": ["alta", "media", "baja"]},
        "detectable": {"enum": ["D", "L", "D/L", "I", "L/I"]},
        "mensaje": {"type": "string", "minLength": 10, "maxLength": 300},
        "seccion_aplicable": {
          "type": "array", "minItems": 1, "uniqueItems": true,
          "items": {"$ref": "#/$defs/tipoArticulo"}
        },
        "fuente": {
          "type": "object",
          "additionalProperties": false,
          "required": ["documentos", "url"],
          "properties": {
            "documentos": {
              "type": "array", "minItems": 1,
              "items": {"enum": ["a", "b", "c", "politica"]}
            },
            "url": {"type": "string", "format": "uri"},
            "referencia": {"type": "string"}
          }
        },
        "activa": {"type": "boolean", "default": true},
        "notas": {"type": "string"}
      }
    }
  }
}
```

**Validaciones adicionales del loader** (no expresables en JSON Schema):

1. `id` único en todos los archivos.
2. `categoria` de cada regla igual a la del archivo.
3. `evaluador` registrado en el código; si no, la regla se carga como `not_implemented`.
4. Los marcadores del `mensaje` pertenecen a la lista de la §8.
5. Los `parametros` requeridos por el evaluador están presentes (cada evaluador declara su propio esquema de parámetros con Pydantic).

## 8. Mensaje y marcadores

El `mensaje` es el texto que recibe el autor cuando no hay redacción del LLM (fallback, US-16) y sirve de referencia de
contenido para el prompt (US-15).

| Marcador | Se reemplaza por | Ejemplo |
|---|---|---|
| `{pagina}` | Página del hallazgo | `5` |
| `{figura}` | Número de figura (o posición si no tiene) | `Figura 3` |
| `{tabla}` | Número de tabla | `Tabla 2` |
| `{referencia}` | Número de referencia | `[7]` |
| `{encontrado}` | `valor_encontrado` del hallazgo | `300 × 600 px` |
| `{esperado}` | `valor_esperado` del hallazgo | `≥ 531 × 1328 px` |
| `{fragmento}` | Texto breve de evidencia (≤ 80 caracteres) | `…trabajos previos [1,3,5].` |

Estilo del mensaje: español formal, trato de *usted*, cordial, una sola idea, sin jerga técnica (`rule_id`, `bbox`) y sin
emojis.

## 9. Salida: hallazgo (`Finding`)

Todo evaluador devuelve una lista (posiblemente vacía) de hallazgos con esta forma:

```json
{
  "rule_id": "RE-20",
  "severidad": "alta",
  "pagina": 5,
  "ubicacion": {"tipo": "figura", "numero": 3, "bbox": [90.0, 200.0, 520.0, 430.0]},
  "evidencia": {"tipo": "imagen", "ruta": "storage/7f3c…/fig-3.png"},
  "valor_encontrado": "300 × 600 px",
  "valor_esperado": "≥ 531 × 1328 px",
  "requires_llm": false
}
```

| Campo | Regla |
|---|---|
| `rule_id` | Igual al `id` de la regla que lo produjo. Obligatorio. |
| `severidad` | Copiada de la regla (no la decide el evaluador). |
| `pagina` | Página 1-indexada; `null` solo para hallazgos de documento completo (p. ej. RE-44). |
| `ubicacion.tipo` | `figura`, `tabla`, `seccion`, `cita`, `referencia`, `parrafo`, `pagina`, `documento`. |
| `evidencia.tipo` | `texto` (fragmento), `imagen` (miniatura) o `lista` (varias ocurrencias). |
| `valor_encontrado` / `valor_esperado` | Texto legible para el editor. |

El motor agrega `id`, `run_id` y `manuscript_id` al persistir. Si un evaluador lanza una excepción, el motor registra
`{rule_id, estado: "rule_error", detalle}` en el run y continúa con las demás reglas.

## 10. Ejemplos completos

### RE-20 · Tamaño mínimo de figura (D)

```yaml
- id: RE-20
  categoria: figuras
  descripcion: "Imagen de al menos 531 × 1328 px (alto × ancho), o proporción 200 × 500 si es panorámica"
  condicion:
    evaluador: figure_min_pixels
    parametros:
      min_height_px: 531
      min_width_px: 1328
      aplica_a_vectoriales: false
  severidad: alta
  detectable: D
  mensaje: "La {figura} (página {pagina}) mide {encontrado}. Para asegurar su legibilidad, la revista solicita un tamaño mínimo de {esperado}."
  seccion_aplicable: [corto, original, revision]
  fuente:
    documentos: [a]
    url: "https://revistas.ulasalle.edu.pe/innosoft/about/submissions"
    referencia: "Directrices para autores — Figuras"
  notas: "Supuesto aprobado (D-03): mínimo 531 × 1328 px para toda figura raster; la variante panorámica 200 × 500 se añadirá aquí si la revista la precisa."
```

### RE-21 · Resolución efectiva (D)

```yaml
- id: RE-21
  categoria: figuras
  descripcion: "Resolución efectiva de la imagen ≥ 300 dpi"
  condicion:
    evaluador: figure_min_dpi
    parametros: {min_dpi: 300}
  severidad: alta
  detectable: D
  mensaje: "La {figura} (página {pagina}) tiene una resolución aproximada de {encontrado}; se requiere al menos {esperado}."
  seccion_aplicable: [corto, original, revision]
  fuente:
    documentos: [a]
    url: "https://revistas.ulasalle.edu.pe/innosoft/about/submissions"
    referencia: "Directrices para autores — Figuras"
```

### RE-44 · Mínimo de referencias por tipo (D, parámetros por tipo)

```yaml
- id: RE-44
  categoria: referencias
  descripcion: "Mínimo de referencias: corto 7, original 15, revisión 25"
  condicion:
    evaluador: references_min_count
    parametros_por_tipo:
      corto:    {min: 7}
      original: {min: 15}
      revision: {min: 25}
  severidad: alta
  detectable: D
  mensaje: "El manuscrito incluye {encontrado} referencias; para este tipo de artículo la revista solicita al menos {esperado}."
  seccion_aplicable: [corto, original, revision]
  fuente:
    documentos: [a]
    url: "https://revistas.ulasalle.edu.pe/innosoft/about/submissions"
```

### RE-04 · Estilo del resumen (L)

```yaml
- id: RE-04
  categoria: estructura
  descripcion: "Resumen en tercera persona y tiempo pasado, sin referencias, abreviaturas ni ecuaciones"
  condicion:
    evaluador: llm_abstract_style
    parametros: {max_fragmento: 600}
  severidad: media
  detectable: L
  mensaje: "Le sugerimos revisar la redacción del resumen: debe estar en tercera persona y en tiempo pasado, sin referencias, abreviaturas ni ecuaciones."
  seccion_aplicable: [corto, original, revision]
  fuente:
    documentos: [b, c]
    url: "https://revistas.ulasalle.edu.pe/innosoft/about/submissions"
    referencia: "Plantilla — Resumen"
```

### RE-11 · Declaración de uso de IA generativa (I)

```yaml
- id: RE-11
  categoria: estructura
  descripcion: "Declaración de uso de IA generativa después de Contribución de Autoría, cuando aplique"
  condicion:
    evaluador: ai_disclosure_notice
  severidad: baja
  detectable: I
  mensaje: "Si utilizó herramientas de IA generativa en la preparación del manuscrito, inclúyase la declaración correspondiente después de la sección Contribución de Autoría."
  seccion_aplicable: [corto, original, revision]
  fuente:
    documentos: [politica]
    url: "https://revistas.ulasalle.edu.pe/innosoft/about"
    referencia: "Política editorial"
```

## 11. Catálogo de evaluadores

Nombre del evaluador que usa cada regla, parámetros iniciales y la historia que lo implementa. Los valores iniciales se
copian al YAML; si cambian, se cambia el YAML, no esta tabla (esta tabla se actualiza en la siguiente versión de la spec).

| ID | Regla (resumen) | Sev. | Det. | Evaluador | Parámetros iniciales | Historia |
|---|---|---|---|---|---|---|
| RE-01 | Título en español (negritas, 18 pt) **y** título en inglés (negritas, cursiva, 18 pt) | Alta | D | `title_format` | tamano_pt: 18; titulo_es: negrita; titulo_en: negrita+cursiva | US-14 |
| RE-02 | Título en español **≤ 15 palabras** | Media | D | `title_max_words` | max_palabras: 15 | US-14 |
| RE-03 | Resumen en español en **un solo párrafo**, 200–250 palabras, 11 pt | Alta | D | `abstract_es_format` | palabras: 200–250; parrafos: 1; tamano_pt: 11 | US-14 |
| RE-04 | Resumen redactado en tercera persona y tiempo pasado; **sin referencias, abreviaturas ni ecuaciones** | Media | L | `llm_abstract_style` | max_fragmento: 600 | US-14 (L) |
| RE-05 | Abstract en inglés en un solo párrafo, ≤ 250 palabras, cursiva | Alta | D | `abstract_en_format` | max_palabras: 250; parrafos: 1; cursiva: true | US-14 |
| RE-06 | 3–5 palabras clave en español, **ordenadas alfabéticamente**; Keywords en inglés en cursiva | Alta | D | `keywords_format` | min: 3; max: 5; orden_alfabetico: true | US-14 |
| RE-07 | Autores: nombre y apellidos 11 pt negritas, superíndice de afiliación, ORCID entre corchetes; **un solo** autor de correspondencia con asterisco | Media | D | `authors_block` | autores_correspondencia: 1; patron_orcid | US-14 |
| RE-08 | Afiliación institucional completa + dirección postal + correo por cada autor | Media | D/L | `affiliations_complete` | campos: afiliacion, direccion, correo | US-14 (D/L) |
| RE-09 | Secciones obligatorias en orden: Introducción · Materiales y métodos (o Metodología computacional) · Resultados y discusión · Conclusiones · Contribución de Autoría · Referencias (Agradecimientos opcional entre Conclusiones y Contribución) | Alta | D | `section_order` | orden: introduccion → metodos → resultados_discusion → conclusiones → [agradecimientos] → contribucion_autoria → referencias | US-14 |
| RE-10 | Sección **Contribución de Autoría** con roles CRediT por cada autor | Alta | D/L | `authorship_credit` | roles: taxonomía CRediT | US-14 (D/L) |
| RE-11 | Declaración de uso de IA generativa después de Contribución de Autoría, cuando aplique | Baja | I | `ai_disclosure_notice` | — | US-14 (I) |
| RE-12 | Extensión por tipo: corto ≤ 5 pág.; original 10–15; revisión 15–30 | Media | D | `page_count_by_type` | corto ≤ 5; original 10–15; revision 15–30 | US-14 |
| RE-13 | Temática declarada pertenece a la lista de 12 temáticas de la revista | Baja | D | `topic_in_list` | tematicas: 12 valores de innosoft_template.tex | US-14 |
| RE-14 | Siglas y abreviaturas definidas en su primera aparición | Baja | L | `llm_acronyms_defined` | — | US-14 (L) |
| RE-15 | Redacción en tercera persona ("se presenta", "se evaluó") | Baja | L | `llm_third_person` | — | US-14 (L) |
| RE-20 | Imagen ≥ 531 × 1328 px (alto × ancho) o proporción 200 × 500 si es panorámica | Alta | D | `figure_min_pixels` | min_height_px: 531; min_width_px: 1328 (supuesto D-03) | US-10 |
| RE-21 | Resolución efectiva ≥ 300 dpi | Alta | D | `figure_min_dpi` | min_dpi: 300 | US-10 |
| RE-22 | Figura contenida en los márgenes de página (no recortada, no desbordada); en LaTeX ancho de referencia 0,9\textwidth | Alta | D | `figure_within_margins` | margenes_cm: 3,81 / 3,81 / 2 / 1,2; tolerancia_pt: 2 | US-35 |
| RE-23 | Pie de figura **debajo**, centrado, Times New Roman 10 pt, formato "Figura n. Título" | Media | D | `figure_caption_format` | posicion: below; tamano_pt: 10; patron: Figura n. Título | US-11 |
| RE-24 | Numeración secuencial de figuras por orden de aparición | Media | D | `figure_numbering_sequence` | — | US-11 |
| RE-25 | Toda figura referenciada en el texto como "Figura n" (no "figura de abajo", "la siguiente imagen") | Media | D | `figure_referenced_in_text` | frases_vagas: lista | US-11 |
| RE-26 | Texto interno de la figura legible y en el idioma del artículo; fuentes Times/Arial/Courier/Symbol | Baja | L/I | `llm_figure_text_legibility` | fuentes: Times, Arial, Courier, Symbol | — (L/I) |
| RE-27 | Formato preferido vectorial (SVG/EPS); aceptables TIFF/PNG | Baja | I | `figure_format_notice` | preferidos: SVG, EPS; aceptables: TIFF, PNG | — (I) |
| RE-28 | Título de tabla **arriba**, centrado, 10 pt, "Tabla n. Título"; numeración secuencial | Media | D | `table_title_format` | posicion: above; tamano_pt: 10; patron: Tabla n. Título | US-34 + evaluador por asignar |
| RE-29 | Notas al pie de tabla a 9 pt | Baja | D | `table_notes_size` | tamano_pt: 9 | US-34 + evaluador por asignar |
| RE-30 | Toda tabla referenciada en el texto como "Tabla n" | Media | D | `table_referenced_in_text` | — | US-34 + evaluador por asignar |
| RE-31 | Ecuaciones numeradas secuencialmente a la derecha "(n)" y referenciadas como "Ecuación n" | Baja | D | `equation_numbering` | patron: (n) a la derecha; referencia: Ecuación n | Por asignar |
| RE-40 | Citas numéricas entre corchetes `[n]`, precedidas de espacio y **antes** de la puntuación | Alta | D | `citation_brackets_spacing` | max_ocurrencias_por_hallazgo: 5 | US-12 |
| RE-41 | Numeración por orden de primera aparición; el mismo número se reutiliza en citas posteriores | Alta | D | `citation_order` | — | US-12 |
| RE-42 | Citas múltiples como `[1], [3], [5]` o `[1]–[5]`; no `[1,3,5]` ni "en la referencia [2]" | Media | D | `citation_multiple_format` | frases_prohibidas: en la referencia [n] | US-12 |
| RE-43 | Sin citas autor-año (APA) ni notas al pie bibliográficas | Alta | D | `citation_no_author_year` | — | US-12 |
| RE-44 | Mínimo de referencias: corto 7 · original 15 · revisión 25 | Alta | D | `references_min_count` | corto 7; original 15; revision 25 (por tipo) | US-13 |
| RE-45 | Cada entrada cumple el patrón IEEE de su tipo (iniciales + apellido, título entre comillas, fuente en cursiva, vol./no./pp., año; "[Online]. Available: URL [Accessed: fecha]" para web) | Alta | D/L | `reference_ieee_pattern` | umbral_llm: 0,6 | US-13 |
| RE-46 | Correspondencia total: toda referencia está citada y toda cita tiene referencia | Alta | D | `citation_reference_match` | — | US-13 |
| RE-47 | La lista de referencias sigue el orden de citación (no alfabético) | Media | D | `references_citation_order` | max_evidencia: 5 | US-13 |
| RE-48 | URL o DOI cuando exista | Baja | D | `reference_has_url_doi` | tipos: articulo, conferencia | US-13 |
| RE-49 | Sección "Información sobre las Referencias" de la plantilla eliminada (texto de ejemplo residual) | Media | D | `template_references_residue` | frases: Información sobre las Referencias | US-13 |
| RE-60 | Cuerpo en Times New Roman 11 pt | Baja | D | `body_font` | fuente: Times New Roman; tamano_pt: 11; proporcion_min: 0,9 | US-36 |
| RE-61 | Interlineado 1,5 y línea en blanco entre párrafos/secciones | Baja | D | `line_spacing` | interlineado: 1,5; tolerancia: 0,1 | US-36 |
| RE-62 | Papel carta 21,59 × 27,94 cm | Baja | D | `paper_size` | ancho_pt: 612; alto_pt: 792; tolerancia_pt: 2 | US-36 |
| RE-63 | Márgenes: superior/inferior 3,81 cm; izquierdo 2 cm; derecho 1,2 cm | Baja | D | `page_margins` | sup/inf 3,81 cm; izq 2 cm; der 1,2 cm; tolerancia 0,2 cm | US-36 |
| RE-64 | Páginas numeradas en esquina inferior derecha | Baja | D | `page_numbering` | posicion: inferior derecha; proporcion_paginas: 0,8 | US-36 |
| RE-65 | Sistema Internacional de Unidades y coma decimal | Baja | L | `si_units_decimal_comma` | — | US-36 (coma decimal D; SI con L) |
| RE-66 | Texto de instrucciones de la plantilla no eliminado (p. ej. "Los párrafos se escribirán en Times New Roman…", "Nombre y apellidos 1") | Media | D | `template_instructions_residue` | frases: lista extraída de las plantillas | US-14 |

## 12. Versión del conjunto de reglas

- Al cargar, el motor calcula `rules_hash = sha256` del contenido normalizado (YAML parseado y serializado en JSON con claves ordenadas) de todos los archivos activos.
- `rules_hash` se guarda en cada `run` (US-28). Así se sabe con qué versión de reglas se produjo cada hallazgo.
- `GET /rules` devuelve `rules_hash`, las reglas activas y las `not_implemented`.

## 13. Ciclo de cambio de una regla

1. Abrir un pull request que modifique `rules/innosoft/*.yaml` (y `actualizado`).
2. La CI valida el esquema y ejecuta las pruebas de la regla (§14).
3. El otro developer revisa; si cambia el sentido de la regla, se actualiza también el catálogo de requisitos.
4. Tras el merge: redespliegue o recarga en caliente con `POST /admin/rules/reload` (US-30).

## 14. Pruebas obligatorias por regla

- Cada regla implementada tiene al menos **un caso positivo** (cumple, sin hallazgo) y **un caso negativo** (incumple, con hallazgo) en `tests/rules/test_RE-nn.py`.
- Las pruebas del loader cubren: archivo válido, regla sin `id`, `id` duplicado, categoría inconsistente, evaluador inexistente, marcador de mensaje desconocido, parámetro requerido ausente.
- Una prueba de CI recorre todas las reglas del YAML y falla si alguna regla `activa` y `D` no tiene archivo de prueba.

## 15. Preguntas abiertas

- [ ] RE-13: cómo se declara la temática en los PDFs generados desde Word.
- [ ] RE-26 y RE-65: ¿se evaluarán con LLM en el MVP o quedan como informativas?
- [ ] URL exacta de cada apartado de las directrices para completar `fuente.referencia`.

## Historial de cambios

| Versión | Fecha | Autor | Cambio |
|---|---|---|---|
| 0.1 | 2026-09-29 | Equipo | Borrador inicial: estructura de archivos, campos, JSON Schema, marcadores, formato del hallazgo y catálogo de evaluadores. |
| 1.0 | 2026-09-29 | Dev A, Dev B | Aprobada. Incorpora D-02 (RE-22 se implementa en US-35) y D-03 (supuesto de RE-20). |
