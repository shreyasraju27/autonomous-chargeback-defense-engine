import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER

OUTPUT_DIR = "output"


def _build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="DossierTitle",
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=19,
        spaceAfter=2,
        textColor=colors.HexColor("#0F172A"),
    ))
    styles.add(ParagraphStyle(
        name="DossierSubtitle",
        fontName="Helvetica",
        fontSize=8.5,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="SectionHeader",
        fontName="Helvetica-Bold",
        fontSize=10.5,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=8,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="BodyTextClean",
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1E293B"),
    ))
    styles.add(ParagraphStyle(
        name="SmallLabel",
        fontName="Helvetica-Bold",
        fontSize=7.5,
        textColor=colors.HexColor("#64748B"),
    ))
    styles.add(ParagraphStyle(
        name="CitationText",
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        textColor=colors.HexColor("#64748B"),
        leading=10,
    ))
    styles.add(ParagraphStyle(
        name="FooterText",
        fontName="Helvetica",
        fontSize=7.5,
        textColor=colors.HexColor("#94A3B8"),
        alignment=TA_CENTER,
    ))
    return styles


def _status_color(recommendation: str):
    mapping = {
        "STRONG_CASE": colors.HexColor("#16A34A"),
        "WEAK_CASE": colors.HexColor("#DC2626"),
        "INSUFFICIENT_EVIDENCE": colors.HexColor("#D97706"),
    }
    return mapping.get(recommendation, colors.HexColor("#475569"))


def generate_dispute_pdf(state: dict) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    order_id = state.get("order_id", "unknown_order")
    filepath = os.path.join(OUTPUT_DIR, f"dispute_{order_id}.pdf")

    styles = _build_styles()
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        topMargin=12 * mm,
        bottomMargin=10 * mm,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
    )

    story = []

    # ---------- Header ----------
    story.append(Paragraph("Dispute Evidence Dossier", styles["DossierTitle"]))
    story.append(Paragraph(
        f"Order {order_id} &nbsp;·&nbsp; Merchant {state.get('merchant_id', 'N/A')}",
        styles["DossierSubtitle"]
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0")))
    story.append(Spacer(1, 6))

    # ---------- Summary metrics table ----------
    risk = state.get("risk_analysis") or {}
    recommendation = risk.get("recommendation", "N/A")
    rec_color = _status_color(recommendation)

    metrics_data = [
        ["RISK SCORE", "RECOMMENDATION", "REASON CODE"],
        [
            f"{risk.get('risk_score', 'N/A')}/100",
            recommendation,
            risk.get("reason_code_response", "N/A"),
        ],
    ]
    metrics_table = Table(metrics_data, colWidths=[55 * mm, 55 * mm, 55 * mm])
    metrics_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 7),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#64748B")),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, 1), 11),
        ("TEXTCOLOR", (1, 1), (1, 1), rec_color),
        ("TEXTCOLOR", (0, 1), (0, 1), colors.HexColor("#0F172A")),
        ("TEXTCOLOR", (2, 1), (2, 1), colors.HexColor("#0F172A")),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("TOPPADDING", (0, 1), (-1, 1), 1),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#E2E8F0")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 5))

    # ---------- Verified Claims ----------
    claims = risk.get("claims", [])
    if claims:
        story.append(Paragraph("Verified Claims", styles["SectionHeader"]))
        for i, c in enumerate(claims, 1):
            story.append(Paragraph(f"{i}. {c.get('claim', '')}", styles["BodyTextClean"]))
            story.append(Paragraph(f"Source: {c.get('source_query', '')}", styles["CitationText"]))
            story.append(Spacer(1, 3))

    # ---------- Evidence Gaps ----------
    gaps = risk.get("evidence_gaps", [])
    if gaps:
        story.append(Paragraph("Evidence Gaps", styles["SectionHeader"]))
        for g in gaps:
            story.append(Paragraph(f"• {g}", styles["BodyTextClean"]))
        story.append(Spacer(1, 3))

    # ---------- Evidence table ----------
    evidence_result = state.get("evidence_result") or {}
    evidence_items = evidence_result.get("evidence", [])
    if evidence_items:
        story.append(Paragraph("Evidence Records", styles["SectionHeader"]))
        for item in evidence_items:
            data = item.get("data", {})
            rows = [[Paragraph(f"<b>{k}</b>", styles["BodyTextClean"]),
                     Paragraph(str(v), styles["BodyTextClean"])] for k, v in data.items()]
            t = Table(rows, colWidths=[42 * mm, 113 * mm])
            t.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#F1F5F9")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F8FAFC")),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(t)
            story.append(Spacer(1, 4))

    # ---------- Blocked query attempts ----------
    blocked = evidence_result.get("blocked_attempts", [])
    if blocked:
        story.append(Paragraph("Blocked Query Attempts — Security Guardrail", styles["SectionHeader"]))
        for b in blocked:
            story.append(Paragraph(f"<font color='#DC2626'><b>Blocked:</b></font> {b.get('query', '')}",
                                     styles["BodyTextClean"]))
            story.append(Paragraph(f"Reason: {b.get('reason', '')}", styles["CitationText"]))
            story.append(Spacer(1, 3))

    # ---------- Narrative summary ----------
    dossier = state.get("dossier") or {}
    if dossier.get("summary"):
        story.append(Paragraph("Summary Narrative", styles["SectionHeader"]))
        story.append(Paragraph(dossier["summary"], styles["BodyTextClean"]))

    # ---------- Footer ----------
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0")))
    story.append(Spacer(1, 3))
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    story.append(Paragraph(
        f"Reviewed and approved by Risk Officer &nbsp;·&nbsp; Generated {timestamp}",
        styles["FooterText"]
    ))

    doc.build(story)
    return filepath