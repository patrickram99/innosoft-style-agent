# Corpus sintético de prueba

Generado con `python tests/fixtures/generate_pdfs.py` (PyMuPDF). Ningún archivo contiene datos
personales: los autores son ficticios y no hay correos ni ORCID. Dimensiones en píxeles como
**alto × ancho**, igual que RE-20.

| Archivo | Caso | Páginas | Figuras | Hallazgos esperados |
|---|---|---|---|---|
| `figuras_pequenas.pdf` | Figuras problemáticas (1) | 3 | 3 raster de 300 × 600 px a 300 dpi, con pie «Figura n.» | RE-20 × 3 · RE-21 × 0 |
| `figuras_baja_dpi.pdf` | Figuras problemáticas (2) | 2 | Fig. 1: 600 × 1400 px a 200 dpi, con pie · Fig. 2: 400 × 1000 px a 200 dpi, **sin pie** | RE-20 × 1 (fig. 2) · RE-21 × 2 |
| `sin_figuras.pdf` | Sin figuras (ALT-03) | 15 | ninguna | ninguno |
| `escaneado.pdf` | Escaneado (ALT-01) | 3 | páginas solo imagen | estado `unreadable/no_text_layer` |
| `correcto.pdf` | Correcto | 10 | 2 raster de 800 × 2000 px a 300 dpi + logo decorativo de 50 × 50 px (ignorado) | ninguno |
| `vectorial.pdf` | Figura vectorial | 1 | 1 `kind=vector` con pie | RE-21 no aplica |
| `corrupto.pdf` | Corrupto (ALT-01) | — | bytes truncados | estado `unreadable/corrupt` |
| `treinta_paginas.pdf` | Rendimiento (US-04 AC-03) | 30 | ninguna | extracción < 10 s |

Los 5 PDFs que exige US-00 §3 son los cinco primeros; `vectorial.pdf`, `corrupto.pdf` y
`treinta_paginas.pdf` son auxiliares de US-04, US-06 y US-10.
