"""
Generate aesthetic 3:4 category thumbnails for Safa Style.

Warm neutral flat-lay style — similar to boutique category grids.
"""

from __future__ import annotations

import io
import math
from typing import Callable

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont


W, H = 600, 800

BG_TOP = (235, 228, 218)
BG_BOTTOM = (214, 203, 188)
SHADOW = (120, 100, 80, 70)
INK = (38, 32, 28)
MUTED = (110, 98, 88)
TONE_A = (198, 178, 152)
TONE_B = (168, 148, 126)
TONE_C = (138, 118, 98)
TONE_D = (88, 72, 58)
ACCENT = (201, 162, 39)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = []
    if bold:
        candidates.extend(
            [
                "C:/Windows/Fonts/georgiab.ttf",
                "C:/Windows/Fonts/timesbd.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
            ]
        )
    else:
        candidates.extend(
            [
                "C:/Windows/Fonts/georgia.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            ]
        )
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _gradient_bg() -> Image.Image:
    img = Image.new("RGB", (W, H), BG_TOP)
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / max(H - 1, 1)
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    return img


def _soft_light(img: Image.Image) -> Image.Image:
    overlay = Image.new("RGBA", (W, H), (255, 248, 240, 0))
    draw = ImageDraw.Draw(overlay)
    draw.ellipse((-80, -40, W * 0.55, H * 0.55), fill=(255, 255, 255, 38))
    draw.rectangle((W * 0.45, H * 0.2, W + 60, H), fill=(0, 0, 0, 16))
    return Image.alpha_composite(img.convert("RGBA"), overlay)


def _ground_shadow(img: Image.Image, cx: int, cy: int, rx: int, ry: int) -> Image.Image:
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=SHADOW)
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    return Image.alpha_composite(img, shadow)


def _label(draw: ImageDraw.ImageDraw, text: str) -> None:
    font = _font(34, bold=True)
    bbox = draw.textbbox((0, 0), text.upper(), font=font)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2
    y = H - 92
    draw.text((x, y), text.upper(), fill=INK, font=font)


def _rect(draw, xy, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=8, fill=fill, outline=outline, width=width)


def _draw_accessories(draw: ImageDraw.ImageDraw) -> None:
    draw.ellipse((210, 250, 390, 360), outline=TONE_D, width=4)
    for i in range(9):
        ang = math.radians(15 + i * 18)
        x = 300 + int(78 * math.cos(ang))
        y = 305 + int(48 * math.sin(ang))
        draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=TONE_B)
    _rect(draw, (360, 330, 430, 390), TONE_C)
    draw.ellipse((372, 342, 418, 388), outline=ACCENT, width=3)
    draw.polygon([(250, 390), (290, 430), (250, 470), (210, 430)], fill=(40, 40, 40))


def _draw_bags(draw: ImageDraw.ImageDraw) -> None:
    _rect(draw, (170, 300, 430, 470), TONE_A, outline=TONE_C, width=2)
    draw.arc((220, 250, 380, 340), 200, 340, fill=TONE_D, width=8)
    _rect(draw, (250, 360, 350, 420), TONE_B)
    draw.line([(300, 300), (300, 360)], fill=TONE_D, width=2)


def _draw_basics(draw: ImageDraw.ImageDraw) -> None:
    colors = [(245, 245, 245), TONE_A, (170, 170, 170), TONE_D]
    for i, col in enumerate(colors):
        y = 290 + i * 42
        _rect(draw, (190, y, 410, y + 36), col, outline=TONE_C, width=1)


def _draw_cardigans(draw: ImageDraw.ImageDraw) -> None:
    draw.polygon([(250, 250), (350, 250), (390, 500), (210, 500)], fill=TONE_A, outline=TONE_C)
    for x in range(270, 351, 22):
        draw.line([(x, 280), (x, 470)], fill=TONE_C, width=2)
    draw.line([(300, 250), (300, 500)], fill=TONE_B, width=3)


def _draw_coats(draw: ImageDraw.ImageDraw) -> None:
    draw.polygon([(230, 230), (370, 230), (410, 520), (190, 520)], fill=TONE_B, outline=TONE_D)
    draw.line([(300, 230), (300, 520)], fill=TONE_C, width=2)
    for y in range(300, 460, 40):
        draw.ellipse((285, y, 315, y + 20), fill=TONE_D)


def _draw_dresses(draw: ImageDraw.ImageDraw) -> None:
    draw.polygon([(300, 240), (340, 300), (380, 520), (220, 520), (260, 300)], fill=TONE_A, outline=TONE_C)
    draw.arc((270, 220, 330, 290), 20, 160, fill=TONE_B, width=6)


def _draw_jackets(draw: ImageDraw.ImageDraw) -> None:
    draw.polygon([(240, 270), (360, 270), (390, 500), (210, 500)], fill=TONE_C, outline=TONE_D)
    draw.line([(300, 270), (300, 500)], fill=TONE_D, width=2)
    draw.polygon([(240, 270), (300, 320), (360, 270)], fill=TONE_B)


def _draw_pants(draw: ImageDraw.ImageDraw) -> None:
    colors = [TONE_A, TONE_B, TONE_D]
    for i, col in enumerate(colors):
        y = 300 + i * 50
        _rect(draw, (200, y, 400, y + 40), col, outline=TONE_C)


def _draw_ramadan(draw: ImageDraw.ImageDraw) -> None:
    draw.pieslice((220, 260, 380, 420), 30, 210, fill=ACCENT)
    draw.pieslice((235, 275, 365, 405), 30, 210, fill=BG_TOP)
    _rect(draw, (270, 360, 330, 480), TONE_D)
    draw.polygon([(285, 340), (315, 340), (330, 360), (270, 360)], fill=ACCENT)
    draw.ellipse((288, 390, 312, 420), fill=(255, 220, 120))


def _draw_scarfs(draw: ImageDraw.ImageDraw) -> None:
    for i, col in enumerate([TONE_A, (210, 170, 170), (170, 170, 170)]):
        y = 310 + i * 55
        draw.polygon([(190, y), (410, y + 10), (400, y + 45), (200, y + 35)], fill=col)


def _draw_sets(draw: ImageDraw.ImageDraw) -> None:
    _rect(draw, (230, 270, 370, 390), (195, 155, 165), outline=TONE_C)
    draw.polygon([(220, 400), (380, 400), (360, 510), (240, 510)], fill=(175, 135, 145))


def _draw_shawls(draw: ImageDraw.ImageDraw) -> None:
    for i, col in enumerate([TONE_A, TONE_B, (220, 220, 220)]):
        draw.polygon(
            [(160 + i * 20, 280), (440 - i * 15, 300), (420, 360 + i * 40), (180, 340 + i * 35)],
            fill=col,
        )


def _draw_shoes(draw: ImageDraw.ImageDraw) -> None:
    draw.polygon([(200, 420), (400, 420), (380, 470), (180, 470)], fill=TONE_B, outline=TONE_D)
    draw.pieslice((250, 360, 390, 450), 180, 360, fill=TONE_A, outline=TONE_C)


def _draw_skirts(draw: ImageDraw.ImageDraw) -> None:
    for i, col in enumerate([TONE_A, TONE_B, TONE_D]):
        top = 300 + i * 8
        draw.polygon([(280, top), (320, top), (360, 500 - i * 15), (240, 500 - i * 15)], fill=col)


def _draw_socks(draw: ImageDraw.ImageDraw) -> None:
    pairs = [TONE_A, TONE_B, TONE_C, TONE_D]
    for i, col in enumerate(pairs):
        x = 170 + (i % 2) * 120
        y = 320 + (i // 2) * 90
        _rect(draw, (x, y, x + 70, y + 100), col, outline=TONE_C)


def _draw_tops(draw: ImageDraw.ImageDraw) -> None:
    draw.line([(180, 260), (420, 260)], fill=TONE_D, width=5)
    colors = [(245, 245, 245), TONE_A, (170, 170, 170), TONE_D]
    for i, col in enumerate(colors):
        x = 185 + i * 52
        draw.polygon([(x, 260), (x + 45, 260), (x + 40, 430), (x + 5, 430)], fill=col)


def _draw_vests(draw: ImageDraw.ImageDraw) -> None:
    draw.polygon([(250, 270), (350, 270), (370, 500), (230, 500)], fill=TONE_B, outline=TONE_C)
    draw.rectangle((250, 270, 350, 310), fill=(240, 235, 228))


DRAWERS: dict[str, Callable[[ImageDraw.ImageDraw], None]] = {
    "accessories": _draw_accessories,
    "bags": _draw_bags,
    "basics": _draw_basics,
    "cardigans": _draw_cardigans,
    "coats": _draw_coats,
    "dresses": _draw_dresses,
    "jackets": _draw_jackets,
    "pants": _draw_pants,
    "ramadan-specials": _draw_ramadan,
    "scarfs": _draw_scarfs,
    "sets": _draw_sets,
    "shawls": _draw_shawls,
    "shoes": _draw_shoes,
    "skirts": _draw_skirts,
    "socks": _draw_socks,
    "tops": _draw_tops,
    "vests": _draw_vests,
}


def render_category_image(slug: str, name: str) -> bytes:
    """Return optimized JPEG bytes for a category thumbnail."""
    img = _gradient_bg().convert("RGBA")
    img = _soft_light(img)
    img = _ground_shadow(img, W // 2, 520, 155, 28)
    draw = ImageDraw.Draw(img)
    drawer = DRAWERS.get(slug)
    if drawer:
        drawer(draw)
    _label(draw, name)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=90, optimize=True)
    return buf.getvalue()
