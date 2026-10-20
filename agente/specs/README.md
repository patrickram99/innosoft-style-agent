# Especificaciones de historias de usuario

Agente de sugerencias estilísticas para la revista *Innovación y Software* (Innosoft).

Cada historia tiene su especificación en `specs/US-nn.md` **antes** de implementarse, siguiendo el ciclo Spec-Driven Development del Capítulo III: *Especificar → Revisar → Planificar → Implementar → Verificar → Cerrar*.

Documentos base: `catalogo_requisitos_innosoft.md` (v1.0) y `priorizacion_rice_sprint1.xlsx`. Plantilla para nuevas specs: [`_template.md`](_template.md).

## Specs transversales

| Documento | Contenido |
|---|---|
| [`00-producto.md`](00-producto.md) | **Aprobada (v1.0).** Spec general: objetivo, alcance, actores, arquitectura, estados, API canónica, modelo de datos, RNF y ALT. Prevalece sobre las specs de historia. |
| [`formato-reglas.md`](formato-reglas.md) | **Aprobada (v1.0).** Contrato de las reglas YAML: campos, JSON Schema, marcadores, formato del hallazgo y catálogo de evaluadores RE-01..RE-66. |

## Índice

| ID | Historia | Épica | Release | Sprint | RICE | ★ | Estado spec |
|---|---|---|---|---|---|---|---|
| [US-00](US-00.md) | Especificación general del producto y configuración del entorno | Transversal (historia técnica) | R1 | 2 | — |  | **Aprobada** |
| [US-01](US-01.md) | Recibir PDF por API | A. Recepción del envío | R1 | 2 | 600 | ★ | **Aprobada** |
| [US-02](US-02.md) | Plugin OJS: hook al completar un envío | A. Recepción del envío | R1 | 5 | 75 |  | Borrador |
| [US-03](US-03.md) | Obtener metadatos del envío (sección, título, idioma) | A. Recepción del envío | R1 | 3 | 160 |  | Borrador |
| [US-04](US-04.md) | Extraer texto y páginas | B. Extracción documental | R1 | 2 | 600 | ★ | **Aprobada** |
| [US-05](US-05.md) | Detectar secciones IMRyD | B. Extracción documental | R1 | 3 | 100 | ★ | Borrador |
| [US-06](US-06.md) | Extraer figuras: posición, tamaño y pie | B. Extracción documental | R1 | 2 | 216 | ★ | **Aprobada** |
| [US-07](US-07.md) | Extraer citas en texto [n] | B. Extracción documental | R1 | 3 | 320 | ★ | Borrador |
| [US-08](US-08.md) | Extraer lista de referencias | B. Extracción documental | R1 | 3 | 160 | ★ | Borrador |
| [US-09](US-09.md) | Cargar reglas Innosoft desde YAML | C. Motor de validación | R1 | 2 | 600 | ★ | **Aprobada** |
| [US-10](US-10.md) | Validar figuras: tamaño y proporción | C. Motor de validación | R1 | 2 | 216 | ★ | **Aprobada** |
| [US-11](US-11.md) | Validar figuras: pie, numeración y orden | C. Motor de validación | R1 | 3 | 112 |  | Borrador |
| [US-12](US-12.md) | Validar citas IEEE en el texto | C. Motor de validación | R1 | 3 | 256 | ★ | Borrador |
| [US-13](US-13.md) | Validar referencias IEEE (formato, orden y mínimo) | C. Motor de validación | R1 | 3 | 80 | ★ | Borrador |
| [US-14](US-14.md) | Validar estructura, resumen y palabras clave | C. Motor de validación | R2 | — | 30 |  | Borrador |
| [US-15](US-15.md) | Redactar sugerencia con Gemini | D. Generación de sugerencias | R1 | 4 | 160 | ★ | Borrador |
| [US-16](US-16.md) | Validar el esquema de respuesta del LLM | D. Generación de sugerencias | R1 | 4 | 400 | ★ | Borrador |
| [US-17](US-17.md) | Anonimizar el contexto antes de enviarlo al LLM | D. Generación de sugerencias | R1 | 4 | 320 |  | Borrador |
| [US-18](US-18.md) | Reintentos, límite de tokens y fallback determinístico | D. Generación de sugerencias | R1 | 4 | 96 |  | Borrador |
| [US-19](US-19.md) | Ver cola de manuscritos pendientes | E. Revisión editorial | R1 | 4 | 200 | ★ | Borrador |
| [US-20](US-20.md) | Ver sugerencias con su evidencia | E. Revisión editorial | R1 | 4 | 160 | ★ | Borrador |
| [US-21](US-21.md) | Aceptar, rechazar o editar cada sugerencia | E. Revisión editorial | R1 | 5 | 160 | ★ | Borrador |
| [US-22](US-22.md) | Agregar una sugerencia manual | E. Revisión editorial | R2 | — | 64 |  | Borrador |
| [US-23](US-23.md) | Marcar manuscrito como "sin observaciones" | E. Revisión editorial | R2 | — | 40 |  | Borrador |
| [US-24](US-24.md) | Publicar comentario en la discusión del envío | F. Publicación en OJS | R1 | 5 | 160 | ★ | Borrador |
| [US-25](US-25.md) | Reintento y cola si OJS no responde | F. Publicación en OJS | R2 | — | 16 |  | Borrador |
| [US-26](US-26.md) | Vincular el comentario a la versión del manuscrito | F. Publicación en OJS | R2 | — | 50 |  | Borrador |
| [US-27](US-27.md) | Notificar al editor por correo de OJS | F. Publicación en OJS | R2 | — | 80 |  | Borrador |
| [US-28](US-28.md) | Registro de ejecución por manuscrito | G. Administración y observabilidad | R1 | 4 | 200 | ★ | Borrador |
| [US-29](US-29.md) | Registro de consumo y latencia de Gemini | G. Administración y observabilidad | R2 | — | 200 |  | Borrador |
| [US-30](US-30.md) | Editar reglas sin redespliegue | G. Administración y observabilidad | R2 | — | 40 |  | Borrador |
| [US-31](US-31.md) | Detectar reenvío (versión 2 del manuscrito) | A. Recepción del envío | R2 | — | 25 |  | Borrador |
| [US-32](US-32.md) | Panel de métricas | G. Administración y observabilidad | R3 | — | 26,7 |  | Borrador |
| [US-33](US-33.md) | Auditoría de decisiones editoriales | G. Administración y observabilidad | R3 | — | 50 |  | Borrador |
| [US-34](US-34.md) | Detectar tablas y sus títulos | B. Extracción documental | R3 | — | 15 |  | Borrador |
| [US-35](US-35.md) | Detectar figuras recortadas o fuera de margen | B. Extracción documental | R3 | — | 20 |  | Borrador |
| [US-36](US-36.md) | Validar formato de página (fuente, márgenes, numeración) | C. Motor de validación | R3 | — | 6,7 |  | Borrador |

★ = walking skeleton (flujo mínimo de punta a punta).

## Estados de una spec

| Estado | Significado |
|---|---|
| Borrador | Redactada, pendiente de revisión cruzada. |
| En revisión | El otro developer la está revisando (comentarios en el PR de la spec). |
| Aprobada | Lista para implementar; cambios posteriores requieren nueva versión. |
| Implementada | Código fusionado en `main`. |
| Verificada | Pruebas en verde y comportamiento idéntico a la spec (Definition of Done). |

## Convenciones

- `US-nn` historia · `RE-nn` regla editorial · `RNF-nn` requisito no funcional · `ALT-nn` flujo alternativo · `AC` criterio de aceptación.
- Los umbrales de las reglas viven en `rules/innosoft/*.yaml`; las specs los citan pero el código no los contiene.
- Todo hallazgo tiene la forma `{rule_id, severidad, página, ubicación, evidencia, valor_encontrado, valor_esperado}`.
- Todo cambio de spec se hace por pull request y actualiza el historial de cambios de la propia spec.
