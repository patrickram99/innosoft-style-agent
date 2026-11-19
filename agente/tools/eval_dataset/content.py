"""Text bank for the synthetic manuscripts, written once by Gemini (Vertex AI) and versioned as JSON.

The bank only varies the wording of the documents; it never decides which defects a document has. All
articles are fictitious: no real authors, institutions or references, so no personal data is involved.
"""
from __future__ import annotations

import json
import os

from pydantic import BaseModel, Field

from tools.eval_dataset import CONTENT_BANK

DEFAULT_MODEL = "gemini-2.5-flash"
BATCH = 6  # articles per call: keeps each JSON answer well below the output limit
MAX_TOKENS = 400_000  # hard budget guard for the whole bank: about 1 USD with gemini-2.5-flash (D-06)
MAX_ATTEMPTS = 4  # per area, with a growing pause when Vertex AI answers 429 (quota per minute)
AREAS = [
    "ingeniería de software y calidad de software",
    "aprendizaje automático y visión por computador",
    "sistemas de información, bases de datos y gobierno digital",
    "redes, computación en la nube e Internet de las cosas",
    "interacción humano-computador y tecnología educativa",
]

PROMPT = """Escribe {n} artículos científicos FICTICIOS en español, del área de {area}, para probar un
verificador de formato editorial. Reglas:
- Todo es inventado: no uses nombres de personas reales, universidades reales ni referencias reales.
- Texto plano, sin Markdown, sin LaTeX, sin comillas tipográficas, sin los caracteres % & $ # _ {{ }} ~ ^ \\.
- No menciones figuras, tablas ni citas dentro de los párrafos (se insertan después).
- Cada párrafo tiene entre 70 y 110 palabras, en registro académico.
- titulo: máximo 15 palabras. titulo_en: su traducción al inglés.
- resumen: un párrafo de 120 a 160 palabras. palabras_clave: 4 términos.
- introduccion, metodos, resultados: 3 párrafos cada una. conclusiones: 2 párrafos.
- figuras: 6 títulos breves de figuras plausibles para el artículo (sin la palabra Figura ni número).
- referencias: 8 referencias ficticias en formato IEEE, sin numeración, con autores de iniciales y apellidos inventados.
"""


class Article(BaseModel):
    titulo: str
    titulo_en: str
    resumen: str
    palabras_clave: list[str]
    introduccion: list[str]
    metodos: list[str]
    resultados: list[str]
    conclusiones: list[str]
    figuras: list[str] = Field(min_length=4)
    referencias: list[str] = Field(min_length=4)


class Batch(BaseModel):
    articulos: list[Article]


def configure_vertex() -> str:
    """Same convention as tools/spec_review: Vertex AI with the local gcloud credentials (D-06)."""
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "true")
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
    if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
        import google.auth

        _, project = google.auth.default()
        if not project:
            raise SystemExit("Define GOOGLE_CLOUD_PROJECT o ejecuta: gcloud auth application-default set-quota-project <proyecto>")
        os.environ["GOOGLE_CLOUD_PROJECT"] = project
    return os.environ["GOOGLE_CLOUD_PROJECT"]


def build_bank(model: str = DEFAULT_MODEL, per_area: int = BATCH) -> dict:
    import time

    from google import genai
    from google.genai import errors as genai_errors
    from google.genai import types

    project = configure_vertex()
    client = genai.Client()
    # The bank is saved after every area and resumed on the next run, so a quota error never loses paid work.
    bank = json.loads(CONTENT_BANK.read_text(encoding="utf-8")) if CONTENT_BANK.exists() else {"tokens": 0, "articulos": []}
    bank.update({"modelo": model, "proyecto": project})
    done = {a["area"] for a in bank["articulos"]}
    for area in AREAS:
        if area in done:
            continue
        if bank["tokens"] >= MAX_TOKENS:
            raise SystemExit(f"Tope de {MAX_TOKENS} tokens alcanzado ({bank['tokens']}); no se llama más a Gemini.")
        config = types.GenerateContentConfig(temperature=0.9, max_output_tokens=32768, response_mime_type="application/json", response_schema=Batch)
        for attempt in range(MAX_ATTEMPTS):
            try:
                response = client.models.generate_content(model=model, contents=PROMPT.format(n=per_area, area=area), config=config)
                break
            except genai_errors.ClientError as exc:
                if exc.code != 429 or attempt == MAX_ATTEMPTS - 1:
                    raise
                wait = 60 * (attempt + 1)
                print(f"{area}: cuota agotada (429), reintento en {wait} s", flush=True)
                time.sleep(wait)
        batch = Batch.model_validate_json(response.text)
        bank["tokens"] += response.usage_metadata.total_token_count or 0
        bank["articulos"] += [{"area": area, **article.model_dump()} for article in batch.articulos]
        CONTENT_BANK.write_text(json.dumps(bank, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print(f"{area}: {len(batch.articulos)} artículos", flush=True)
    print(f"{len(bank['articulos'])} artículos, {bank['tokens']} tokens → {CONTENT_BANK.name}")
    return bank


def load_bank() -> list[dict]:
    if not CONTENT_BANK.exists():
        raise SystemExit("Falta contenido.json: ejecuta  python -m tools.eval_dataset contenido")
    return json.loads(CONTENT_BANK.read_text(encoding="utf-8"))["articulos"]
