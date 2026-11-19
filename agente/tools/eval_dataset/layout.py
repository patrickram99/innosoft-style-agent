"""Order of the blocks of a synthetic manuscript, shared by the LaTeX and the Word generators."""
from __future__ import annotations

import random
from dataclasses import dataclass

from tools.eval_dataset.design import DocPlan, FigurePlan

ARTICLE_TYPE_LABEL = {"corto": "Artículos cortos", "original": "Artículos originales", "revision": "Artículos de revisión"}
SECTION_ID = {"corto": 1, "original": 2, "revision": 3}
VAGUE = ["como se muestra en la siguiente imagen", "tal como se aprecia en la figura de abajo"]
AUTHORS = "Autor Uno, Autora Dos, Autor Tres"
AFFILIATION = "Universidad Ficticia, Facultad de Ingeniería, Ciudad Ejemplo, País Ejemplo. autor@example.org"


@dataclass
class Block:
    kind: str  # heading | paragraph | figure | reference
    text: str = ""
    figure: FigurePlan | None = None


def clean(text: str) -> str:
    """Plain text only: the bank is asked not to use these characters, this is the safety net."""
    for ch in "\\{}$&#_%~^":
        text = text.replace(ch, " ")
    return " ".join(text.replace("'", "").replace("`", "").split())


def figure_title(fig: FigurePlan, article: dict) -> str:
    titles = article["figuras"]
    return clean(titles[(fig.order - 1) % len(titles)]).rstrip(".")


def mention(fig: FigurePlan) -> str:
    if fig.referenced and fig.printed_number is not None:
        return f"Los valores obtenidos se resumen en la Figura {fig.printed_number}, que acompaña a este apartado."
    return f"El comportamiento observado es consistente, {VAGUE[fig.order % len(VAGUE)]}."


def compose(doc: DocPlan, bank: list[dict]) -> tuple[dict, list[Block]]:
    """Header fields and the ordered blocks of the body. Deterministic for a given document plan."""
    rng = random.Random(doc.doc_id)
    article = bank[doc.article_index]
    for fig in doc.figures:
        fig.title = figure_title(fig, article)

    filler = [p for a in bank if a["area"] == article["area"] for k in ("introduccion", "metodos", "resultados") for p in a[k]]
    rng.shuffle(filler)
    extra = [clean(p) for p in filler[: doc.body_blocks]]
    third = len(extra) // 3
    extra_by_section = {"introduccion": extra[:third], "metodos": extra[third : 2 * third], "resultados": extra[2 * third :]}

    n_refs = len(article["referencias"])
    figures = list(doc.figures)
    half = (len(figures) + 1) // 2
    figs_by_section = {"metodos": figures[:half], "resultados": figures[half:]}

    blocks: list[Block] = []
    for key, heading in [("introduccion", "Introducción"), ("metodos", "Materiales y métodos"), ("resultados", "Resultados y discusión"), ("conclusiones", "Conclusiones")]:
        blocks.append(Block("heading", heading))
        paragraphs = [clean(p) for p in article[key]] + extra_by_section.get(key, [])
        pending = list(figs_by_section.get(key, []))
        for i, text in enumerate(paragraphs):
            if key != "conclusiones" and i % 2 == 0:
                text += f" Este planteamiento coincide con trabajos previos [{rng.randint(1, n_refs)}]."
            if pending:
                fig = pending.pop(0)
                blocks.append(Block("paragraph", f"{text} {mention(fig)}"))
                blocks.append(Block("figure", figure=fig))
            else:
                blocks.append(Block("paragraph", text))
        for fig in pending:  # more figures than paragraphs
            blocks.append(Block("paragraph", mention(fig)))
            blocks.append(Block("figure", figure=fig))
    blocks.append(Block("heading", "Referencias"))
    for i, ref in enumerate(article["referencias"], start=1):
        blocks.append(Block("reference", f"[{i}] {clean(ref)}"))

    header = {
        "title": clean(article["titulo"]),
        "title_en": clean(article["titulo_en"]),
        "abstract": clean(article["resumen"]),
        "keywords": ", ".join(clean(k) for k in article["palabras_clave"]),
        "type_label": ARTICLE_TYPE_LABEL[doc.article_type],
        "area": article["area"],
    }
    return header, blocks
