from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_report(
    candidate_name: str,
    match_score: float,
    matched_skills: list[str],
    missing_skills: list[str],
    suggestions: list[str],
    recommendation: str,
) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("AI Job Match Report", styles["Title"]))
    story.append(Spacer(1, 12))

    summary_data = [
        ["Candidate", candidate_name],
        ["Match Score", f"{match_score:.2f}%"],
        ["Final Recommendation", recommendation],
    ]
    table = Table(summary_data, colWidths=[160, 340])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F5F7FA")),
        ("GRID", (0, 0), (-1, -1), 1, colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(table)
    story.append(Spacer(1, 16))

    story.append(Paragraph(f"<b>Matched Skills:</b> {', '.join(matched_skills) or 'None'}", styles["BodyText"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"<b>Missing Skills:</b> {', '.join(missing_skills) or 'None'}", styles["BodyText"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Improvement Suggestions:</b>", styles["BodyText"]))
    for suggestion in suggestions:
        story.append(Paragraph(f"• {suggestion}", styles["BodyText"]))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
