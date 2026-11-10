"""Review story specs with a multi-agent system (Google ADK + Gemini on Vertex AI).

Usage (PowerShell, from agente/):
    python -m tools.spec_review US-05 US-07          # writes specs/revisiones/US-nn.md
    python -m tools.spec_review US-05 --aplicar      # also moves a favourable spec to `Revisada (IA)`

Environment: GOOGLE_CLOUD_PROJECT (default: project of the local gcloud credentials), GOOGLE_CLOUD_LOCATION
(default: global), SPEC_REVIEW_MODEL (default: gemini-2.5-flash). Credentials: `gcloud auth application-default login`.
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import os
import sys

from tools.spec_review import context as ctx

DEFAULT_MODEL = "gemini-2.5-flash"
MAX_SPECS_PER_RUN = 8  # budget guard (D-06): 10 USD per month


def configure_vertex() -> str:
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "true")
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
    if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
        import google.auth

        _, project = google.auth.default()
        if not project:
            raise SystemExit("Define GOOGLE_CLOUD_PROJECT o ejecuta: gcloud auth application-default set-quota-project <proyecto>")
        os.environ["GOOGLE_CLOUD_PROJECT"] = project
    return os.environ["GOOGLE_CLOUD_PROJECT"]


async def review(story_id: str, model: str) -> tuple[dict, dict[str, str], int]:
    from google.adk.runners import InMemoryRunner
    from google.genai import types

    from tools.spec_review.agents import build_pipeline

    runner = InMemoryRunner(agent=build_pipeline(model), app_name="spec_review")
    session = await runner.session_service.create_session(app_name="spec_review", user_id="equipo")
    message = types.Content(role="user", parts=[types.Part(text=ctx.build_context(story_id))])
    tokens = 0
    async for event in runner.run_async(user_id="equipo", session_id=session.id, new_message=message):
        usage = getattr(event, "usage_metadata", None)
        if usage and usage.total_token_count:
            tokens += usage.total_token_count
    session = await runner.session_service.get_session(app_name="spec_review", user_id="equipo", session_id=session.id)
    state = session.state
    verdict = state.get("veredicto")
    if isinstance(verdict, str):
        verdict = json.loads(verdict)
    if not verdict:
        raise RuntimeError(f"{story_id}: el coordinador no devolvió un veredicto")
    reviews = {k: str(state.get(k, "")) for k in ("consistencia", "testabilidad", "alcance")}
    return dict(verdict), reviews, tokens


def main() -> int:
    parser = argparse.ArgumentParser(description="Revisión multiagente de specs (D-07)")
    parser.add_argument("historias", nargs="+", help="US-05, 07, ...")
    parser.add_argument("--aplicar", action="store_true", help="pasa a 'Revisada (IA)' las specs con veredicto favorable")
    parser.add_argument("--modelo", default=os.environ.get("SPEC_REVIEW_MODEL", DEFAULT_MODEL))
    args = parser.parse_args()

    ids = [ctx.normalize_id(h) for h in args.historias]
    if len(ids) > MAX_SPECS_PER_RUN:
        print(f"Máximo {MAX_SPECS_PER_RUN} specs por ejecución (presupuesto D-06).", file=sys.stderr)
        return 2
    project = configure_vertex()
    print(f"Proyecto {project} · modelo {args.modelo}")
    ctx.REVIEWS.mkdir(exist_ok=True)
    today = dt.date.today()
    total = 0
    failed = []
    for story_id in ids:
        try:
            verdict, reviews, tokens = asyncio.run(review(story_id, args.modelo))
        except Exception as exc:  # noqa: BLE001 - one failed review must not hide the others
            failed.append(story_id)
            print(f"{story_id}: ERROR, sin informe ({type(exc).__name__}: {str(exc)[:200]})", file=sys.stderr)
            continue
        total += tokens
        report = ctx.render_report(story_id, verdict, reviews, args.modelo, tokens, today)
        (ctx.REVIEWS / f"{story_id}.md").write_text(report, encoding="utf-8", newline="\n")
        counts = {s: sum(1 for o in verdict["observaciones"] if o["severidad"] == s) for s in ("bloqueante", "mayor", "menor")}
        line = f"{story_id}: {verdict['veredicto']} · {counts['bloqueante']} bloqueantes, {counts['mayor']} mayores, {counts['menor']} menores · {tokens} tokens"
        if args.aplicar and verdict["veredicto"] == "favorable" and ctx.mark_reviewed(story_id, today):
            line += f" · estado → {ctx.REVIEWED_STATE}"
        print(line)
    print(f"Total: {total} tokens. Informes en specs/revisiones/")
    if failed:
        print(f"Sin revisar por error: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
