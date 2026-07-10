"""Extract readable text from saved Safa Style HTML pages."""
from html.parser import HTMLParser
from pathlib import Path
import re
import tempfile
import sys

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0
        self.skip_tags = {"script", "style", "noscript", "svg", "nav", "header", "footer"}

    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags:
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in self.skip_tags and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            t = data.strip()
            if t:
                self.parts.append(t)


def extract(path: Path) -> str:
    if not path.exists() or path.stat().st_size < 100:
        return f"(missing or empty: {path})"
    html = path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(
        r'class="[^"]*entry-content[^"]*"[^>]*>(.*?)</div>\s*(?:<div|</article|</main)',
        html,
        re.S | re.I,
    )
    if not m:
        m = re.search(r"<main[^>]*>(.*?)</main>", html, re.S | re.I)
    chunk = m.group(1) if m else html
    te = TextExtractor()
    te.feed(chunk)
    lines = []
    for line in te.parts:
        if not lines or lines[-1] != line:
            lines.append(line)
    return "\n".join(lines)


def main():
    tmp = Path(tempfile.gettempdir())
    out_dir = Path(__file__).parent / "site_content"
    out_dir.mkdir(exist_ok=True)
    names = [
        "ss-privacy",
        "ss-terms",
        "ss-contact",
        "ss-findus",
        "ss-exchange",
        "safastyle",
    ]
    for name in names:
        src = tmp / f"{name}.html"
        text = extract(src)
        dest = out_dir / f"{name}.txt"
        dest.write_text(text, encoding="utf-8")
        print(f"==== {name} ({src.stat().st_size if src.exists() else 0} bytes) ====")
        print(text[:2500])
        print()


if __name__ == "__main__":
    main()
