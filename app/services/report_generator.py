"""Medical PDF Report Generator for MedExtract Clinical Assistant"""
import os
from datetime import datetime
from collections import defaultdict

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.lib import colors

from app.core.config import settings
from app.core.schemas import ClassificationResult

# ── Colour palette ────────────────────────────────────────────────────────────
TEAL       = colors.HexColor("#0d6e6e")
LIGHT_TEAL = colors.HexColor("#e6f4f4")
DARK       = colors.HexColor("#1a1a1a")
GREY_BG    = colors.HexColor("#f5f5f5")
RED_FLAG   = colors.HexColor("#c0392b")
GREEN_FLAG = colors.HexColor("#1a7a4a")
AMBER_FLAG = colors.HexColor("#d35400")
BLUE_LINK  = colors.HexColor("#1f77b4")
WHITE      = colors.white

FLAG_COLOURS = {
    "HIGH": RED_FLAG, "H": RED_FLAG,
    "LOW":  BLUE_LINK, "L": BLUE_LINK,
    "CRITICAL": RED_FLAG,
    "ABNORMAL": AMBER_FLAG,
    "NORMAL": GREEN_FLAG, "N": GREEN_FLAG,
}

# ── Shared paragraph styles used inside table cells ───────────────────────────
_SS = getSampleStyleSheet()

CELL       = ParagraphStyle("cell",   parent=_SS["Normal"], fontSize=8,
                             leading=11, wordWrap="CJK")
CELL_BOLD  = ParagraphStyle("cellb",  parent=_SS["Normal"], fontSize=8,
                             leading=11, fontName="Helvetica-Bold", wordWrap="CJK")
CELL_HDR   = ParagraphStyle("cellh",  parent=_SS["Normal"], fontSize=8,
                             leading=11, fontName="Helvetica-Bold",
                             textColor=WHITE, wordWrap="CJK")
CELL_RED   = ParagraphStyle("cellr",  parent=_SS["Normal"], fontSize=8,
                             leading=11, fontName="Helvetica-Bold",
                             textColor=RED_FLAG, wordWrap="CJK")
CELL_BLUE  = ParagraphStyle("cellbl", parent=_SS["Normal"], fontSize=8,
                             leading=11, fontName="Helvetica-Bold",
                             textColor=BLUE_LINK, wordWrap="CJK")
CELL_GREEN = ParagraphStyle("cellg",  parent=_SS["Normal"], fontSize=8,
                             leading=11, fontName="Helvetica-Bold",
                             textColor=GREEN_FLAG, wordWrap="CJK")
CELL_AMBER = ParagraphStyle("cella",  parent=_SS["Normal"], fontSize=8,
                             leading=11, fontName="Helvetica-Bold",
                             textColor=AMBER_FLAG, wordWrap="CJK")


def _p(text: str, style=None) -> Paragraph:
    """Wrap a string in a Paragraph so ReportLab wraps it inside table cells."""
    return Paragraph(_safe(str(text or "—")), style or CELL)


def _safe(v: str) -> str:
    return str(v).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _flag_cell(flag: str) -> Paragraph:
    flag = (flag or "").upper()
    style_map = {
        "HIGH": CELL_RED, "H": CELL_RED,
        "CRITICAL": CELL_RED,
        "LOW": CELL_BLUE, "L": CELL_BLUE,
        "ABNORMAL": CELL_AMBER,
        "NORMAL": CELL_GREEN, "N": CELL_GREEN,
    }
    return Paragraph(_safe(flag or "—"), style_map.get(flag, CELL))


# ── Table style builder ───────────────────────────────────────────────────────

def _table_style(header_color=None, stripe=False) -> TableStyle:
    cmds = [
        ("BACKGROUND",    (0, 0), (-1, 0),  header_color or TEAL),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.grey),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]
    if stripe:
        cmds.append(("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GREY_BG]))
    return TableStyle(cmds)


# ── Page styles ───────────────────────────────────────────────────────────────

def _ps(name, parent="Normal", **kw) -> ParagraphStyle:
    return ParagraphStyle(name, parent=_SS[parent], **kw)


# ── Public entry point ────────────────────────────────────────────────────────

def generate_pdf_report(
    doc_analysis,
    job_id: str,
    filename: str,
    classification: ClassificationResult,
    document_text: str = "",
) -> str:
    job_dir = os.path.join(settings.REPORT_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    report_path = os.path.join(job_dir, "report.pdf")

    doc = SimpleDocTemplate(
        report_path,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    doc.build(_build_story(doc_analysis, job_id, filename,
                           classification, document_text))
    return report_path


# ── Story builder ─────────────────────────────────────────────────────────────

def _build_story(analysis, job_id, filename, classification, doc_text):
    story = []

    title_s   = _ps("T",  "Heading1", fontSize=22, textColor=TEAL,
                    spaceAfter=6, alignment=TA_CENTER)
    sub_s     = _ps("S",  "Normal",   fontSize=10, textColor=colors.grey,
                    spaceAfter=20, alignment=TA_CENTER)
    h2_s      = _ps("H2", "Heading2", fontSize=14, textColor=TEAL,
                    spaceBefore=18, spaceAfter=8)
    h3_s      = _ps("H3", "Heading3", fontSize=11, textColor=DARK,
                    spaceBefore=10, spaceAfter=4)
    body_s    = _ps("B",  "Normal",   fontSize=10, leading=14,
                    spaceAfter=4, alignment=TA_JUSTIFY, wordWrap="CJK")
    caption_s = _ps("C",  "Normal",   fontSize=8,  textColor=colors.grey,
                    spaceAfter=2, wordWrap="CJK")
    meta_key  = _ps("MK", "Normal",   fontSize=9,  fontName="Helvetica-Bold",
                    wordWrap="CJK")
    meta_val  = _ps("MV", "Normal",   fontSize=9,  wordWrap="CJK")

    # ── Title ────────────────────────────────────────────────────────────────
    story.append(Paragraph("MedExtract Clinical Assistant", title_s))
    story.append(Paragraph(
        "Powered by LangExtract · Structured Clinical Data Extraction", sub_s))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL))
    story.append(Spacer(1, 0.2 * inch))

    # ── Metadata table ────────────────────────────────────────────────────────
    doc_type_label = analysis.document_type.value.replace("_", " ").title()
    meta_rows = [
        [Paragraph("Document",                  meta_key),
         Paragraph(_safe(filename),             meta_val)],
        [Paragraph("Document Type",             meta_key),
         Paragraph(_safe(doc_type_label),       meta_val)],
        [Paragraph("Classification Confidence", meta_key),
         Paragraph(f"{classification.confidence:.0%}", meta_val)],
        [Paragraph("Classification Reasoning",  meta_key),
         Paragraph(_safe(classification.reasoning), meta_val)],
        [Paragraph("Analysed",                  meta_key),
         Paragraph(datetime.now().strftime("%d %b %Y %H:%M"), meta_val)],
        [Paragraph("Session ID",                meta_key),
         Paragraph(_safe(job_id),               meta_val)],
    ]
    meta_table = Table(meta_rows, colWidths=[2 * inch, 4.5 * inch])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, -1), LIGHT_TEAL),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("GRID",          (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.3 * inch))

    # ── Diagnoses ─────────────────────────────────────────────────────────────
    if analysis.diagnoses:
        story.append(Paragraph("Diagnoses", h2_s))
        rows = [[Paragraph("#", CELL_HDR), Paragraph("Diagnosis", CELL_HDR)]]
        for i, d in enumerate(analysis.diagnoses, 1):
            rows.append([_p(str(i)), _p(d)])
        t = Table(rows, colWidths=[0.4 * inch, 6.1 * inch])
        t.setStyle(_table_style(header_color=TEAL))
        story.append(t)
        story.append(Spacer(1, 0.2 * inch))

    # ── Medications ───────────────────────────────────────────────────────────
    if analysis.medication_records:
        story.append(Paragraph("Medications", h2_s))
        hdrs = ["Medication", "Dose", "Route", "Frequency", "Duration", "Indication"]
        rows = [[Paragraph(h, CELL_HDR) for h in hdrs]]
        for m in analysis.medication_records:
            rows.append([
                _p(m.medication_name),
                _p(m.dosage),
                _p(m.route),
                _p(m.frequency),
                _p(m.duration),
                _p(m.indication),
            ])
        t = Table(rows, colWidths=[w * inch for w in [1.3, 0.85, 0.85, 1.05, 0.85, 1.55]])
        t.setStyle(_table_style(header_color=TEAL, stripe=True))
        story.append(t)

        specials = [(m.medication_name, m.special_instruction)
                    for m in analysis.medication_records if m.special_instruction]
        if specials:
            story.append(Spacer(1, 0.05 * inch))
            for name, instr in specials:
                story.append(Paragraph(
                    f"<i>{_safe(name)}:</i> {_safe(instr)}", caption_s))
        story.append(Spacer(1, 0.2 * inch))

    # ── Radiology Findings ────────────────────────────────────────────────────
    if analysis.radiology_findings:
        story.append(Paragraph("Radiology Findings", h2_s))
        hdrs = ["Finding", "Body Part", "Side", "Size", "Impression", "Recommendation"]
        rows = [[Paragraph(h, CELL_HDR) for h in hdrs]]
        for f in analysis.radiology_findings:
            rows.append([
                _p(f.finding),
                _p(f.body_part),
                _p(f.laterality),
                _p(f.measurement),
                _p(f.impression),
                _p(f.recommendation),
            ])
        t = Table(rows, colWidths=[w * inch for w in [1.2, 0.95, 0.65, 0.65, 1.5, 1.5]])
        t.setStyle(_table_style(header_color=TEAL, stripe=True))
        story.append(t)
        story.append(Spacer(1, 0.2 * inch))

    # ── Lab Results ───────────────────────────────────────────────────────────
    if analysis.lab_results:
        story.append(Paragraph("Laboratory Results", h2_s))
        hdrs = ["Test", "Result", "Unit", "Reference Range", "Flag", "Panel"]
        rows = [[Paragraph(h, CELL_HDR) for h in hdrs]]
        for r in analysis.lab_results:
            rows.append([
                _p(r.test_name),
                _p(r.result_value),
                _p(r.unit),
                _p(r.reference_range),
                _flag_cell(r.flag or ""),
                _p(r.panel_name),
            ])
        t = Table(rows, colWidths=[w * inch for w in [1.5, 0.75, 0.7, 1.2, 0.75, 1.1]])
        t.setStyle(_table_style(header_color=TEAL, stripe=True))
        story.append(t)
        story.append(Spacer(1, 0.2 * inch))

    # ── Additional Clinical Information ───────────────────────────────────────
    skip = {
        "medication", "dosage", "route", "frequency", "duration",
        "indication", "special_instruction", "treatment_given",
        "medication_change", "medication_adjustment",
        "finding", "measurement", "impression", "recommendation",
        "lab_test", "result_value", "unit", "reference_range", "flag", "panel_name",
        "diagnosis", "admission_diagnosis", "discharge_diagnosis", "ed_diagnosis",
    }
    grouped: dict = defaultdict(list)
    for e in analysis.extractions:
        if e.extraction_class not in skip:
            grouped[e.extraction_class].append(e)

    if grouped:
        story.append(Paragraph("Additional Clinical Information", h2_s))
        for cls, items in sorted(grouped.items()):
            story.append(Paragraph(cls.replace("_", " ").title(), h3_s))
            for item in items:
                story.append(Paragraph(f"• <b>{_safe(item.extraction_text)}</b>", body_s))
                attrs = {k: v for k, v in (item.attributes or {}).items()
                         if k not in ("medication_group", "finding_group", "test_group",
                                      "pathology_group", "operative_group", "mention_count")
                         and v}
                if attrs:
                    line = " · ".join(
                        f"<i>{k.replace('_', ' ')}:</i> {_safe(v)}"
                        for k, v in list(attrs.items())[:4]
                    )
                    story.append(Paragraph(f"&nbsp;&nbsp;{line}", caption_s))

    # ── Source Verification Appendix ──────────────────────────────────────────
    verifiable = [e for e in analysis.extractions
                  if e.source_span and e.source_span.char_start is not None]
    if verifiable and doc_text:
        story.append(PageBreak())
        story.append(Paragraph("Source Verification Appendix", h2_s))
        story.append(Paragraph(
            "Every row shows an extracted fact linked to its exact character position "
            "in the original document. Use Chars to locate the span in the source.",
            body_s,
        ))
        story.append(Spacer(1, 0.1 * inch))

        hdrs = ["Class", "Extracted Text", "Source Snippet", "Chars", "Confidence"]
        rows = [[Paragraph(h, CELL_HDR) for h in hdrs]]
        for e in verifiable[:80]:
            sp      = e.source_span
            snippet = (doc_text[sp.char_start:sp.char_end] if sp.char_start is not None else "")
            snippet = snippet[:80] + ("…" if len(snippet) > 80 else "")
            pos     = (f"{sp.char_start}–{sp.char_end}"
                       if sp.char_start is not None else "—")
            conf    = ((sp.alignment_status or "").replace("match_", "").title()
                       if sp.alignment_status else "—")
            rows.append([
                _p(e.extraction_class.replace("_", " ")),
                _p(e.extraction_text[:50]),
                _p(snippet),
                _p(pos),
                _p(conf),
            ])

        t = Table(rows, colWidths=[w * inch for w in [1.0, 1.2, 2.5, 0.9, 0.8]])
        t.setStyle(_table_style(header_color=colors.HexColor("#555555"), stripe=True))
        story.append(t)

    return story
