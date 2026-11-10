# Tesis-Doc — informe de tesis en LaTeX

Proyecto LaTeX del informe *Agente de IA de sugerencias estilísticas integrado con Open Journal Systems para el formateo
de artículos científicos dirigido a journals latinoamericanos*. Las reglas de edición están en `CLAUDE.md`.

## Compilar (Windows, MiKTeX)

```powershell
winget install MiKTeX.MiKTeX      # una sola vez; aceptar la instalación automática de paquetes
.\compilar.ps1 -Abrir            # deja build\main.pdf
```

El PDF queda en `build/main.pdf` (`build/` está ignorada por git). Claude también puede compilar desde su shell Linux
sobre este equipo para verificar (ver `CLAUDE.md`), pero ese PDF no lleva las fuentes de la clase.

Verificación de referencia: el 30-oct-2026 el proyecto compiló con pdfLaTeX (MiKTeX) sin errores ni referencias sin
resolver, en tres pasadas directas de `pdflatex`.

## Esquema oficial ↔ archivos

| Esquema de la universidad (`plantilla/esquema-informe-tecnologico.docx`) | Archivo |
|---|---|
| Portada, dedicatoria, agradecimientos, índices, siglas, resumen, abstract, palabras clave | `main.tex` (portada) + `capitulos/00-preliminares.tex` |
| Capítulo I – Problemática del proyecto | `capitulos/01-problematica.tex` |
| Capítulo II – Planteamiento del proyecto (el esquema lo numera "III" por error) | `capitulos/02-planteamiento.tex` |
| Capítulo III – Metodología de desarrollo | `capitulos/03-metodologia.tex` |
| Conclusiones | `capitulos/04-conclusiones.tex` |
| Referencias | `capitulos/referencias.tex` |
| Anexos | `anexos/A-fichas-lectura.tex`, `anexos/B-matriz-trazabilidad.tex` |

## Registro de sincronización

El borrador original (`Tesis2026.pdf`, Google Docs, 63 páginas) se convirtió a esta carpeta el 19-oct-2026 y se
sincronizó con el estado del proyecto (specs SDD v1.0, Sprint 3). Criterio: ante una contradicción entre el borrador y
el trabajo actual (specs, catálogo, Excel RICE), **prevalece el trabajo actual**.

| ID | Tema | Borrador original | Versión sincronizada |
|---|---|---|---|
| S-01 | Alcance de revistas | Innosoft y RICCE | Solo Innosoft como caso de estudio; RICCE pasa a trabajo futuro (limitación geográfica). Decidido por el equipo el 19-oct. |
| S-02 | Estructura | "Planteamiento del Proyecto", "Propuesta de solución", "Revisión y fundamentación teórica", "Alcance y metodología" | Reorganizado según el esquema oficial: antecedentes → Cap. I; fundamentos, objetivos, justificación, viabilidad y limitaciones → Cap. II; propuesta, alcance, cronograma y recursos → Cap. III. |
| S-03 | Metodología | Iterativa e incremental con Kanban "como apoyo" | Scrum (sprints de 2 semanas) + RICE + Spec-Driven Development (00-producto §14). La cita de Kanban (`ref29`) queda sin uso. |
| S-04 | Stack | "FastAPI o Flask", "PostgreSQL o MySQL", "cloud o serverless" | FastAPI, PostgreSQL 16, Docker Compose; BackgroundTasks y luego Celery + Redis (D-04). MySQL es solo la base de OJS. Hosting definitivo sigue abierto (00-producto §18). |
| S-05 | OE1 | "Detectar criterios estilísticos en base a plantillas docx o tex de forma automática" | Las normas (plantillas + directrices) se traducen a reglas YAML verificables y configurables; el motor detecta y el LLM solo redacta. La extracción automática de reglas desde plantillas no está especificada en ninguna historia. |
| S-06 | OE4 y evaluación | Reducción del tiempo ≥ 20 % | Métricas de 00-producto §1: precisión ≥ 0,85, recall ≥ 0,75, aceptación ≥ 70 %, análisis < 3 min. La meta de 20 % queda como `\pendiente`: no hay historia que la mida. |
| S-07 | Cronograma | 12 fases en 6 meses + Gantt (imagen) | Plan por sprints de la replanificación del 29-sep (Excel RICE) con Gantt en pgfgantt. |
| S-08 | Alcance funcional | Incluía gramática, márgenes, tipografía, tablas | Gramática general fuera de alcance; formato de página (US-36) y tablas (US-34) quedan en R3. |
| S-09 | Problema | Genérico | Se añade el caso Innosoft y sus problemas más frecuentes (figuras y referencias IEEE). |
| S-10 | Antecedentes | "24 documentos" | 24 seleccionados, de los cuales GS-13 duplica a GS-10: 23 estudios independientes. Se añade una síntesis con la brecha. |
| S-11 | Abstract y portada | Ausentes | Abstract en borrador (por revisar); grado y asesor como marcadores en `main.tex`. |
| S-12 | Formato | Google Docs | LaTeX con la clase oficial, un archivo por capítulo; numeración de tablas y figuras continua (la impone la clase). |
| S-13 | Avance en Cap. III | Cifras congeladas solo al cierre del Sprint 6 | Excepción pedida por el usuario el 30-oct: el Capítulo III lleva un corte fechado (84 casos, 96 % de cobertura medida con `pytest-cov`, instalado aparte y fuera de `requirements.txt`). Se reemplaza al cierre del Sprint 6. |
| S-14 | Diseño de pruebas | No existía | Nueva sección del Capítulo III que consolida los §8 y §9 de las specs. Registra una brecha: faltan casos en el borde exacto de RE-20, RE-21 y US-01. |
| S-15 | Plan y acceso a OJS | Plan del 29-sep; "se dispone de acceso a la revista" | Sin acceso al servidor de OJS al 30-oct: el Capítulo II se corrigió y se añadió un plan ajustado **propuesto**. Falta validarlo con el asesor y pasarlo a la hoja del Excel RICE; prevalece la tabla base mientras tanto. Se corrigió además "sobre el entorno Docker": Docker sigue sin ejecutarse. |
| S-16 | Alcance y cronograma | Todo el producto, con OJS, hasta el 04-dic-2026 | Decisión del usuario del 10-nov (D-05 de 00-producto v1.1): Fase 1 *headless* hasta el 04-dic-2026 y Fase 2 con OJS del 04-ene al 26-mar-2027. Capítulo III (plan y Gantt en dos fases, Tabla 3-16), Capítulo II y resumen actualizados. El plan de la Tabla 3-7 queda como antecedente. El título no cambia. Falta validarlo con el asesor. |
| S-17 | Revisión de especificaciones | Revisión cruzada entre los dos developers | Se añade el revisor multiagente con Google ADK (D-07) y el estado `Revisada (IA)`. El Capítulo III registra la primera revisión: US-05, US-07 y US-08 con veredicto bloqueante. |
| S-18 | Evidencia de pruebas | Solo tabla de resultados | Capturas del 10-nov en `figuras/pruebas/` (9 de `pytest-html` y `pytest-cov`, 5 del flujo *headless*). Las del flujo son respuestas reales de la API con PDFs sintéticos, presentadas en formato de consola; se regeneran con los reportes de `pytest --html` y el agente en local. |

## Pendiente de reflejar en la tesis

Lista que alimentan las tareas de código (paso 8 de `../agente/CLAUDE.md`). Vacía cuando la tesis está al día.

- (vacío)

## Observaciones del borrador por resolver

- Tabla de búsqueda: Web of Science y Scopus aparecen sin resultados ni cadena.
- Las fichas citan RQ1, RQ2 y RQ3, pero la tesis formula una sola pregunta de investigación: definir las RQ o quitar
  esas referencias.
- `ref3` (Khalifa y Albadawy) no se cita en el cuerpo; `ref29` (Kanban) quedó sin uso.
- Grado a obtener, nombre del asesor, dedicatoria y agradecimientos.
