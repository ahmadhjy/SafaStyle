"""Download latin WOFF2 faces used by the storefront."""
import re
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "static" / "fonts"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
CSS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Cormorant+Garamond:wght@600&family=Outfit:wght@400;500;600&display=swap"
)

# Keep only latin blocks to minimize bytes.
FILES = {
    # Cormorant Garamond 600 latin
    "cormorant-garamond-600.woff2": "https://fonts.gstatic.com/s/cormorantgaramond/v21/co3umX5slCNuHLi8bLeY9MK7whWMhyjypVO7abI26QOD_iE9KnTOig.woff2",
    # Outfit variable-ish same file for 400/500/600 latin in recent builds —
    # fetch distinct if available from CSS.
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(CSS_URL, headers={"User-Agent": UA})
    css = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    # Parse latin (not latin-ext) @font-face blocks
    blocks = re.split(r"/\* ", css)
    mapping = {}
    for block in blocks:
        if not block.startswith("latin */"):
            continue
        family = re.search(r"font-family:\s*'([^']+)'", block)
        weight = re.search(r"font-weight:\s*(\d+)", block)
        url = re.search(r"url\((https://[^)]+\.woff2)\)", block)
        if not (family and weight and url):
            continue
        key = (family.group(1), weight.group(1))
        mapping[key] = url.group(1)

    wanted = [
        ("Cormorant Garamond", "600", "cormorant-garamond-600.woff2"),
        ("Outfit", "400", "outfit-400.woff2"),
        ("Outfit", "500", "outfit-500.woff2"),
        ("Outfit", "600", "outfit-600.woff2"),
    ]
    for family, weight, filename in wanted:
        url = mapping.get((family, weight))
        if not url:
            print(f"missing {family} {weight}")
            continue
        dest = OUT / filename
        urllib.request.urlretrieve(url, dest)
        print(f"wrote {dest.name} {dest.stat().st_size // 1024}KB")


if __name__ == "__main__":
    main()
