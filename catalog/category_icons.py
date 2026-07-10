"""
Theme-colored SVG icons for category tiles and admin thumbnails.
"""

from __future__ import annotations

from pathlib import Path

# Safa Style mandala palette
ACCENTS = {
    "gold": ("#e0a92e", "#f7ebcf"),
    "magenta": ("#e23d8b", "#f9d4e8"),
    "teal": ("#2fbfa8", "#d4f5ef"),
    "orange": ("#f26b3a", "#fde4d8"),
    "purple": ("#9b4f96", "#ecd8eb"),
    "ink": ("#1c1526", "#e8e4ec"),
}

# slug -> (accent key, svg inner paths)
ICON_PATHS: dict[str, tuple[str, str]] = {
    "accessories": (
        "magenta",
        """
        <circle cx="32" cy="30" r="14" stroke-width="2.2"/>
        <circle cx="32" cy="30" r="3" fill="#1c1526" stroke="none"/>
        <path d="M18 44 L32 38 L46 44" stroke-width="2"/>
        <rect x="42" y="18" width="12" height="12" rx="2" stroke-width="1.8"/>
        <path d="M46 22 L46 26" stroke-width="1.5"/>
        """,
    ),
    "bags": (
        "gold",
        """
        <path d="M18 26 C18 20 24 16 32 16 C40 16 46 20 46 26" stroke-width="2.2"/>
        <rect x="16" y="26" width="32" height="24" rx="3" stroke-width="2.2"/>
        <path d="M26 26 L26 22 C26 18 29 16 32 16 C35 16 38 18 38 22 L38 26" stroke-width="1.8"/>
        """,
    ),
    "basics": (
        "teal",
        """
        <rect x="14" y="18" width="36" height="10" rx="2" stroke-width="2"/>
        <rect x="14" y="30" width="36" height="10" rx="2" stroke-width="2"/>
        <rect x="14" y="42" width="36" height="10" rx="2" stroke-width="2"/>
        """,
    ),
    "cardigans": (
        "purple",
        """
        <path d="M22 18 L32 24 L42 18 L42 50 L22 50 Z" stroke-width="2.2"/>
        <path d="M32 24 L32 50" stroke-width="1.8"/>
        <path d="M26 30 L26 44 M30 30 L30 44 M34 30 L34 44 M38 30 L38 44" stroke-width="1.5"/>
        """,
    ),
    "coats": (
        "orange",
        """
        <path d="M20 16 L32 22 L44 16 L48 52 L16 52 Z" stroke-width="2.2"/>
        <path d="M32 22 L32 52" stroke-width="1.8"/>
        <circle cx="32" cy="34" r="2" fill="#1c1526" stroke="none"/>
        <circle cx="32" cy="42" r="2" fill="#1c1526" stroke="none"/>
        """,
    ),
    "dresses": (
        "magenta",
        """
        <path d="M32 14 L38 24 L46 52 L18 52 L26 24 Z" stroke-width="2.2"/>
        <path d="M26 24 L38 24" stroke-width="1.8"/>
        """,
    ),
    "jackets": (
        "gold",
        """
        <path d="M18 22 L32 30 L46 22 L46 50 L18 50 Z" stroke-width="2.2"/>
        <path d="M32 30 L32 50" stroke-width="1.8"/>
        <path d="M18 22 L32 16 L46 22" stroke-width="2"/>
        """,
    ),
    "pants": (
        "teal",
        """
        <path d="M20 18 L44 18 L42 52 L34 52 L32 34 L30 52 L22 52 Z" stroke-width="2.2"/>
        """,
    ),
    "ramadan-specials": (
        "gold",
        """
        <path d="M32 14 A16 16 0 1 1 20 38" stroke-width="2.2"/>
        <path d="M28 50 L32 38 L36 50 Z" stroke-width="2"/>
        <circle cx="32" cy="44" r="3" fill="#1c1526" stroke="none"/>
        """,
    ),
    "scarfs": (
        "purple",
        """
        <path d="M14 22 L50 26 L46 38 L12 34 Z" stroke-width="2"/>
        <path d="M12 34 L48 38 L44 50 L10 46 Z" stroke-width="2"/>
        """,
    ),
    "sets": (
        "magenta",
        """
        <rect x="20" y="16" width="24" height="20" rx="2" stroke-width="2"/>
        <path d="M18 40 L46 40 L42 54 L22 54 Z" stroke-width="2.2"/>
        """,
    ),
    "shawls": (
        "orange",
        """
        <path d="M12 20 C24 28 40 28 52 20" stroke-width="2"/>
        <path d="M14 32 C26 40 38 40 50 32" stroke-width="2"/>
        <path d="M16 44 C28 52 36 52 48 44" stroke-width="2"/>
        """,
    ),
    "shoes": (
        "teal",
        """
        <path d="M12 40 L52 40 L48 48 L14 48 Z" stroke-width="2.2"/>
        <path d="M20 40 C24 28 40 28 44 40" stroke-width="2"/>
        """,
    ),
    "skirts": (
        "purple",
        """
        <path d="M24 18 L40 18 L48 52 L16 52 Z" stroke-width="2.2"/>
        <path d="M24 18 L40 18" stroke-width="2"/>
        """,
    ),
    "socks": (
        "gold",
        """
        <path d="M22 16 L22 40 C22 46 28 50 34 50 L40 50 C44 50 46 46 44 42 L38 34 L38 16 Z" stroke-width="2"/>
        <path d="M42 16 L42 40 C42 46 36 50 30 50" stroke-width="2"/>
        """,
    ),
    "tops": (
        "orange",
        """
        <path d="M12 22 L32 14 L52 22 L48 50 L16 50 Z" stroke-width="2.2"/>
        <path d="M32 14 L32 50" stroke-width="1.5"/>
        """,
    ),
    "vests": (
        "magenta",
        """
        <path d="M22 18 L42 18 L44 52 L20 52 Z" stroke-width="2.2"/>
        <path d="M22 18 L32 26 L42 18" stroke-width="2"/>
        <path d="M26 30 L26 44 M38 30 L38 44" stroke-width="1.5"/>
        """,
    ),
}

SLUG_ACCENT_ORDER = [
    "magenta",
    "gold",
    "teal",
    "orange",
    "purple",
]


def accent_for_slug(slug: str, index: int = 0) -> str:
    if slug in ICON_PATHS:
        return ICON_PATHS[slug][0]
    return SLUG_ACCENT_ORDER[index % len(SLUG_ACCENT_ORDER)]


def icon_static_path(slug: str) -> str:
    return f"img/category-icons/{slug}.svg"


def render_category_svg(slug: str, index: int = 0) -> str:
    accent_key, paths = ICON_PATHS.get(slug, ("", ""))
    if not accent_key:
        accent_key = accent_for_slug(slug, index)
        paths = '<circle cx="32" cy="32" r="14" stroke-width="2"/>'
    stroke, _bg = ACCENTS[accent_key]
    ink = "#1c1526"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none" stroke="{ink}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  {paths.strip()}
</svg>"""


def write_category_icons(static_root: Path, slugs: list[str] | None = None) -> int:
    out_dir = static_root / "img" / "category-icons"
    out_dir.mkdir(parents=True, exist_ok=True)
    targets = slugs or list(ICON_PATHS.keys())
    for i, slug in enumerate(targets):
        path = out_dir / f"{slug}.svg"
        path.write_text(render_category_svg(slug, i), encoding="utf-8")
    return len(targets)
