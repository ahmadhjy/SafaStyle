"""Extract the gold flame symbol from the original Safa Style logo."""
from pathlib import Path

from PIL import Image

SRC = Path(
    r"C:\Users\ME\.cursor\projects\c-Users-ME-Desktop-Safa-Style\assets"
    r"\c__Users_ME_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images"
    r"_488038568_1199446101550076_1255610928614637307_n-7d088d9d-9468-455e-927f-0ef15cc1b9a9.png"
)
OUT = Path(r"C:\Users\ME\Desktop\Safa Style\static\img\symbol.png")


def is_gold(r, g, b):
    return r > 150 and g > 105 and b < 130 and (r - b) > 45


def main():
    im = Image.open(SRC).convert("RGBA")
    w, h = im.size
    print("size", w, h)

    # Isolate central flame region (above the SAFA STYLE text)
    box = (int(0.34 * w), int(0.28 * h), int(0.62 * w), int(0.56 * h))
    center = im.crop(box)
    px = center.load()
    cw, ch = center.size

    # Find tight bbox of gold pixels
    minx, miny, maxx, maxy = cw, ch, 0, 0
    found = False
    for y in range(ch):
        for x in range(cw):
            r, g, b, a = px[x, y]
            if is_gold(r, g, b):
                found = True
                minx = min(minx, x)
                miny = min(miny, y)
                maxx = max(maxx, x)
                maxy = max(maxy, y)
    if not found:
        print("No gold found — adjust thresholds")
        return
    margin = 12
    minx = max(0, minx - margin)
    miny = max(0, miny - margin)
    maxx = min(cw, maxx + margin)
    maxy = min(ch, maxy + margin)
    flame = center.crop((minx, miny, maxx, maxy))
    print("flame bbox in center:", (minx, miny, maxx, maxy), "->", flame.size)

    # Make near-white transparent, keep gold shading
    flame = flame.convert("RGBA")
    fp = flame.load()
    fw, fh = flame.size
    for y in range(fh):
        for x in range(fw):
            r, g, b, a = fp[x, y]
            mn = min(r, g, b)
            mx = max(r, g, b)
            # near white / light gray background -> transparent
            if mn > 225 and (mx - mn) < 25:
                fp[x, y] = (r, g, b, 0)
            else:
                # soft edge: fade very light pixels
                if mn > 205 and (mx - mn) < 40:
                    fp[x, y] = (r, g, b, 90)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    flame.save(OUT)
    print("saved", OUT, flame.size)


if __name__ == "__main__":
    main()
