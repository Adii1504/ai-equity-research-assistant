"""Embed web/static/style.css into index.html (for Live Preview / file:// support)."""

from pathlib import Path

STATIC = Path(__file__).parent / "static"
INDEX = STATIC / "index.html"
CSS = STATIC / "style.css"


def sync() -> None:
    html = INDEX.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    start = html.find("<style>")
    end = html.find("</style>", start)
    if start == -1 or end == -1:
        raise SystemExit("Could not find <style> block in index.html")
    updated = html[: start + len("<style>")] + f"\n{css}\n  " + html[end:]
    INDEX.write_text(updated, encoding="utf-8")
    print(f"Synced {len(css)} bytes from style.css into index.html")


if __name__ == "__main__":
    sync()
