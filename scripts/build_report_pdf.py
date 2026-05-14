"""Akademik_Rapor.md dosyasını sade, akademik PDF olarak üretir.

Düzen:
  - Kapak sayfası (başlık + öğrenci bilgileri)
  - İçindekiler (otomatik)
  - Tek sütun, justified gövde metni
  - Numaralı bölümler, alt başlıklar
  - Her sayfada üst başlık ve sayfa numarası
  - İstanbul 1453 örneği için ek bir görsel akış kutusu

Kullanım:
    python scripts/build_report_pdf.py
"""

from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents


ROOT = Path(__file__).resolve().parents[1]
MD_PATH = ROOT / "docs" / "Akademik_Rapor.md"
PDF_PATH = ROOT / "docs" / "Akademik_Rapor.pdf"

FONT_REGULAR = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
pdfmetrics.registerFont(TTFont("Body", FONT_REGULAR))


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
styles = getSampleStyleSheet()

s_body = ParagraphStyle(
    "BodyTR",
    fontName="Body",
    fontSize=10.5,
    leading=15,
    alignment=TA_JUSTIFY,
    spaceAfter=6,
    textColor=colors.HexColor("#111111"),
)
s_h1 = ParagraphStyle(
    "H1",
    fontName="Body",
    fontSize=15,
    leading=19,
    textColor=colors.HexColor("#152238"),
    spaceBefore=14,
    spaceAfter=8,
)
s_h2 = ParagraphStyle(
    "H2",
    fontName="Body",
    fontSize=12.5,
    leading=16,
    textColor=colors.HexColor("#1f3a5f"),
    spaceBefore=10,
    spaceAfter=5,
)
s_h3 = ParagraphStyle(
    "H3",
    fontName="Body",
    fontSize=11,
    leading=14,
    textColor=colors.HexColor("#2c4f76"),
    spaceBefore=7,
    spaceAfter=3,
)
s_quote = ParagraphStyle(
    "Quote",
    parent=s_body,
    leftIndent=18,
    rightIndent=10,
    textColor=colors.HexColor("#333333"),
    fontName="Body",
    fontSize=10.2,
    leading=14,
    spaceAfter=6,
)
s_caption = ParagraphStyle(
    "Caption",
    fontName="Body",
    fontSize=9,
    leading=11,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#555555"),
    spaceAfter=6,
)
s_cover_title = ParagraphStyle(
    "CoverTitle",
    fontName="Body",
    fontSize=22,
    leading=26,
    alignment=TA_CENTER,
    spaceAfter=14,
)
s_cover_sub = ParagraphStyle(
    "CoverSub",
    fontName="Body",
    fontSize=13,
    leading=18,
    alignment=TA_CENTER,
    spaceAfter=10,
    textColor=colors.HexColor("#444444"),
)
s_cover_meta = ParagraphStyle(
    "CoverMeta",
    fontName="Body",
    fontSize=11,
    leading=15,
    alignment=TA_CENTER,
    spaceAfter=4,
    textColor=colors.HexColor("#222222"),
)
s_running = ParagraphStyle(
    "Running",
    fontName="Body",
    fontSize=8,
    leading=10,
    textColor=colors.HexColor("#555555"),
)


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------
def inline_md_to_rl(text: str) -> str:
    """Basit Markdown -> ReportLab paragraf metni."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"`([^`]+)`", r"<font face='Courier'>\1</font>", text)
    return text


def make_table(rows: list[list[str]]) -> Table:
    n = max(len(r) for r in rows)
    rows = [r + [""] * (n - len(r)) for r in rows]
    body = []
    for ri, r in enumerate(rows):
        wrapped = []
        for c in r:
            wrapped.append(Paragraph(inline_md_to_rl(c), ParagraphStyle(
                "Cell", parent=s_body, fontName="Body",
                fontSize=9.2, leading=11.4, spaceAfter=0, alignment=TA_LEFT)))
        body.append(wrapped)

    # 165mm content width split equally
    col_w = 165 * mm / n
    tbl = Table(body, colWidths=[col_w] * n, repeatRows=1, hAlign="LEFT")
    tbl.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Body"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9eef5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#152238")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#8f9bb3")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ]
        )
    )
    return tbl


def make_flow_box() -> Table:
    """İstanbul 1453 örneği için sade görsel akış kutusu."""

    def cell(text, bg, border, fg="#152238"):
        p = Paragraph(
            f"<para align='center'><b>{text}</b></para>",
            ParagraphStyle(
                "FlowCell",
                fontName="Body",
                fontSize=10,
                leading=13,
                alignment=TA_CENTER,
                textColor=colors.HexColor(fg),
            ),
        )
        t = Table([[p]], colWidths=[45 * mm], rowHeights=[14 * mm])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg)),
                    ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor(border)),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        return t

    def arrow_label(text):
        return Paragraph(
            f"<para align='center'><font size='9' color='#444444'>{text}</font></para>",
            s_caption,
        )

    alice = cell("Alice (dürüst)", "#e6f4ea", "#34a853", "#0d6b2a")
    mallory = cell("Mallory (saldırgan)", "#fde7e9", "#d93025", "#8a0e1a")
    sybil = cell("Sybil (yardımcı saldırgan)", "#fde7e9", "#d93025", "#8a0e1a")
    cm = cell("CHECK-MAS", "#e8eefc", "#1a73e8", "#0b3d91")
    pass_lbl = cell("PASS (Φ=1.00)", "#e6f4ea", "#34a853", "#0d6b2a")
    block1 = cell("BLOCK (Φ=0.30)", "#fde7e9", "#d93025", "#8a0e1a")
    block2 = cell("BLOCK (Φ=0.50)", "#fde7e9", "#d93025", "#8a0e1a")
    result = cell("Sonuç: SUPPORTED", "#fff4cd", "#f9a825", "#7a5300")

    row1 = Table(
        [[alice, arrow_label("→"), cm, arrow_label("→"), pass_lbl]],
        colWidths=[45 * mm, 12 * mm, 45 * mm, 12 * mm, 45 * mm],
    )
    row2 = Table(
        [[mallory, arrow_label("→"), Paragraph("", s_caption), arrow_label("→"), block1]],
        colWidths=[45 * mm, 12 * mm, 45 * mm, 12 * mm, 45 * mm],
    )
    row3 = Table(
        [[sybil, arrow_label("→"), Paragraph("", s_caption), arrow_label("→"), block2]],
        colWidths=[45 * mm, 12 * mm, 45 * mm, 12 * mm, 45 * mm],
    )
    row4 = Table(
        [[Paragraph("", s_caption), Paragraph("", s_caption), arrow_label("↓"), Paragraph("", s_caption), Paragraph("", s_caption)]],
        colWidths=[45 * mm, 12 * mm, 45 * mm, 12 * mm, 45 * mm],
    )
    row5 = Table(
        [[Paragraph("", s_caption), Paragraph("", s_caption), result, Paragraph("", s_caption), Paragraph("", s_caption)]],
        colWidths=[45 * mm, 12 * mm, 45 * mm, 12 * mm, 45 * mm],
    )

    container = Table(
        [[row1], [Spacer(1, 2)], [row2], [Spacer(1, 2)], [row3], [Spacer(1, 4)], [row4], [row5]],
        colWidths=[165 * mm],
    )
    container.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return container


# ---------------------------------------------------------------------------
# Markdown parser
# ---------------------------------------------------------------------------
def parse_md(md_text: str):
    flowables: list = []
    lines = md_text.splitlines()

    list_buf: list[str] = []
    pending_table: list[str] = []
    quote_buf: list[str] = []

    def flush_list():
        nonlocal list_buf
        if not list_buf:
            return
        items = [
            ListItem(Paragraph(inline_md_to_rl(x), s_body), leftIndent=10)
            for x in list_buf
        ]
        flowables.append(ListFlowable(items, bulletType="bullet", leftIndent=14))
        flowables.append(Spacer(1, 3))
        list_buf = []

    def flush_quote():
        nonlocal quote_buf
        if not quote_buf:
            return
        text = " ".join(quote_buf)
        flowables.append(Paragraph(inline_md_to_rl(text), s_quote))
        quote_buf = []

    def flush_table():
        nonlocal pending_table
        if not pending_table:
            return
        rows = []
        for line in pending_table:
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            if cols and all(re.fullmatch(r"[-: ]+", c or "-") for c in cols):
                continue
            rows.append(cols)
        if len(rows) >= 2:
            flowables.append(KeepTogether(make_table(rows)))
            flowables.append(Spacer(1, 6))
        pending_table = []

    h1_re = re.compile(r"^#\s+(.*)$")
    h2_re = re.compile(r"^##\s+(.*)$")
    h3_re = re.compile(r"^###\s+(.*)$")

    # Skip lines until first "## Özet" (cover info already on cover page)
    started = False
    for raw in lines:
        line = raw.rstrip("\n")
        if not started:
            if line.startswith("## Özet"):
                started = True
            else:
                continue

        # Code fences - skip (rapor metni içinde uzun kod yok)
        if line.startswith("```"):
            continue

        if not line.strip():
            flush_list()
            flush_table()
            flush_quote()
            flowables.append(Spacer(1, 4))
            continue

        if line.strip() == "---":
            flush_list()
            flush_table()
            flush_quote()
            flowables.append(HRFlowable(width="100%", thickness=0.4, color=colors.HexColor("#bbbbbb")))
            flowables.append(Spacer(1, 4))
            continue

        if line.strip().startswith("|") and line.strip().endswith("|"):
            flush_list()
            flush_quote()
            pending_table.append(line)
            continue
        flush_table()

        if line.startswith("> "):
            flush_list()
            quote_buf.append(line[2:].strip())
            continue
        flush_quote()

        m = h1_re.match(line)
        if m:
            flush_list()
            heading = m.group(1).strip()
            flowables.append(Paragraph(f"<b>{inline_md_to_rl(heading)}</b>", s_h1))
            continue

        m = h2_re.match(line)
        if m:
            flush_list()
            heading = m.group(1).strip()
            # markdown'da ## her zaman ana bölüm
            flowables.append(Paragraph(f"<b>{inline_md_to_rl(heading)}</b>", s_h1))
            continue

        m = h3_re.match(line)
        if m:
            flush_list()
            heading = m.group(1).strip()
            # markdown'da ### her zaman alt bölüm
            flowables.append(Paragraph(f"<b>{inline_md_to_rl(heading)}</b>", s_h2))
            # Akış kutusunu 5.1 başlığından sonra ekle
            if heading.startswith("5.1"):
                flowables.append(Spacer(1, 4))
                flowables.append(KeepTogether(make_flow_box()))
                flowables.append(Paragraph("Şekil 1. CHECK-MAS, üç ajanı paralel olarak değerlendirir; çoğunluk saldırgan olsa da karar dürüst ajan üzerinden verilir.", s_caption))
                flowables.append(Spacer(1, 4))
            continue

        if line.lstrip().startswith("- "):
            list_buf.append(line.lstrip()[2:].strip())
            continue

        flush_list()
        flowables.append(Paragraph(inline_md_to_rl(line), s_body))

    flush_list()
    flush_table()
    flush_quote()
    return flowables


# ---------------------------------------------------------------------------
# Page templates
# ---------------------------------------------------------------------------
PAGE_W, PAGE_H = A4
L_MARGIN = 22 * mm
R_MARGIN = 22 * mm
T_MARGIN = 22 * mm
B_MARGIN = 20 * mm


def draw_header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Body", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    # Header
    canvas.drawString(
        L_MARGIN, PAGE_H - 12 * mm,
        "CHECK-MAS — Ahmet Selim Arıcan (230212033)"
    )
    canvas.setLineWidth(0.3)
    canvas.setStrokeColor(colors.HexColor("#aaaaaa"))
    canvas.line(L_MARGIN, PAGE_H - 14 * mm, PAGE_W - R_MARGIN, PAGE_H - 14 * mm)
    # Footer
    canvas.drawRightString(PAGE_W - R_MARGIN, 10 * mm, f"Sayfa {doc.page}")
    canvas.restoreState()


def cover_page_template():
    frame = Frame(L_MARGIN, B_MARGIN, PAGE_W - L_MARGIN - R_MARGIN,
                  PAGE_H - T_MARGIN - B_MARGIN, id="cover")
    return PageTemplate(id="Cover", frames=[frame])


def normal_page_template():
    frame = Frame(L_MARGIN, B_MARGIN, PAGE_W - L_MARGIN - R_MARGIN,
                  PAGE_H - T_MARGIN - B_MARGIN, id="normal")
    return PageTemplate(id="Normal", frames=[frame], onPage=draw_header_footer)


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
class ReportDoc(BaseDocTemplate):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.toc_built = False

    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):
            return
        text = flowable.getPlainText().strip()
        if not text:
            return
        # Türkçe karakter güvenli filtre: kapak/TOC başlıkları içindekilere girmesin
        if text in {"İçindekiler", "Akademik Rapor", "AKADEMİK RAPOR", "Hazırlayan"}:
            return
        style_name = flowable.style.name
        if style_name == "H1":
            self.notify("TOCEntry", (0, text, self.page))
        elif style_name == "H2":
            self.notify("TOCEntry", (1, text, self.page))


def build_pdf():
    md_text = MD_PATH.read_text(encoding="utf-8")

    doc = ReportDoc(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=L_MARGIN,
        rightMargin=R_MARGIN,
        topMargin=T_MARGIN,
        bottomMargin=B_MARGIN,
        title="CHECK-MAS",
        author="Ahmet Selim Arıcan",
    )
    doc.addPageTemplates([cover_page_template(), normal_page_template()])

    story: list = []

    # ---- Cover page ----
    story.append(Spacer(1, 50 * mm))
    story.append(Paragraph(
        "CHECK-MAS",
        ParagraphStyle("BigTitle", parent=s_cover_title, fontSize=32, leading=38),
    ))
    story.append(Paragraph(
        "Çok Ajanlı LLM Sistemlerinde Prompt Injection Saldırılarına Karşı "
        "Semantik Bir Güvenlik Katmanı",
        s_cover_sub,
    ))
    story.append(Spacer(1, 25 * mm))
    story.append(HRFlowable(width="60%", thickness=0.7, color=colors.HexColor("#999999"),
                            spaceBefore=2, spaceAfter=10, hAlign="CENTER"))
    story.append(Paragraph("<b>Hazırlayan</b>", s_cover_meta))
    story.append(Paragraph("Ahmet Selim Arıcan", s_cover_meta))
    story.append(Paragraph("Öğrenci Numarası: 230212033", s_cover_meta))
    story.append(Paragraph("Yapay Zeka Mühendisliği", s_cover_meta))

    # ---- TOC page ----
    story.append(PageBreak())
    # Switch to normal template from here on
    from reportlab.platypus.doctemplate import NextPageTemplate
    # NextPageTemplate uygulanmadan önce sayfa içinde olmamalı.
    # Cover sonrası header/footer'lı template'e geçiyoruz:
    story.insert(len(story) - 1, NextPageTemplate("Normal"))

    toc_heading = ParagraphStyle(
        "TOCHeading", parent=s_h1, fontName="Body",
        fontSize=16, leading=20, alignment=TA_CENTER,
        textColor=colors.HexColor("#152238"), spaceAfter=10,
    )
    story.append(Paragraph("İçindekiler", toc_heading))
    story.append(HRFlowable(width="40%", thickness=0.5,
                            color=colors.HexColor("#999999"),
                            spaceBefore=2, spaceAfter=10, hAlign="CENTER"))
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle("TOC1", fontName="Body", fontSize=10.5, leading=15,
                       textColor=colors.HexColor("#152238"), leftIndent=0,
                       firstLineIndent=0, spaceAfter=2),
        ParagraphStyle("TOC2", fontName="Body", fontSize=9.5, leading=13,
                       textColor=colors.HexColor("#444444"), leftIndent=18,
                       firstLineIndent=0, spaceAfter=1),
    ]
    story.append(toc)
    story.append(PageBreak())

    # ---- Body parsed from markdown ----
    story.extend(parse_md(md_text))

    # Multi-pass build so the TOC gets the real page numbers
    doc.multiBuild(story)

    return PDF_PATH


if __name__ == "__main__":
    out = build_pdf()
    print(f"PDF üretildi: {out}")
