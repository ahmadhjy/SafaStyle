"""Build favicon + apple-touch-icon from the original Safa Style logo symbol."""
from pathlib import Path

from PIL import Image

SRC = Path(
    r"C:\Users\ME\.cursor\projects\c-Users-ME-Desktop-Safa-Style\assets"
    r"\c__Users_ME_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images"
    r"_488038568_1199446101550076_1255610928614637307_n-7d088d9d-9468-455e-927f-0ef15cc1b9a9.png"
)
SYMBOL = Path(r"C:\Users\ME\Desktop\Safa Style\static\img\symbol.png")
OUT = Path(r"C:\Users\ME\Desktop\Safa Style\static\img")


def is_gold(r, g, b):
    return r > 150 and g > 105 and b < 130 and (r - b) > 45


def load_symbol():
    if SYMBOL.exists():
        return Image.open(SYMBOL).convert("RGBA")
    im = Image.open(SRC).convert("RGBA")
    w, h = im.size
    box = (int(0.34 * w), int(0.28 * h), int(0.62 * w), int(0.56 * h))
    center = im.crop(box)
    px = center.load()
    cw, ch = center.size
    minx, miny, maxx, maxy = cw, ch, 0, 0
    for y in range(ch):
        for x in range(cw):
            r, g, b, a = px[x, y]
            if is_gold(r, g, b):
                minx, miny = min(minx, x), min(miny, y)
                maxx, maxy = max(maxx, x), max(maxy, y)
    flame = center.crop((max(0, minx - 12), max(0, miny - 12), min(cw, maxx + 12), min(ch, maxy + 12)))
    fp = flame.load()
    fw, fh = flame.size
    for y in range(fh):
        for x in range(fw):
            r, g, b, a = fp[x, y]
            if min(r, g, b) > 225:
                fp[x, y] = (r, g, b, 0)
    return flame


def icon_on_bg(symbol, size, bg=(26, 18, 32, 255), pad=0.14):
    canvas = Image.new("RGBA", (size, size), bg)
    sw, sh = symbol.size
    inner = int(size * (1 - pad * 2))
    scale = min(inner / sw, inner / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    resized = symbol.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas.paste(resized, ((size - nw) // 2, (size - nh) // 2), resized)
    return canvas


def main():
    symbol = load_symbol()
    OUT.mkdir(parents=True, exist_ok=True)

    sizes = [16, 32, 48]
    icons = [icon_on_bg(symbol, s).convert("RGBA") for s in sizes]
    icons[0].save(
        OUT / "favicon.ico",
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=icons[1:],
    )
    icon_on_bg(symbol, 180).save(OUT / "apple-touch-icon.png", "PNG")
    icon_on_bg(symbol, 32).save(OUT / "favicon-32.png", "PNG")
    print("saved favicon.ico, apple-touch-icon.png, favicon-32.png")


if __name__ == "__main__":
    main()
