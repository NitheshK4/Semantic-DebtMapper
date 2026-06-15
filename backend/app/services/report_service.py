import logging
from datetime import datetime
from io import BytesIO
from uuid import UUID

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)
from sqlalchemy.orm import Session

from app.models.db_models import ActionCard, DetectorRun, Finding, Project

logger = logging.getLogger(__name__)


class ReportService:
    """Service responsible for generating weekly meaning audit reports in Markdown and PDF.

    Compiles findings, SDS scores, and prioritized action cards into professional,
    distributable report documents.
    """

    @staticmethod
    def get_weekly_report_markdown(db: Session, project_id: UUID) -> str:
        """Generate a weekly audit report in Markdown format.

        Args:
            db: SQLAlchemy database session.
            project_id: Unique identifier of the project.

        Returns:
            A string containing the formatted Markdown report.
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return "# Project Not Found"

        # Fetch latest completed run
        run = (
            db.query(DetectorRun)
            .filter(
                DetectorRun.project_id == project_id, DetectorRun.status == "completed"
            )
            .order_by(DetectorRun.started_at.desc())
            .first()
        )

        if not run:
            return f"""# Weekly Meaning Audit Report - {project.name}
Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

**Status**: No audit run has been successfully completed for this project yet.
Please navigate to the Ingestion and Audit centers to trigger your first run.
"""

        findings = db.query(Finding).filter(Finding.run_id == run.id).all()
        cards = (
            db.query(ActionCard)
            .filter(ActionCard.run_id == run.id)
            .order_by(ActionCard.priority.desc())
            .all()
        )

        sds = float(run.sds_score) if run.sds_score is not None else 0.0

        # Determine band
        if sds <= 20:
            band = "Healthy"
        elif sds <= 40:
            band = "Watch"
        elif sds <= 60:
            band = "Elevated Semantic Debt"
        elif sds <= 80:
            band = "High Risk"
        else:
            band = "Critical"

        markdown = f"""# Weekly Meaning Audit Report: {project.name}
Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Audit Run ID: `{run.id}` | Timestamp: {run.finished_at.strftime("%Y-%m-%d %H:%M:%S") if run.finished_at else "N/A"}

## Executive Summary
The semantic lineage audit for the **{project.name}** pipeline ({project.domain} domain) resulted in a **Semantic Debt Score (SDS) of {sds}/100**, placing the system in the **{band}** band.

- **Total Semantic Mismatches (Findings):** {len(findings)}
- **Open Remediation Actions:** {len([c for c in cards if c.status == 'open'])}

---

## Semantic Debt Breakdown

| Detector | Code | Severity | Target Entity | Issue Summary |
|---|---|---|---|---|
"""
        for f in findings:
            desc = f.payload.get("recommendation", "Review required")
            markdown += f"| {f.detector} | {f.detector} | **{f.severity.upper()}** | `{f.target}` | {desc} |\n"

        if not findings:
            markdown += (
                "| None | N/A | N/A | N/A | No semantic mismatches detected. |\n"
            )

        markdown += """
---

## Prioritized Action Items
The following action items are ranked by estimated semantic debt reduction and business KPI impact:

"""
        for i, card in enumerate(cards, 1):
            status_tag = f"[{card.status.upper()}]"
            markdown += f"### {i}. {card.title} {status_tag}\n"
            markdown += f"- **Action Type**: `{card.action_type}`\n"
            markdown += f"- **Priority Score**: {card.priority}\n"
            markdown += "- **Implementation Steps**:\n"
            for step in card.steps:
                markdown += f"  - [ ] {step}\n"
            markdown += "\n"

        if not cards:
            markdown += "_No active action cards found for this run._\n"

        return markdown

    @staticmethod
    def get_weekly_report_pdf(db: Session, project_id: UUID) -> bytes:
        """Generate a weekly audit report in PDF format.

        Uses ReportLab to generate a styled, corporate PDF containing
        the Executive Summary, SDS Score breakdown, and remediation roadmap.

        Args:
            db: SQLAlchemy database session.
            project_id: Unique identifier of the project.

        Returns:
            Raw bytes of the generated PDF document.
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        proj_name = project.name if project else "Project"
        proj_domain = project.domain if project else "General"

        # Fetch latest completed run
        run = (
            db.query(DetectorRun)
            .filter(
                DetectorRun.project_id == project_id, DetectorRun.status == "completed"
            )
            .order_by(DetectorRun.started_at.desc())
            .first()
        )

        findings = []
        cards = []
        sds = 0.0
        band = "No Audit Data"
        run_id = "N/A"

        if run:
            run_id = str(run.id)
            sds = float(run.sds_score) if run.sds_score is not None else 0.0
            if sds <= 20:
                band = "Healthy"
            elif sds <= 40:
                band = "Watch"
            elif sds <= 60:
                band = "Elevated"
            elif sds <= 80:
                band = "High Risk"
            else:
                band = "Critical"

            findings = db.query(Finding).filter(Finding.run_id == run.id).all()
            cards = (
                db.query(ActionCard)
                .filter(ActionCard.run_id == run.id)
                .order_by(ActionCard.priority.desc())
                .all()
            )

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )
        story = []

        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            textColor=colors.HexColor("#1A365D"),
            spaceAfter=15,
            alignment=0,
        )

        h2_style = ParagraphStyle(
            "Heading2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            textColor=colors.HexColor("#2C5282"),
            spaceBefore=15,
            spaceAfter=8,
        )

        h3_style = ParagraphStyle(
            "Heading3",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=colors.HexColor("#2B6CB0"),
            spaceBefore=8,
            spaceAfter=4,
        )

        body_style = ParagraphStyle(
            "ReportBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            textColor=colors.HexColor("#2D3748"),
            spaceAfter=6,
            leading=13,
        )

        # Header
        story.append(Paragraph(f"Weekly Meaning Audit: {proj_name}", title_style))
        story.append(
            Paragraph(
                f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Project Domain: {proj_domain}",
                body_style,
            )
        )
        story.append(Spacer(1, 10))

        # Executive Summary Box
        summary_text = f"<b>Semantic Debt Score:</b> {sds}/100 ({band})<br/>"
        summary_text += f"<b>Detector Run ID:</b> {run_id}<br/>"
        summary_text += f"<b>Total Findings:</b> {len(findings)} | <b>Open Actions:</b> {len([c for c in cards if c.status == 'open'])}"

        summary_p = Paragraph(
            summary_text,
            ParagraphStyle("SummaryText", parent=body_style, fontSize=11, leading=15),
        )

        summary_table = Table([[summary_p]], colWidths=[500])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EDF2F7")),
                    ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor("#CBD5E0")),
                    ("PADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )

        story.append(summary_table)
        story.append(Spacer(1, 15))

        # Findings Section
        story.append(Paragraph("Semantic Debt Findings", h2_style))

        table_data = [["Detector", "Severity", "Target", "Recommended Action"]]
        for f in findings:
            table_data.append(
                [
                    f.detector,
                    f.severity.upper(),
                    f.target or "Global",
                    f.payload.get("recommendation", "Review required"),
                ]
            )

        if len(findings) == 0:
            table_data.append(
                [
                    "None",
                    "N/A",
                    "N/A",
                    "No semantic debt findings reported in this run.",
                ]
            )

        findings_table = Table(table_data, colWidths=[80, 70, 100, 250])
        findings_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C5282")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(findings_table)
        story.append(Spacer(1, 15))

        # Recommendations Section
        story.append(Paragraph("Remediation Roadmap", h2_style))

        for i, card in enumerate(cards, 1):
            story.append(
                Paragraph(f"<b>{i}. {card.title}</b> ({card.status.upper()})", h3_style)
            )
            story.append(
                Paragraph(
                    f"Action Type: <i>{card.action_type}</i> | Priority Score: {card.priority}",
                    body_style,
                )
            )

            steps_bullets = ""
            for step in card.steps:
                steps_bullets += f"• {step}<br/>"
            story.append(
                Paragraph(
                    steps_bullets,
                    ParagraphStyle(
                        "Bullets", parent=body_style, leftIndent=15, leading=12
                    ),
                )
            )
            story.append(Spacer(1, 8))

        if len(cards) == 0:
            story.append(
                Paragraph("No active remediation cards available.", body_style)
            )

        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data
