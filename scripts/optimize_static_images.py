"""Convert heavy homepage PNGs to responsive WebP derivatives."""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1] / "static" / "img"

JOBS = [
    (ROOT / "banners" / "banner1.png", ROOT / "banners" / "banner1", [900, 1600]),
    (ROOT / "banners" / "banner2.png", ROOT / "banners" / "banner2", [900, 1600]),
    (ROOT / "banners" / "banner3.png", ROOT / "banners" / "banner3", [900, 1600]),
    (ROOT / "featured" / "featured1.png", ROOT / "featured" / "featured1", [600, 1200]),
    (ROOT / "featured" / "featured2.png", ROOT / "featured" / "featured2", [600, 1200]),
]


def main():
    for src, stem, widths in JOBS:
        im = Image.open(src).convert("RGB")
        w0, h0 = im.size
        print(f"{src.name}: {w0}x{h0}")
        for tw in widths:
            if tw >= w0:
                out = im
            else:
                th = max(1, int(h0 * (tw / w0)))
                out = im.resize((tw, th), Image.Resampling.LANCZOS)
            q = 74 if tw <= 900 else 78
            path = Path(f"{stem}-{tw}.webp")
            out.save(path, "WEBP", quality=q, method=6)
            print(f"  {path.name}: {path.stat().st_size // 1024}KB {out.size}")
        desktop = max(widths)
        if desktop >= w0:
            out = im
        else:
            th = max(1, int(h0 * (desktop / w0)))
            out = im.resize((desktop, th), Image.Resampling.LANCZOS)
        path = Path(f"{stem}.webp")
        out.save(path, "WEBP", quality=78, method=6)
        print(f"  {path.name}: {path.stat().st_size // 1024}KB")


if __name__ == "__main__":
    main()
