# Revisor multiagente de specs

Herramienta del proceso (decisión D-07 de [`specs/00-producto.md`](../../specs/00-producto.md) §17). Revisa una spec de
historia antes de implementarla. No forma parte del producto: `app/` no la importa y el CI no la ejecuta.

## Cómo funciona

Está hecha con Google ADK sobre Gemini en Vertex AI. Tres revisores leen la misma spec en paralelo y un coordinador
une sus dictámenes en un veredicto.

| Agente | Qué revisa |
|---|---|
| `revisor_consistencia` | Contradicciones con `00-producto.md` (endpoints, estados, modelo de datos, decisiones), con las specs de `depende_de` y dentro de la propia spec. |
| `revisor_testabilidad` | Que cada criterio de aceptación (§8) y cada excepción tenga un caso en el plan de pruebas (§9) ejecutable en local. |
| `revisor_alcance` | Que las reglas RE-nn citadas coincidan con el catálogo, que los umbrales vivan en YAML y que no se exceda el alcance MVP. |
| `coordinador` | Une duplicados, fija la severidad y emite el veredicto: `favorable`, `con_observaciones` o `bloqueante`. |

Cada revisor recibe la spec en revisión, `00-producto.md`, las specs de las que depende, las líneas del catálogo de las
reglas citadas y los YAML de `rules/innosoft/`. Nunca lee `muestras/` (el código lo impide).

## Uso (PowerShell, desde `agente/`)

```powershell
pip install -r requirements-tools.txt
gcloud auth application-default login          # una vez por equipo
python -m tools.spec_review US-05 US-07        # escribe specs/revisiones/US-nn.md
python -m tools.spec_review US-05 --aplicar    # si el veredicto es favorable, la spec pasa a "Revisada (IA)"
```

Variables opcionales: `GOOGLE_CLOUD_PROJECT` (por defecto, el proyecto de las credenciales locales),
`GOOGLE_CLOUD_LOCATION` (`global`) y `SPEC_REVIEW_MODEL` (`gemini-2.5-flash`).

## Qué hacer con el veredicto

- **Favorable:** con `--aplicar` la spec pasa a `Revisada (IA)` y se puede implementar. El equipo la ratifica después.
- **Con observaciones o bloqueante:** se corrige la spec (con su fila en el historial de cambios) y se vuelve a revisar.
  Las correcciones que cambian el comportamiento son decisiones del equipo, no del revisor.

## Costo

Una revisión consume entre 60 000 y 70 000 tokens con `gemini-2.5-flash`. El presupuesto del proyecto es de 10 USD al
mes (D-06) y tiene una alerta en la cuenta de facturación; la alerta avisa, no corta el gasto. Por eso cada ejecución
acepta como máximo 8 specs.
