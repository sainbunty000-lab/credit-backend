from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import inch
from reportlab.platypus import Image
from reportlab.platypus import BaseDocTemplate
from reportlab.platypus import Frame
from reportlab.platypus import PageTemplate
from reportlab.platypus import KeepTogether
from reportlab.platypus import ListFlowable
from reportlab.platypus import ListItem
from reportlab.platypus import PageBreak
from reportlab.platypus import Flowable
from reportlab.platypus import Spacer
from reportlab.platypus import Paragraph
from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table
from reportlab.platypus import TableStyle

def generate_cam_pdf(data, filename="cam_report.pdf"):
    doc = SimpleDocTemplate(f"downloads/{filename}")
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>Credit Appraisal Memo</b>", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(
        Paragraph(f"Customer Name: {data['customer_name']}", styles["Normal"])
    )

    elements.append(Spacer(1, 0.2 * inch))

    wc = data.get("wc_data", {})
    elements.append(Paragraph("<b>Working Capital</b>", styles["Heading2"]))
    elements.append(
        Paragraph(f"MPBF: {wc.get('output', {}).get('mpbf', 0)}", styles["Normal"])
    )

    elements.append(Spacer(1, 0.2 * inch))

    banking = data.get("banking_data", {})
    elements.append(Paragraph("<b>Banking Analysis</b>", styles["Heading2"]))
    elements.append(
        Paragraph(f"Risk Score: {banking.get('risk_score', 0)}", styles["Normal"])
    )

    doc.build(elements)
    return filename
