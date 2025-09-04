# app/pdf_gen.py
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from typing import Dict
import textwrap
from datetime import datetime

PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 50
MAX_WIDTH = PAGE_WIDTH - 2*MARGIN
FONT_SIZE_TEXT = 10
LINE_HEIGHT = FONT_SIZE_TEXT + 4

def _draw_wrapped(c, text, x, y, max_width=MAX_WIDTH, font="Helvetica", size=FONT_SIZE_TEXT):
    c.setFont(font, size)
    lines = []
    for paragraph in text.split("\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            lines.append("")
            continue
        wrapped = textwrap.wrap(paragraph, width=95)  # rough wrap; adjust if needed
        lines.extend(wrapped)
    for line in lines:
        c.drawString(x, y, line)
        y -= LINE_HEIGHT
        if y < MARGIN + LINE_HEIGHT:
            c.showPage()
            c.setFont(font, size)
            y = PAGE_HEIGHT - MARGIN
    return y

def build_pdf(meta: Dict, output: Dict) -> bytes:
    """
    meta: {title, url, timestamp}
    output: {summary, expanded, validation}
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    y = PAGE_HEIGHT - MARGIN

    # Title
    title = meta.get("title") or "Enhanced Document"
    c.setFont("Helvetica-Bold", 16)
    c.drawString(MARGIN, y, title)
    y -= 24

    c.setFont("Helvetica", 9)
    c.drawString(MARGIN, y, f"Source: {meta.get('url','')}")
    y -= 14
    ts = meta.get("timestamp")
    if ts:
        try:
            ts_str = datetime.fromtimestamp(float(ts)/1000.0).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            ts_str = str(ts)
    else:
        ts_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    c.drawString(MARGIN, y, f"Generated: {ts_str}")
    y -= 20

    # Summary
    if output.get("summary"):
        c.setFont("Helvetica-Bold", 12)
        c.drawString(MARGIN, y, "Summary")
        y -= 16
        y = _draw_wrapped(c, output["summary"], MARGIN, y)

    # Expanded Context
    if output.get("expanded"):
        y -= 8
        c.setFont("Helvetica-Bold", 12)
        c.drawString(MARGIN, y, "Expanded Context")
        y -= 16
        y = _draw_wrapped(c, output["expanded"], MARGIN, y)

    # Validation
    if output.get("validation"):
        y -= 8
        c.setFont("Helvetica-Bold", 12)
        c.drawString(MARGIN, y, "Validation & Reasoning")
        y -= 16
        y = _draw_wrapped(c, output["validation"], MARGIN, y)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()
