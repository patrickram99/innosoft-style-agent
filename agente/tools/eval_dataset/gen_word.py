"""Word generator: fills the journal's Word template with python-docx and exports to PDF with Microsoft Word.

Word itself reports the page of each figure (COM automation), so the ground truth never depends on the PDF
library used by the agent. Requires Microsoft Word on Windows.
"""
from __future__ import annotations

import time
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

from tools.eval_dataset import TEMPLATES
from tools.eval_dataset.design import DocPlan, FigurePlan
from tools.eval_dataset.images import image_seed, write_image
from tools.eval_dataset.layout import AFFILIATION, AUTHORS, Block, compose

TEMPLATE = TEMPLATES / "Plantilla_Final_InnoSoft.docx"
FONT = "Times New Roman"
WD_EXPORT_PDF, WD_ACTIVE_END_PAGE, WD_STAT_PAGES = 17, 3, 2


def _para(doc, text: str = "", *, size: float = 11, bold: bool = False, italic: bool = False, align=None, keep_next: bool = False):
    p = doc.add_paragraph()
    if text:
        run = p.add_run(text)
        run.font.name, run.font.size, run.bold, run.italic = FONT, Pt(size), bold, italic
    p.alignment = align
    p.paragraph_format.keep_with_next = keep_next
    p.paragraph_format.line_spacing = 1.5
    return p


def _caption(doc, fig: FigurePlan, *, keep_next: bool = False) -> None:
    if fig.caption_defect == "prefijo_fig":
        _para(doc, f"Fig. {fig.printed_number}: {fig.title}", size=10, align=WD_ALIGN_PARAGRAPH.CENTER, keep_next=keep_next)
        return
    p = _para(doc, f"Figura {fig.printed_number}. ", size=10, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, keep_next=keep_next)
    run = p.add_run(f"{fig.title}.")
    run.font.name, run.font.size = FONT, Pt(10)


def _figure(doc, fig: FigurePlan, image: Path) -> None:
    if fig.caption_defect == "pie_arriba":
        _caption(doc, fig, keep_next=True)
    p = _para(doc, align=WD_ALIGN_PARAGRAPH.CENTER, keep_next=fig.caption_defect not in ("sin_pie", "pie_arriba"))
    shape = p.add_run().add_picture(str(image), width=Inches(fig.print_w_in), height=Inches(fig.print_h_in))
    if fig.crop_right_px:
        # Word stores the crop as a fraction of the source image (thousandths of a percent).
        blip_fill = shape._inline.graphic.graphicData.pic.blipFill
        src_rect = OxmlElement("a:srcRect")
        src_rect.set("r", str(round(fig.crop_right_px / fig.source_w_px * 100000)))
        blip_fill.insert(1, src_rect)
    if fig.caption_defect not in ("sin_pie", "pie_arriba"):
        _caption(doc, fig)


def _keep_images_uncompressed(doc) -> None:
    """Document option "Do not compress images in file": Word must not resample the figures on export."""
    settings = doc.settings.element
    if settings.find(qn("w:doNotAutoCompressPictures")) is None:
        anchor = settings.find(qn("w:compat"))
        element = OxmlElement("w:doNotAutoCompressPictures")
        if anchor is not None:
            anchor.addprevious(element)
        else:
            settings.append(element)


def build_docx(plan: DocPlan, header: dict, blocks: list[Block], images: dict[int, Path], target: Path) -> None:
    doc = Document(str(TEMPLATE))
    body = doc.element.body
    first = doc.paragraphs[0]  # carries the licence logo of the template: kept, only its text changes
    for child in list(body):
        if child is not first._p and child.tag != qn("w:sectPr"):
            body.remove(child)
    text_runs = [r for r in first.runs if not r._r.findall(".//" + qn("w:drawing")) and not r._r.findall(".//" + qn("w:pict"))]
    for run in text_runs[1:]:
        run._r.getparent().remove(run._r)
    title_run = text_runs[0] if text_runs else first.add_run()
    title_run.text = header["title"]
    title_run.font.name, title_run.font.size, title_run.bold = FONT, Pt(18), True

    _para(doc, header["title_en"], size=18, bold=True, italic=True)
    _para(doc, AUTHORS, bold=True)
    _para(doc, f"1 {AFFILIATION}")
    _para(doc, f"Tipo de artículo: {header['type_label']}")
    _para(doc, "Resumen", bold=True)
    _para(doc, header["abstract"])
    _para(doc, f"Palabras clave: {header['keywords']}")
    for block in blocks:
        if block.kind == "heading":
            _para(doc, block.text, size=14, bold=True, keep_next=True)
        elif block.kind == "figure":
            _figure(doc, block.figure, images[block.figure.order])
        else:
            _para(doc, block.text, align=WD_ALIGN_PARAGRAPH.JUSTIFY if block.kind == "paragraph" else None)
    _keep_images_uncompressed(doc)
    doc.save(str(target))


def generate(docs: list[DocPlan], bank: list[dict], build: Path, pdf_dir: Path) -> None:
    import win32com.client

    (build / "img").mkdir(parents=True, exist_ok=True)
    for plan in docs:
        header, blocks = compose(plan, bank)
        images = {
            fig.order: write_image(fig, build / "img", f"{plan.doc_id}-f{fig.order}", seed=image_seed(plan.doc_id, fig.order))
            for fig in plan.figures
        }
        build_docx(plan, header, blocks, images, build / f"{plan.doc_id}.docx")

    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        for plan in docs:
            document = word.Documents.Open(str((build / f"{plan.doc_id}.docx").resolve()), ReadOnly=True, AddToRecentFiles=False)
            try:
                document.Repaginate()
                shapes = document.InlineShapes
                if shapes.Count != len(plan.figures):
                    raise RuntimeError(f"{plan.doc_id}: Word ve {shapes.Count} imágenes en línea y el plan tiene {len(plan.figures)}")
                for fig in plan.figures:  # inline shapes come in document order, the same as the plan
                    fig.page = int(shapes.Item(fig.order).Range.Information(WD_ACTIVE_END_PAGE))
                plan.pages = int(document.ComputeStatistics(WD_STAT_PAGES))
                target = pdf_dir / f"{plan.doc_id}.pdf"
                document.ExportAsFixedFormat(str(target.resolve()), WD_EXPORT_PDF, False, 0)  # 0 = optimise for print
                deadline = time.monotonic() + 60  # the export may finish in the background
                while not (target.exists() and target.stat().st_size > 0):
                    if time.monotonic() > deadline:
                        raise RuntimeError(f"{plan.doc_id}: Word no escribió el PDF")
                    time.sleep(0.2)
                plan.pdf = target.name
            finally:
                document.Close(False)
    finally:
        word.Quit()

