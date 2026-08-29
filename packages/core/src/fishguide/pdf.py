"""Prints build/book.html to build/book.pdf with a headless Chromium.
`page.pdf()` respects the book's own `@media print` rules (one `.page`
per sheet -- see base.html.j2), so this is a thin wrapper, not a
second rendering path. Needs `playwright install chromium` once.

Trim size is a placeholder (landscape Letter, chosen because the
book's widest content -- 3/4-column entry grids, wide map crops -- is
closer to landscape than portrait) rather than a settled decision;
PLAN.md's Phase 4 still has the real trim-size choice open.
"""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

BOOK_HTML = Path("build/book.html")
BOOK_PDF = Path("build/book.pdf")


def build_pdf(html_path: Path = BOOK_HTML, pdf_path: Path = BOOK_PDF) -> Path:
    if not html_path.exists():
        raise FileNotFoundError(f"{html_path} not found -- run `fishguide build` first")
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(html_path.resolve().as_uri())
        page.emulate_media(media="print")
        page.pdf(
            path=str(pdf_path),
            format="Letter",
            landscape=True,
            print_background=True,
            margin={"top": "0.3in", "bottom": "0.3in", "left": "0.3in", "right": "0.3in"},
        )
        browser.close()
    return pdf_path
