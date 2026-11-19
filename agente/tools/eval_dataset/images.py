"""Synthetic figure images drawn with Pillow at an exact pixel size (charts and block diagrams, no real data)."""
from __future__ import annotations

import random
import zlib
from pathlib import Path

from PIL import Image, ImageDraw

from tools.eval_dataset.design import FigurePlan

PALETTE = [(31, 119, 180), (255, 127, 14), (44, 160, 44), (214, 39, 40), (148, 103, 189), (140, 86, 75)]


def _bars(draw: ImageDraw.ImageDraw, w: int, h: int, rng: random.Random) -> None:
    n = rng.randint(4, 9)
    x0, y0, x1, y1 = int(w * 0.10), int(h * 0.10), int(w * 0.95), int(h * 0.85)
    draw.line([(x0, y0), (x0, y1), (x1, y1)], fill=(0, 0, 0), width=max(2, h // 200))
    slot = (x1 - x0) / n
    for i in range(n):
        top = y1 - int((y1 - y0) * rng.uniform(0.15, 0.95))
        draw.rectangle([x0 + slot * (i + 0.2), top, x0 + slot * (i + 0.8), y1], fill=PALETTE[i % len(PALETTE)])


def _lines(draw: ImageDraw.ImageDraw, w: int, h: int, rng: random.Random) -> None:
    x0, y0, x1, y1 = int(w * 0.10), int(h * 0.10), int(w * 0.95), int(h * 0.85)
    draw.line([(x0, y0), (x0, y1), (x1, y1)], fill=(0, 0, 0), width=max(2, h // 200))
    for s in range(rng.randint(2, 4)):
        pts, y = [], rng.uniform(0.3, 0.7)
        for i in range(12):
            y = min(0.95, max(0.05, y + rng.uniform(-0.12, 0.12)))
            pts.append((x0 + (x1 - x0) * i / 11, y1 - (y1 - y0) * y))
        draw.line(pts, fill=PALETTE[s], width=max(2, h // 150))


def _blocks(draw: ImageDraw.ImageDraw, w: int, h: int, rng: random.Random) -> None:
    n = rng.randint(3, 5)
    bw, bh, gap = w * 0.8 / n * 0.7, h * 0.35, w * 0.8 / n
    y = h * 0.32
    for i in range(n):
        x = w * 0.1 + gap * i
        draw.rectangle([x, y, x + bw, y + bh], outline=(0, 0, 0), fill=tuple(min(255, c + 90) for c in PALETTE[i % 6]), width=max(2, h // 200))
        if i < n - 1:
            draw.line([(x + bw, y + bh / 2), (x + gap, y + bh / 2)], fill=(0, 0, 0), width=max(2, h // 200))


def image_seed(doc_id: str, order: int) -> int:
    """Stable across processes (unlike `hash`), so the same plan always draws the same images."""
    return zlib.crc32(f"{doc_id}-{order}".encode())


def draw_figure(w: int, h: int, seed: int) -> Image.Image:
    """Upright chart of exactly w x h pixels."""
    rng = random.Random(seed)
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    rng.choice([_bars, _lines, _blocks])(draw, w, h, rng)
    draw.rectangle([0, 0, w - 1, h - 1], outline=(120, 120, 120), width=1)
    return img


def write_image(fig: FigurePlan, out_dir: Path, stem: str, seed: int) -> Path:
    """Write the image FILE the author would embed (source size), in the format of the variant."""
    if fig.variant == "rotada":
        # Drawn upright at the visible size, stored sideways; the document rotates it back 90 degrees.
        img = draw_figure(fig.visible_w_px, fig.visible_h_px, seed).rotate(-90, expand=True)
    else:
        img = draw_figure(fig.source_w_px, fig.source_h_px, seed)
    assert img.size == (fig.source_w_px, fig.source_h_px), (img.size, fig)
    if fig.variant == "jpeg":
        path = out_dir / f"{stem}.jpg"
        img.save(path, "JPEG", quality=90)
    elif fig.variant == "png_alfa":
        path = out_dir / f"{stem}.png"
        rgba = img.convert("RGBA")
        rgba.putalpha(Image.new("L", img.size, 255).point(lambda _: 255))
        px = rgba.load()
        for x in range(0, img.size[0], 7):  # a few transparent pixels so the alpha channel is really used
            px[x, 0] = (255, 255, 255, 0)
        rgba.save(path, "PNG")
    else:
        path = out_dir / f"{stem}.png"
        img.save(path, "PNG")  # no pHYs chunk: LaTeX takes 1 px = 1 bp, which the crop relies on
    return path
