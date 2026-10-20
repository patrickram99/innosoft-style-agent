"""Convierte los DOCX de muestras/ a PDF en muestras/pdf/.

Usa LibreOffice en modo headless si está instalado; si no, usa Microsoft Word
por automatización COM (requiere pywin32 y Word instalado).

    python scripts/convertir_docx.py [--in muestras] [--out muestras/pdf] [--motor auto|word|libreoffice]
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WD_FORMAT_PDF = 17

LIBREOFFICE_CANDIDATES = [
    "soffice",
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
]


def find_libreoffice() -> str | None:
    for cand in LIBREOFFICE_CANDIDATES:
        found = shutil.which(cand) or (cand if Path(cand).exists() else None)
        if found:
            return found
    return None


def convert_with_libreoffice(soffice: str, docx_files: list[Path], out_dir: Path) -> list[Path]:
    cmd = [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(out_dir), *map(str, docx_files)]
    subprocess.run(cmd, check=True)
    return [out_dir / f"{d.stem}.pdf" for d in docx_files]


def convert_with_word(docx_files: list[Path], out_dir: Path) -> list[Path]:
    try:
        import win32com.client  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("Falta pywin32: pip install pywin32") from exc

    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    results: list[Path] = []
    try:
        for docx in docx_files:
            target = out_dir / f"{docx.stem}.pdf"
            doc = word.Documents.Open(str(docx.resolve()), ReadOnly=True, AddToRecentFiles=False)
            try:
                doc.SaveAs2(str(target.resolve()), FileFormat=WD_FORMAT_PDF)
            finally:
                doc.Close(SaveChanges=0)
            results.append(target)
    finally:
        word.Quit()
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--in", dest="src", default=str(ROOT / "muestras"))
    parser.add_argument("--out", dest="out", default=str(ROOT / "muestras" / "pdf"))
    parser.add_argument("--motor", choices=["auto", "word", "libreoffice"], default="auto")
    args = parser.parse_args(argv)

    src, out = Path(args.src), Path(args.out)
    docx_files = sorted(p for p in src.rglob("*.docx") if not p.name.startswith("~$"))
    if not docx_files:
        print(f"No hay archivos .docx en {src}")
        return 1
    out.mkdir(parents=True, exist_ok=True)

    soffice = find_libreoffice() if args.motor in ("auto", "libreoffice") else None
    if soffice:
        print(f"Convirtiendo con LibreOffice: {soffice}")
        produced = convert_with_libreoffice(soffice, docx_files, out)
    elif args.motor in ("auto", "word"):
        print("Convirtiendo con Microsoft Word (COM)")
        produced = convert_with_word(docx_files, out)
    else:
        print("No se encontro LibreOffice.")
        return 1

    for pdf in produced:
        estado = "OK" if pdf.exists() else "FALLO"
        print(f"  {estado}  {pdf}")
    return 0 if all(p.exists() for p in produced) else 1


if __name__ == "__main__":
    sys.exit(main())
