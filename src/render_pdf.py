from __future__ import annotations

import argparse
import html
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)
from pypdf import PdfReader, PdfWriter

from lesson_models import BASE_DIR, clean_for_filename, read_json, write_json


PAGE_SIZE = A5
PAGE_WIDTH, PAGE_HEIGHT = PAGE_SIZE
GOLD = colors.HexColor("#B98A2E")
BLACK = colors.HexColor("#101010")
INK = colors.HexColor("#151515")
MUTED = colors.HexColor("#555555")
LIGHT = colors.HexColor("#F4F1EA")


def _draw_cover(canvas, doc, title: str, today: str, focus: str, lesson_date: str) -> None:
    canvas.saveState()
    canvas.setFillColor(BLACK)
    canvas.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)

    margin = 16 * mm
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(1.2)
    canvas.rect(margin, margin, PAGE_WIDTH - 2 * margin, PAGE_HEIGHT - 2 * margin, fill=0, stroke=1)

    canvas.setStrokeColor(colors.HexColor("#5D4620"))
    canvas.setLineWidth(0.4)
    canvas.line(margin + 10, PAGE_HEIGHT - margin - 36, PAGE_WIDTH - margin - 10, PAGE_HEIGHT - margin - 36)
    canvas.line(margin + 10, margin + 54, PAGE_WIDTH - margin - 10, margin + 54)

    canvas.setFillColor(GOLD)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - margin - 26, today.upper())

    canvas.setFillColor(colors.white)
    text = canvas.beginText()
    text.setTextOrigin(margin + 12, PAGE_HEIGHT - margin - 92)
    text.setFont("Helvetica-Bold", 25)
    for line in ["Tagesdosis", "Strategie", "& Macht"]:
        text.textLine(line)
    canvas.drawText(text)

    canvas.setFillColor(colors.HexColor("#D8C99D"))
    canvas.setFont("Helvetica", 10)
    wrapped_focus = _wrap_plain(focus, 42)
    y = margin + 88
    for line in wrapped_focus[:4]:
        canvas.drawCentredString(PAGE_WIDTH / 2, y, line)
        y -= 13

    canvas.setFillColor(GOLD)
    canvas.setFont("Helvetica", 9)
    canvas.drawCentredString(PAGE_WIDTH / 2, margin + 26, lesson_date)
    canvas.restoreState()


def _wrap_plain(text: str, width: int) -> List[str]:
    words = text.split()
    lines: List[str] = []
    current: List[str] = []
    for word in words:
        candidate = " ".join(current + [word])
        if len(candidate) <= width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def _styles() -> Dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "kicker": ParagraphStyle(
            "Kicker",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=GOLD,
            alignment=TA_CENTER,
            uppercase=True,
            spaceAfter=4,
        ),
        "title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=19,
            leading=23,
            textColor=BLACK,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=14,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=14,
        ),
        "h2": ParagraphStyle(
            "Heading2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13.5,
            leading=17,
            textColor=BLACK,
            spaceBefore=9,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=11.2,
            leading=15.6,
            textColor=INK,
            alignment=TA_LEFT,
            spaceAfter=7,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=12.2,
            textColor=MUTED,
            spaceAfter=5,
        ),
        "quote": ParagraphStyle(
            "Quote",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=11.2,
            leading=15,
            textColor=BLACK,
            leftIndent=9,
            rightIndent=9,
            borderColor=GOLD,
            borderWidth=0.8,
            borderPadding=7,
            backColor=LIGHT,
            spaceBefore=5,
            spaceAfter=11,
        ),
        "question": ParagraphStyle(
            "Question",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10.8,
            leading=14.7,
            leftIndent=12,
            firstLineIndent=-10,
            textColor=INK,
            spaceAfter=5,
        ),
    }


def _paragraphs(body: str, style: ParagraphStyle) -> Iterable[Paragraph]:
    parts = [part.strip() for part in body.split("\n\n") if part.strip()]
    for part in parts:
        escaped = html.escape(part).replace("\n", "<br/>")
        yield Paragraph(escaped, style)


def _single_paragraph(body: str, style: ParagraphStyle) -> Paragraph:
    escaped = html.escape(body.strip()).replace("\n", "<br/>")
    return Paragraph(escaped, style)


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


def _footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#DDDDDD"))
    canvas.setLineWidth(0.3)
    canvas.line(doc.leftMargin, 11 * mm, PAGE_WIDTH - doc.rightMargin, 11 * mm)
    canvas.setFillColor(colors.HexColor("#777777"))
    canvas.setFont("Helvetica", 7.5)
    canvas.drawCentredString(PAGE_WIDTH / 2, 6 * mm, str(doc.page))
    canvas.restoreState()


def lesson_document_title(lesson: Dict[str, Any]) -> str:
    today_key = lesson.get("today_key", "")
    focus = lesson.get("focus_title", "Tagesdosis Strategie & Macht")
    if today_key == "new_law" and focus.startswith("Gesetz "):
        return "Gesetz der Macht Nummer " + focus.removeprefix("Gesetz ")
    if today_key == "new_strategy" and focus.startswith("Strategie "):
        return "Gesetz der Strategie Nummer " + focus.removeprefix("Strategie ")
    if today_key == "review":
        return "Wiederholung Strategie und Macht - " + focus.removeprefix("Wiederholung: ")
    if today_key == "application":
        return focus
    if today_key == "comparison":
        return "Vergleich Strategie und Macht - " + focus
    if today_key == "weekly_review":
        return "Wochenreview Strategie und Macht"
    return focus


def render_lesson_pdf(lesson_json: Path, output_pdf: Path | None = None) -> Path:
    lesson = read_json(lesson_json)
    lesson_date = lesson.get("date") or date.today().isoformat()
    document_title = lesson_document_title(lesson)
    if output_pdf is None:
        filename = f"{clean_for_filename(document_title)}.pdf"
        output_pdf = BASE_DIR / "output" / "pdf" / filename
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    styles = _styles()
    doc = SimpleDocTemplate(
        str(output_pdf),
        pagesize=PAGE_SIZE,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=15 * mm,
        title=document_title,
        author="Codex",
    )

    story: List[Any] = [
        Spacer(1, 1),
        PageBreak(),
        Paragraph(html.escape(lesson["title"]), styles["title"]),
        Paragraph(html.escape(lesson["focus_title"]), styles["subtitle"]),
    ]

    story.append(Paragraph(_numbered_heading(1, f"Heute: {lesson['today']}"), styles["h2"]))
    intro = lesson.get("intro") or lesson.get("subtitle", "")
    if intro:
        story.extend(_paragraphs(intro, styles["body"]))

    story.append(Paragraph(_numbered_heading(2, "Erst Abruf"), styles["h2"]))
    for index, question in enumerate(lesson.get("recall_questions", []), start=1):
        story.append(Paragraph(f"{index}. {html.escape(question)}", styles["question"]))

    section_number = 3
    sections = lesson.get("sections", [])
    for idx, section in enumerate(sections):
        heading = section.get("heading", "")
        if idx == 0 and heading in {"Inhalt", "Gesetz(e)", "Strategie(n)"}:
            heading = _content_label(lesson)
        block: List[Any] = [Paragraph(_numbered_heading(section_number, heading), styles["h2"])]
        block.extend(_paragraphs(section.get("body", ""), styles["body"]))
        story.append(KeepTogether(block))
        section_number += 1

    story.append(Paragraph(_numbered_heading(section_number, "Mini-Aufgabe für heute"), styles["h2"]))
    story.append(_single_paragraph(lesson.get("mini_task", ""), styles["quote"]))

    if lesson.get("quote"):
        story.append(Paragraph("Tagesformel", styles["h2"]))
        story.append(_single_paragraph(lesson["quote"], styles["quote"]))

    doc.build(
        story,
        onFirstPage=lambda canvas, doc: _draw_cover(
            canvas,
            doc,
            lesson["title"],
            lesson["today"],
            lesson["focus_title"],
            lesson_date,
        ),
        onLaterPages=_footer,
    )
    _sanitize_for_send_to_kindle(output_pdf)

    lesson["output_pdf"] = str(output_pdf.relative_to(BASE_DIR))
    write_json(lesson_json, lesson)
    return output_pdf


def _sanitize_for_send_to_kindle(pdf_path: Path) -> None:
    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()
    for page in reader.pages:
        if "/Trans" in page:
            del page["/Trans"]
        writer.add_page(page)

    metadata = reader.metadata or {}
    writer.add_metadata(
        {
            "/Title": metadata.get("/Title", ""),
            "/Author": metadata.get("/Author", "Codex"),
            "/Creator": "Codex",
            "/Producer": "Codex",
        }
    )
    tmp_path = pdf_path.with_suffix(".tmp.pdf")
    with tmp_path.open("wb") as handle:
        writer.write(handle)
    tmp_path.replace(pdf_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a Strategy & Power lesson JSON as Kindle-friendly PDF.")
    parser.add_argument("lesson_json", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pdf_path = render_lesson_pdf(args.lesson_json, args.output)
    print(pdf_path)


if __name__ == "__main__":
    main()
