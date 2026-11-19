# Dataset sintético de evaluación

Herramienta del proceso (decisión D-09 de [`specs/00-producto.md`](../../specs/00-producto.md) §17). Genera manuscritos
con defectos conocidos, ejecuta el agente sobre ellos por su API y calcula precisión, *recall* y F1 por regla. No forma
parte del producto: `app/` no la importa y el CI no la ejecuta.

## Por qué sintético

No hay un corpus de manuscritos reales anotado ni autorización para usar los de `muestras/`. En un dataset sintético la
verdad de referencia se conoce por construcción (cada defecto lo inyecta el generador) y no hay datos personales:
autores, afiliaciones y referencias son ficticios.

## Cómo funciona

| Paso | Módulo | Qué hace |
|---|---|---|
| Textos | `content.py` | Gemini (Vertex AI, D-06) redacta 30 artículos ficticios y los guarda en `contenido.json`. Solo varía la redacción; no decide ningún defecto. Se ejecuta una vez y el resultado se versiona. |
| Diseño | `design.py` | A partir de una semilla decide cada documento: perfil (20 % conforme, 50 % con un defecto, 30 % con varios), figuras, tamaño en píxeles, resolución y variante. Los umbrales salen de `rules/innosoft/figuras.yaml`. |
| Generación | `gen_latex.py`, `gen_word.py` | Escribe cada manuscrito con las plantillas oficiales de la revista (`docs/plantillas/`) y lo convierte a PDF con pdfLaTeX o con Microsoft Word. La página de cada figura la informan LaTeX (`.aux`) y Word. |
| Verificación | `verify.py` | Lee con pypdf las imágenes guardadas en cada PDF y fija la verdad de referencia sobre el PDF. |
| Evaluación | `evaluate.py` | Envía cada PDF por `POST /manuscripts`, lee `GET /manuscripts/{id}/findings` y clasifica cada par (figura, regla) como VP, FP, FN o VN. |
| Informe | `report.py`, `stats.py` | Métricas por regla con intervalos de Wilson al 95 %, prueba binomial exacta contra las metas, prueba exacta de Fisher entre generadores, tiempos y gráficos. |

### Variantes de figura

`png`, `jpeg` y `png_alfa` (con canal de transparencia) en los dos generadores. Solo en LaTeX: `recortada` (la imagen
incrustada es más ancha que la parte visible), `rotada` (la imagen se guarda de lado y se gira 90°) y `vectorial`
(TikZ; las reglas de píxeles y resolución no le aplican). El manifiesto registra además defectos de reglas que aún no
tienen evaluador (pie de figura, numeración y mención en el texto) para reutilizar el dataset cuando se implementen.

### Verdad de referencia y circularidad

El generador nunca importa `app/` ni usa PyMuPDF. La verdad se define con lo que el autor hizo (píxeles visibles y
tamaño impreso) y se comprueba con pypdf, una librería distinta de la que usa el agente.

Word remuestrea las imágenes a unos 200 ppp al exportar a PDF, aunque el documento tenga activada la opción de no
comprimir imágenes. Como el agente recibe el PDF, la verdad (`truth`) se fija sobre lo que el PDF contiene; lo que el
autor incrustó queda en `truth_source` y permite medir cuántas figuras conformes en origen dejan de serlo al convertir.

## Uso (PowerShell, desde `agente/`)

```powershell
pip install -r requirements-tools.txt
python -m tools.eval_dataset contenido     # una vez; requiere: gcloud auth application-default login
python -m tools.eval_dataset todo --tesis  # generar + evaluar + informe, y copia los gráficos a Tesis-Doc
```

Requisitos: MiKTeX (pdfLaTeX) y Microsoft Word. Opciones: `--latex 140`, `--word 60`, `--semilla`, `--repeticiones 3`
(envíos por documento; el tiempo que se informa es la mediana).

### Parar y continuar

La corrida completa tarda unos diez minutos y se puede detener con `Ctrl+C` en cualquier momento. Al volver a ejecutar
el mismo comando continúa donde quedó:

- **Generación:** trabaja en tandas (`--lote 20`). Cada documento terminado deja una ficha en `evaluacion/dataset/meta/`
  con la huella de su plan; se salta si el plan no cambió y su PDF sigue ahí. Como mucho se repite la tanda en curso.
- **Evaluación:** cada documento evaluado se guarda en `evaluacion/dataset/eval/`. La clave incluye el PDF, la verdad
  de referencia, el YAML de reglas y el código de `app/`: si el agente o las reglas cambian, se vuelve a evaluar todo.
- `--limpiar` descarta el avance y empieza de cero.

## Salidas

| Ruta | Versionada | Contenido |
|---|---|---|
| `evaluacion/manifest.json` | sí | Plan y verdad de referencia de cada documento y figura. |
| `evaluacion/resultados/detalle.csv` | sí | Una fila por (figura, regla) con su resultado. |
| `evaluacion/resultados/documentos.csv` | sí | Páginas, figuras, estado y tiempo de análisis por documento. |
| `evaluacion/resultados/resumen.json` | sí | Métricas, intervalos, pruebas y lista de errores. |
| `evaluacion/resultados/figuras/` | sí | Gráficos (copiados a `Tesis-Doc/figuras/resultados/` con `--tesis`). |
| `evaluacion/dataset/` | no | PDFs y archivos de compilación; se regeneran con la semilla. |

La misma semilla produce el mismo plan y la misma verdad de referencia. Los PDFs no salen idénticos byte a byte porque
LaTeX y Word escriben fechas de creación.

## Límites

- Mide la corrección del agente frente a defectos controlados, no su desempeño con manuscritos reales. La evaluación
  con editores y manuscritos reales es de la Fase 2 (D-05).
- Solo se evalúan las reglas que tienen evaluador (`RULES` en `evaluate.py`). Al implementar una regla nueva se añade
  ahí y, si hace falta, su defecto en `design.py`.
- El tiempo de análisis se mide en proceso, sin red ni cola; es el tiempo del análisis, no el de un despliegue.

## Costo

El banco de textos consume unos 80 000 tokens de `gemini-2.5-flash`, una sola vez. Si Vertex AI responde 429 por cuota
por minuto, el comando espera y reintenta; lo ya generado queda guardado y no se vuelve a pedir.
