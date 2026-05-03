from __future__ import annotations

import argparse
import html
import uuid
import zipfile
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

from lesson_models import BASE_DIR, clean_for_filename, read_json, write_json
from render_pdf import lesson_document_title


def _xhtml_page(title: str, body: str) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="de" xml:lang="de">
<head>
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
{body}
</body>
</html>
"""


def _paragraphs(text: str) -> str:
    parts = [part.strip() for part in text.split("\n\n") if part.strip()]
    return "\n".join(f"<p>{html.escape(part).replace(chr(10), '<br/>')}</p>" for part in parts)


def _blockquote(text: str) -> str:
    return f"<blockquote>{html.escape(text.strip()).replace(chr(10), '<br/>')}</blockquote>"


def _numbered_heading(index: int, heading: str) -> str:
    return f"{index}. {heading}"


def _content_label(lesson: Dict[str, Any]) -> str:
    today_key = lesson.get("today_key", "")
    if today_key == "new_law":
        return "Gesetz(e)"
    if today_key == "new_strategy":
        return "Strategie(n)"
    if today_key == "review":
        return "Wiederholung"
    if today_key == "application":
        return "Fallanalyse"
    if today_key == "comparison":
        return "Vergleich"
    if today_key == "weekly_review":
        return "Wochenreview"
    return "Inhalt"


def _lesson_body(lesson: Dict[str, Any]) -> str:
    chunks: List[str] = [
        f"<h1>{html.escape(lesson.get('title', 'Tagesdosis Strategie &amp; Macht'))}</h1>",
        f"<p class=\"subtitle\">{html.escape(lesson.get('focus_title', ''))}</p>",
    ]
    intro = lesson.get("intro") or lesson.get("subtitle", "")
    today_heading = _numbered_heading(1, f"Heute: {lesson.get('today', '')}")
    chunks.append(f"<h2>{html.escape(today_heading)}</h2>")
    if intro:
        chunks.append(_paragraphs(intro))

    chunks.append(f"<h2>{html.escape(_numbered_heading(2, 'Erst Abruf'))}</h2>")
    chunks.append("<ol>")
    for question in lesson.get("recall_questions", []):
        chunks.append(f"<li>{html.escape(question)}</li>")
    chunks.append("</ol>")

    section_number = 3
    sections = lesson.get("sections", [])
    for idx, section in enumerate(sections):
        heading = section.get("heading", "")
        if idx == 0 and heading in {"Inhalt", "Gesetz(e)", "Strategie(n)"}:
            heading = _content_label(lesson)
        chunks.append(f"<h2>{html.escape(_numbered_heading(section_number, heading))}</h2>")
        chunks.append(_paragraphs(section.get("body", "")))
        section_number += 1

    chunks.append(f"<h2>{html.escape(_numbered_heading(section_number, 'Mini-Aufgabe für heute'))}</h2>")
    chunks.append(_blockquote(lesson.get("mini_task", "")))
    if lesson.get("quote"):
        chunks.append("<h2>Tagesformel</h2>")
        chunks.append(_blockquote(lesson["quote"]))
    return "\n".join(chunks)


def _cover_body(lesson: Dict[str, Any], document_title: str) -> str:
    lesson_date = lesson.get("date") or date.today().isoformat()
    return f"""
<section class="cover">
  <p class="kicker">{html.escape(lesson.get('today', '')).upper()}</p>
  <h1>Tagesdosis<br/>Strategie<br/>&amp; Macht</h1>
  <p class="cover-focus">{html.escape(document_title)}</p>
  <p class="date">{html.escape(lesson_date)}</p>
</section>
"""


def render_lesson_epub(lesson_json: Path, output_epub: Path | None = None) -> Path:
    lesson = read_json(lesson_json)
    document_title = lesson_document_title(lesson)
    if output_epub is None:
        output_epub = BASE_DIR / "output" / "epub" / f"{clean_for_filename(document_title)}.epub"
    output_epub.parent.mkdir(parents=True, exist_ok=True)

    book_id = f"urn:uuid:{uuid.uuid4()}"
    modified = f"{date.today().isoformat()}T00:00:00Z"
    stylesheet = """
body {
  font-family: serif;
  line-height: 1.45;
  margin: 0;
  padding: 1.2em;
}
h1, h2 {
  font-family: sans-serif;
  line-height: 1.15;
}
h1 {
  font-size: 1.8em;
  margin-bottom: 0.25em;
}
h2 {
  font-size: 1.25em;
  margin-top: 1.2em;
  margin-bottom: 0.35em;
}
p, li {
  font-size: 1em;
}
blockquote {
  border-left: 0.2em solid #b98a2e;
  margin: 1em 0;
  padding: 0.6em 0.8em;
  background: #f4f1ea;
  font-weight: bold;
}
.kicker {
  color: #b98a2e;
  font-family: sans-serif;
  font-weight: bold;
  letter-spacing: 0.04em;
  text-align: center;
}
.subtitle {
  color: #555;
  font-family: sans-serif;
  text-align: center;
}
.cover {
  background: #101010;
  color: white;
  min-height: 90vh;
  padding: 2em;
  text-align: left;
}
.cover h1 {
  color: white;
  font-size: 2.4em;
  margin-top: 1.4em;
}
.cover-focus, .date {
  color: #d8c99d;
  font-family: sans-serif;
  margin-top: 3em;
  text-align: center;
}
"""
    container = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""
    content_opf = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="de">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">{book_id}</dc:identifier>
    <dc:title>{html.escape(document_title)}</dc:title>
    <dc:creator id="creator">Codex</dc:creator>
    <dc:language>de</dc:language>
    <meta property="dcterms:modified">{modified}</meta>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="styles" href="styles.css" media-type="text/css"/>
    <item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>
    <item id="chapter" href="chapter.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="cover"/>
    <itemref idref="chapter"/>
  </spine>
</package>
"""
    nav = _xhtml_page(
        "Inhalt",
        f"""
<nav epub:type="toc" xmlns:epub="http://www.idpf.org/2007/ops">
  <h1>Inhalt</h1>
  <ol>
    <li><a href="cover.xhtml">Titel</a></li>
    <li><a href="chapter.xhtml">{html.escape(document_title)}</a></li>
  </ol>
</nav>
""",
    )
    cover = _xhtml_page(document_title, _cover_body(lesson, document_title))
    chapter = _xhtml_page(document_title, _lesson_body(lesson))

    if output_epub.exists():
        output_epub.unlink()
    with zipfile.ZipFile(output_epub, "w") as epub:
        epub.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        epub.writestr("META-INF/container.xml", container, compress_type=zipfile.ZIP_DEFLATED)
        epub.writestr("OEBPS/content.opf", content_opf, compress_type=zipfile.ZIP_DEFLATED)
        epub.writestr("OEBPS/nav.xhtml", nav, compress_type=zipfile.ZIP_DEFLATED)
        epub.writestr("OEBPS/styles.css", stylesheet, compress_type=zipfile.ZIP_DEFLATED)
        epub.writestr("OEBPS/cover.xhtml", cover, compress_type=zipfile.ZIP_DEFLATED)
        epub.writestr("OEBPS/chapter.xhtml", chapter, compress_type=zipfile.ZIP_DEFLATED)

    lesson["output_epub"] = str(output_epub.relative_to(BASE_DIR))
    write_json(lesson_json, lesson)
    return output_epub


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a Strategy & Power lesson JSON as EPUB.")
    parser.add_argument("lesson_json", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    epub_path = render_lesson_epub(args.lesson_json, args.output)
    print(epub_path)


if __name__ == "__main__":
    main()
