"""
web/sync_styles.py
------------------
Utility script to embed or verify web/static/style.css in HTML files when needed.
"""

from pathlib import Path

STATIC = Path(__file__).parent / "static"
INDEX = STATIC / "index.html"
CSS = STATIC / "style.css"


def sync() -> None:
    if not INDEX.exists() or not CSS.exists():
        print("Missing index.html or style.css in static directory.")
        return

    html = INDEX.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    start = html.find("<style>")
    end = html.find("</style>", start)

    if start != -1 and end != -1:
        updated = html[: start + len("<style>")] + f"\n{css}\n  " + html[end:]
        INDEX.write_text(updated, encoding="utf-8")
        print(f"Synced {len(css)} bytes from style.css into index.html inline style block.")
    else:
        print("index.html references external /style.css — no inline sync needed.")


if __name__ == "__main__":
    sync()
