import os
import tempfile

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors


# =========================================
# SAFE VALUE
# =========================================

def safe(value):
    if value is None:
        return "-"
    return str(value)


# =========================================
# TABLE BUILDER
# =========================================

def create_table(data):

    table = Table(data, hAlign="LEFT")

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    return table


# =========================================
# CAM PDF GENERATOR
# Returns the full path to the generated PDF.
# Uses /tmp so it works on Cloud Run and other
# read-only container filesystems.
# =========================================

def generate_cam_pdf(data, filename="cam_report.pdf"):

    styles = getSampleStyleSheet()

    # Always write to /tmp for compatibility with Cloud Run
    output_path = os.path.join(tempfile.gettempdir(), filename)

    doc = SimpleDocTemplate(
        output_path,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    elements = [
        Paragraph("<b>CREDIT APPRAISAL MEMO</b>", styles["Title"]),
        Spacer(1, 0.3 * inch),
        Paragraph("<b>Customer Details</b>", styles["Heading2"]),
    ]

    # =========================================
    # CUSTOMER DETAILS
    # =========================================

    customer_table = [
        ["Field", "Value"],
        ["Customer Name", safe(data.get("customer_name"))],
        ["Loan Amount", safe(data.get("loan_amount"))],
        ["Status", safe(data.get("status"))],
    ]

    elements.append(create_table(customer_table))

    elements.append(Spacer(1, 0.25 * inch))

    # =========================================
    # WORKING CAPITAL SECTION
    # =========================================

    wc = data.get("wc_data")

    if wc:

        ratios = wc.get("ratios", {})
        mpbf = wc.get("mpbf_analysis", {})

        elements.append(
            Paragraph("<b>Working Capital Analysis</b>", styles["Heading2"])
        )

        wc_table = [
            ["Metric", "Value"],
            ["Current Ratio", safe(ratios.get("current_ratio"))],
            ["Quick Ratio", safe(ratios.get("quick_ratio"))],
            ["Net Working Capital", safe(ratios.get("nwc"))],
            ["MPBF", safe(mpbf.get("mpbf"))],
            ["Recommended Limit", safe(mpbf.get("recommended_limit"))],
        ]

        elements.append(create_table(wc_table))

        elements.append(Spacer(1, 0.25 * inch))

    # =========================================
    # BANKING ANALYSIS
    # =========================================

    banking = data.get("banking_data")

    if banking:

        summary = banking.get("statement_summary", {})
        risk = banking.get("risk_summary", {})

        elements.append(
            Paragraph("<b>Banking Behaviour</b>", styles["Heading2"])
        )

        banking_table = [
            ["Metric", "Value"],
            ["Total Credit", safe(summary.get("total_credit"))],
            ["Total Debit", safe(summary.get("total_debit"))],
            ["Net Surplus", safe(summary.get("net_surplus"))],
            ["Risk Score", safe(risk.get("hygiene_score"))],
            ["Risk Grade", safe(risk.get("risk_grade"))],
        ]

        elements.append(create_table(banking_table))

        elements.append(Spacer(1, 0.25 * inch))

    # =========================================
    # AGRICULTURE ANALYSIS
    # =========================================

    agri = data.get("agri_data")

    if agri:

        income = agri.get("income_analysis", {})
        emi = agri.get("emi_analysis", {})
        loan = agri.get("loan_eligibility", {})

        elements.append(
            Paragraph("<b>Agriculture Eligibility</b>", styles["Heading2"])
        )

        agri_table = [
            ["Metric", "Value"],
            ["Total Adjusted Income", safe(income.get("total_adjusted_income"))],
            ["Disposable Income", safe(emi.get("disposable_income"))],
            ["Eligible Loan", safe(loan.get("final_eligible_loan"))],
        ]

        elements.append(create_table(agri_table))

        elements.append(Spacer(1, 0.25 * inch))

    # =========================================
    # CREDIT RECOMMENDATION
    # =========================================

    elements.append(
        Paragraph("<b>Credit Recommendation</b>", styles["Heading2"])
    )

    decision_table = [
        ["Field", "Value"],
        ["Credit Grade", safe(data.get("credit_grade"))],
        ["Recommended Limit", safe(data.get("recommended_limit"))],
        ["Remarks", safe(data.get("remarks"))],
    ]

    elements.append(create_table(decision_table))

    # =========================================
    # BUILD PDF
    # =========================================

    doc.build(elements)

    return output_path

