"""ADK agents: three reviewers run in parallel over the same spec and a coordinator merges their findings."""
from __future__ import annotations

from typing import Literal

from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from google.genai import types
from pydantic import BaseModel, Field

COMMON = """Eres un revisor de especificaciones de software (Spec-Driven Development) de un agente que revisa el estilo de
manuscritos PDF para una revista académica. Recibirás la spec de una historia de usuario y su contexto: la spec de
producto (que prevalece), las specs de las que depende, las reglas del catálogo que cita y las reglas ya declaradas en YAML.

Reglas de trabajo:
- Revisa solo la spec marcada como SPEC EN REVISIÓN. El resto es contexto.
- Cita la sección de la spec en cada observación (por ejemplo, "§6.2" o "§8 AC-03").
- Clasifica cada observación como BLOQUEANTE (impide implementar sin adivinar o contradice la spec de producto),
  MAYOR (conviene corregir antes de implementar) o MENOR (redacción, detalle).
- No inventes requisitos nuevos ni amplíes el alcance. Si algo no está decidido, señálalo como pregunta abierta.
- No elogies ni resumas la spec: lista solo problemas. Si no encuentras ninguno en tu dimensión, dilo en una línea.
- Responde en español, con una lista numerada de observaciones, como máximo 10, de la más grave a la menos grave.
"""

CONSISTENCY = COMMON + """
Tu dimensión es la CONSISTENCIA:
- Contradicciones con la spec de producto: nombres de endpoints (§8.3), estados (§7), campos del modelo de datos (§8.4),
  formato del hallazgo, decisiones vigentes (§17) y requisitos no funcionales.
- Contradicciones con las specs de las que depende: entradas que esta historia espera y que la dependencia no produce.
- Contradicciones internas entre las secciones de la propia spec.
- La decisión D-05: hasta diciembre de 2026 el agente es headless. Si la spec es de la Fase 1, no puede exigir OJS,
  plugin ni interfaz de editor para funcionar.
"""

TESTABILITY = COMMON + """
Tu dimensión es la TESTABILIDAD:
- Cada criterio de aceptación (§8) debe ser verificable, con entrada y resultado esperado concretos, y tener al menos un
  caso en el plan de pruebas (§9). Señala los criterios sin caso y los casos sin criterio.
- Cada excepción o flujo alternativo descrito debe tener un caso de prueba.
- Los casos deben poder ejecutarse en local con PDFs sintéticos y dobles de prueba (sin OJS real, sin llamar a Gemini,
  sin manuscritos reales).
- Ambigüedades que obligarían a quien implementa a adivinar: umbrales sin valor, formatos sin ejemplo, "etc.".
"""

SCOPE = COMMON + """
Tu dimensión es el ALCANCE Y LAS REGLAS EDITORIALES:
- Cada regla RE-nn citada debe existir en el catálogo y describirse igual que en él; señala las que faltan o difieren.
- Los umbrales y mensajes de las reglas deben vivir en YAML (RNF-05): la spec no debe fijar en el código ningún número
  de una regla editorial.
- Alcance: señala lo que excede el alcance MVP declarado para la historia y las dependencias no declaradas en `depende_de`.
- Datos personales (Ley N.º 29733): nada de manuscritos reales en pruebas, logs o prompts; a Gemini solo llega el
  fragmento anonimizado.
"""

COORDINATOR = """Eres el coordinador de una revisión de especificaciones. Tres revisores analizaron la misma spec y
dejaron sus dictámenes:

## Dictamen de consistencia
{consistencia}

## Dictamen de testabilidad
{testabilidad}

## Dictamen de alcance y reglas
{alcance}

Consolida los tres dictámenes en un único resultado:
- Une las observaciones duplicadas y descarta las que no señalen un problema concreto de la spec.
- Conserva la severidad más alta cuando dos revisores difieran. Usa solo: bloqueante, mayor, menor.
- Para cada observación propone la corrección mínima de la spec, sin ampliar el alcance.
- Veredicto: "bloqueante" si queda al menos una observación bloqueante; "con_observaciones" si quedan mayores pero
  ninguna bloqueante; "favorable" si solo quedan menores o ninguna.
- Como máximo 10 observaciones, cada una en una o dos frases.
- El resumen son dos o tres frases en español para el equipo.
"""


class Observation(BaseModel):
    severidad: Literal["bloqueante", "mayor", "menor"]
    seccion: str = Field(description="Sección de la spec, por ejemplo '§8 AC-03'")
    descripcion: str
    correccion: str = Field(description="Corrección mínima propuesta para la spec")


class Verdict(BaseModel):
    veredicto: Literal["favorable", "con_observaciones", "bloqueante"]
    resumen: str
    observaciones: list[Observation]


def build_pipeline(model: str, max_output_tokens: int = 4096) -> SequentialAgent:
    config = types.GenerateContentConfig(temperature=0.2, max_output_tokens=max_output_tokens)

    def reviewer(name: str, instruction: str, key: str) -> LlmAgent:
        return LlmAgent(name=name, model=model, instruction=instruction, output_key=key, generate_content_config=config)

    reviewers = ParallelAgent(
        name="revisores",
        sub_agents=[
            reviewer("revisor_consistencia", CONSISTENCY, "consistencia"),
            reviewer("revisor_testabilidad", TESTABILITY, "testabilidad"),
            reviewer("revisor_alcance", SCOPE, "alcance"),
        ],
    )
    coordinator = LlmAgent(
        name="coordinador",
        model=model,
        instruction=COORDINATOR,
        include_contents="none",  # works from the three reviews in state, not from the full spec again
        output_schema=Verdict,
        output_key="veredicto",
        # The model's reasoning counts against this limit: a low value truncates the JSON verdict.
        generate_content_config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=4 * max_output_tokens),
    )
    return SequentialAgent(name="revision_de_spec", sub_agents=[reviewers, coordinator])
