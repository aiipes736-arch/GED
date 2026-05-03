"""Monthly report generation for MHCGED.

Generates a PDF report containing:
- Institutional header (logo + ministry + period)
- Top 5 most downloaded documents
- Top active agents
- Signature footer (admin name + date)
"""
import io
import os
from datetime import datetime, timezone
from typing import Optional

import requests
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

# Congo institutional colors
GREEN = colors.HexColor("#0F4C3A")
GREEN_LIGHT = colors.HexColor("#E8F3ED")
YELLOW = colors.HexColor("#FCD116")
RED = colors.HexColor("#DC241F")
GRAY_TEXT = colors.HexColor("#374151")
GRAY_LIGHT = colors.HexColor("#F3F4F6")

LOGO_URL = "https://customer-assets.emergentagent.com/job_ada3efd6-4e4c-4295-902b-4abf286154c2/artifacts/dmk2iip2_Photo%201.jpeg"

MONTHS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]


def _fetch_logo_bytes() -> Optional[bytes]:
    try:
        r = requests.get(LOGO_URL, timeout=10)
        r.raise_for_status()
        return r.content
    except Exception:
        return None


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", parent=base["Title"],
            fontName="Helvetica-Bold", fontSize=20, leading=24,
            textColor=GREEN, alignment=TA_LEFT, spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base["Normal"],
            fontName="Helvetica", fontSize=10, leading=14,
            textColor=GRAY_TEXT, alignment=TA_LEFT, spaceAfter=4,
        ),
        "eyebrow": ParagraphStyle(
            "eyebrow", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=8, leading=12,
            textColor=GREEN, alignment=TA_LEFT, spaceAfter=4,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"],
            fontName="Helvetica-Bold", fontSize=13, leading=18,
            textColor=GREEN, alignment=TA_LEFT, spaceBefore=14, spaceAfter=8,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"],
            fontName="Helvetica", fontSize=10, leading=14,
            textColor=GRAY_TEXT, alignment=TA_LEFT,
        ),
        "small": ParagraphStyle(
            "small", parent=base["Normal"],
            fontName="Helvetica", fontSize=8, leading=11,
            textColor=colors.HexColor("#6B7280"), alignment=TA_LEFT,
        ),
        "small_right": ParagraphStyle(
            "small_right", parent=base["Normal"],
            fontName="Helvetica", fontSize=8, leading=11,
            textColor=colors.HexColor("#6B7280"), alignment=TA_RIGHT,
        ),
    }


def _build_header(s, period_label: str, scope_label: str, logo_bytes: Optional[bytes]):
    elements = []
    # Top color bar (Congo flag)
    bar = Table([[""]], colWidths=[17 * cm], rowHeights=[0.18 * cm])
    bar.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), GREEN),
    ]))
    elements.append(bar)
    elements.append(Spacer(1, 0.4 * cm))

    # Logo + titles
    if logo_bytes:
        try:
            logo = Image(io.BytesIO(logo_bytes), width=2.4 * cm, height=2.4 * cm)
        except Exception:
            logo = Paragraph("", s["body"])
    else:
        logo = Paragraph("", s["body"])

    titles = [
        Paragraph("RÉPUBLIQUE DU CONGO", s["eyebrow"]),
        Paragraph("Ministère des Hydrocarbures", s["title"]),
        Paragraph("Direction des Systèmes d'Information et de la Communication", s["subtitle"]),
        Paragraph("<b>MHCGED</b> — Gestion Électronique des Documents", s["subtitle"]),
    ]

    header_tbl = Table(
        [[logo, titles]],
        colWidths=[3.0 * cm, 13.5 * cm],
    )
    header_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    elements.append(header_tbl)
    elements.append(Spacer(1, 0.3 * cm))

    # Period block
    period_tbl = Table(
        [[
            Paragraph("RAPPORT MENSUEL D'ACTIVITÉ", s["eyebrow"]),
            Paragraph(period_label, ParagraphStyle("period", parent=s["body"],
                fontName="Helvetica-Bold", fontSize=11, alignment=TA_RIGHT, textColor=GREEN)),
        ]],
        colWidths=[8 * cm, 8.5 * cm],
    )
    period_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GREEN_LIGHT),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(period_tbl)
    elements.append(Paragraph(f"Périmètre : {scope_label}", s["small"]))
    elements.append(Spacer(1, 0.5 * cm))
    return elements


def _section_top_documents(s, top_docs):
    elements = [Paragraph("📄 Top 5 documents les plus téléchargés", s["h2"])]
    if not top_docs:
        elements.append(Paragraph("Aucun téléchargement enregistré sur cette période.", s["small"]))
        return elements

    rows = [["#", "Titre", "Téléchargements"]]
    for i, d in enumerate(top_docs, 1):
        rows.append([str(i), d.get("title", "—"), str(d.get("count", 0))])

    tbl = Table(rows, colWidths=[1.2 * cm, 12.5 * cm, 3 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRAY_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E5E7EB")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    elements.append(tbl)
    return elements


def _section_top_agents(s, top_agents):
    elements = [Paragraph("👤 Agents les plus actifs", s["h2"])]
    if not top_agents:
        elements.append(Paragraph("Aucune activité d'agent enregistrée sur cette période.", s["small"]))
        return elements

    rows = [["#", "Agent", "Actions"]]
    for i, a in enumerate(top_agents, 1):
        rows.append([str(i), a.get("name", "—"), str(a.get("count", 0))])

    tbl = Table(rows, colWidths=[1.2 * cm, 12.5 * cm, 3 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRAY_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E5E7EB")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    elements.append(tbl)
    return elements


def _section_signature(s, signed_by_name: str, signed_by_role: str):
    elements = [Spacer(1, 1.5 * cm)]
    today_str = datetime.now(timezone.utc).strftime("%d/%m/%Y")

    sig_table = Table(
        [
            [Paragraph("Fait à Brazzaville, le " + today_str, s["body"]), ""],
            ["", ""],
            [Paragraph(f"<b>{signed_by_name}</b>", s["body"]),
             Paragraph("Signature et cachet", s["small_right"])],
            [Paragraph(signed_by_role, s["small"]), ""],
            ["", ""],
            ["", ""],
        ],
        colWidths=[10 * cm, 6.5 * cm],
        rowHeights=[0.7 * cm, 0.3 * cm, 0.6 * cm, 0.5 * cm, 0.4 * cm, 1.2 * cm],
    )
    sig_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEABOVE", (1, 5), (1, 5), 0.6, GREEN),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    elements.append(KeepTogether(sig_table))
    return elements


def _footer(canvas, doc):
    canvas.saveState()
    page_w, _ = A4
    canvas.setStrokeColor(GREEN)
    canvas.setLineWidth(0.4)
    canvas.line(2 * cm, 1.4 * cm, page_w - 2 * cm, 1.4 * cm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#6B7280"))
    canvas.drawString(2 * cm, 1.0 * cm, "MHCGED — Ministère des Hydrocarbures · République du Congo · Document confidentiel")
    canvas.drawRightString(page_w - 2 * cm, 1.0 * cm, f"Page {doc.page}")
    canvas.restoreState()


def build_monthly_report_pdf(
    *,
    year: int,
    month: int,
    scope_label: str,
    top_docs: list,
    top_agents: list,
    signed_by_name: str,
    signed_by_role: str,
) -> bytes:
    """Build the monthly PDF report and return its bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=1.5 * cm, bottomMargin=2 * cm,
        title=f"Rapport mensuel MHCGED {month:02d}/{year}",
        author="MHCGED",
    )
    s = _styles()
    period_label = f"{MONTHS_FR[month - 1].capitalize()} {year}"
    logo_bytes = _fetch_logo_bytes()

    flow = []
    flow += _build_header(s, period_label, scope_label, logo_bytes)
    flow += _section_top_documents(s, top_docs)
    flow += _section_top_agents(s, top_agents)
    flow += _section_signature(s, signed_by_name, signed_by_role)

    doc.build(flow, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()
