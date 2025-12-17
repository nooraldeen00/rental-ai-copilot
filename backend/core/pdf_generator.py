# backend/core/pdf_generator.py
"""
PDF Quote Generator using ReportLab.
Generates a modern, clean 1-page SaaS-style PDF quote.
"""
from io import BytesIO
from typing import Any, Dict, List
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

from backend.core.logging_config import get_logger

logger = get_logger(__name__)


def generate_quote_pdf(
    run_id: int,
    quote: Dict[str, Any],
    customer_tier: str = "C",
    location: str = "",
    start_date: str = "",
    end_date: str = "",
) -> bytes:
    """
    Generate a modern 1-page SaaS-style PDF quote.

    Args:
        run_id: The quote run ID
        quote: Quote data dict with items, fees, totals, notes
        customer_tier: Customer tier (A/B/C)
        location: Customer location/ZIP
        start_date: Rental start date
        end_date: Rental end date

    Returns:
        PDF file as bytes
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.4 * inch,
        bottomMargin=0.4 * inch,
    )

    styles = getSampleStyleSheet()

    # Modern SaaS color palette
    PRIMARY = '#2563eb'      # Blue
    PRIMARY_DARK = '#1e40af'
    SUCCESS = '#10b981'      # Green
    TEXT_DARK = '#1f2937'
    TEXT_MED = '#4b5563'
    TEXT_LIGHT = '#9ca3af'
    BG_LIGHT = '#f9fafb'
    BORDER = '#e5e7eb'

    # Custom styles - compact for 1 page
    styles.add(ParagraphStyle(
        name='Brand',
        fontSize=20,
        textColor=colors.HexColor(PRIMARY),
        fontName='Helvetica-Bold',
        spaceAfter=2,
    ))

    styles.add(ParagraphStyle(
        name='Tagline',
        fontSize=9,
        textColor=colors.HexColor(TEXT_LIGHT),
        spaceAfter=8,
    ))

    styles.add(ParagraphStyle(
        name='SectionTitle',
        fontSize=9,
        textColor=colors.HexColor(TEXT_LIGHT),
        fontName='Helvetica-Bold',
        spaceBefore=10,
        spaceAfter=4,
        textTransform='uppercase',
    ))

    styles.add(ParagraphStyle(
        name='InfoLabel',
        fontSize=8,
        textColor=colors.HexColor(TEXT_LIGHT),
    ))

    styles.add(ParagraphStyle(
        name='InfoValue',
        fontSize=9,
        textColor=colors.HexColor(TEXT_DARK),
        fontName='Helvetica-Bold',
    ))

    styles.add(ParagraphStyle(
        name='Note',
        fontSize=8,
        textColor=colors.HexColor(TEXT_MED),
        leftIndent=8,
        spaceBefore=2,
        spaceAfter=2,
    ))

    styles.add(ParagraphStyle(
        name='Terms',
        fontSize=7,
        textColor=colors.HexColor(TEXT_LIGHT),
        spaceBefore=1,
        spaceAfter=1,
    ))

    styles.add(ParagraphStyle(
        name='TermsItem',
        fontSize=7,
        textColor=colors.HexColor(TEXT_MED),
        spaceBefore=2,
        spaceAfter=2,
        leftIndent=12,
    ))

    styles.add(ParagraphStyle(
        name='TermsNumber',
        fontSize=7,
        textColor=colors.HexColor(PRIMARY),
        fontName='Helvetica-Bold',
    ))

    styles.add(ParagraphStyle(
        name='Footer',
        fontSize=7,
        textColor=colors.HexColor(TEXT_LIGHT),
        alignment=TA_CENTER,
    ))

    # Build content
    story = []
    currency = quote.get("currency", "$")
    generated_date = datetime.now().strftime("%b %d, %Y")
    generated_time = datetime.now().strftime("%I:%M %p")

    # Get rental days from quote
    days = 1
    items = quote.get("items", [])
    if items and items[0].get("days"):
        days = items[0].get("days", 1)

    # Format rental period
    if start_date and end_date:
        rental_period = f"{start_date} - {end_date}"
    elif days > 1:
        rental_period = f"{days} days"
    else:
        rental_period = "1 day"

    # Tier labels
    tier_labels = {"A": "Premium", "B": "Corporate", "C": "Standard"}
    tier_label = tier_labels.get(customer_tier, "Standard")

    # ============ HEADER - Two column layout ============
    header_left = [
        [Paragraph("RentalAI", styles['Brand'])],
        [Paragraph("Enterprise Equipment Rentals", styles['Tagline'])],
    ]

    header_right = [
        [Paragraph("QUOTE", ParagraphStyle(
            'QuoteTitle',
            fontSize=24,
            textColor=colors.HexColor(TEXT_DARK),
            fontName='Helvetica-Bold',
            alignment=TA_RIGHT,
        ))],
        [Paragraph(f"#{run_id}", ParagraphStyle(
            'QuoteNum',
            fontSize=10,
            textColor=colors.HexColor(TEXT_LIGHT),
            alignment=TA_RIGHT,
        ))],
    ]

    header_table = Table(
        [[Table(header_left), Table(header_right)]],
        colWidths=[3.75 * inch, 3.75 * inch]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 12))

    # ============ QUOTE DETAILS - Card style ============
    story.append(Paragraph("QUOTE DETAILS", styles['SectionTitle']))

    # Create info grid - 2 rows, 4 columns
    info_data = [
        [
            Paragraph("Date", styles['InfoLabel']),
            Paragraph("Location", styles['InfoLabel']),
            Paragraph("Rental Period", styles['InfoLabel']),
            Paragraph("Customer Tier", styles['InfoLabel']),
        ],
        [
            Paragraph(generated_date, styles['InfoValue']),
            Paragraph(location if location else "Not specified", styles['InfoValue']),
            Paragraph(rental_period, styles['InfoValue']),
            Paragraph(f"{tier_label} (Tier {customer_tier})", styles['InfoValue']),
        ],
    ]

    info_table = Table(info_data, colWidths=[1.875 * inch] * 4)
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(BG_LIGHT)),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor(BORDER)),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 12))

    # ============ ITEMS TABLE ============
    story.append(Paragraph("EQUIPMENT", styles['SectionTitle']))

    # Table header
    table_data = [["Item", "Qty", "Days", "Daily Rate", "Total"]]

    # Table rows
    for item in items:
        name = item.get("name", "Unknown Item")
        qty = item.get("qty", item.get("quantity", 0))
        item_days = item.get("days", days)
        unit_price = item.get("unitPrice", item.get("unit_price", 0))
        daily_rate = item.get("dailyRate") or (unit_price / item_days if item_days > 0 else unit_price)
        subtotal = item.get("subtotal", item.get("extended", 0))

        table_data.append([
            name,
            str(qty),
            str(item_days),
            f"{currency}{daily_rate:,.2f}",
            f"{currency}{subtotal:,.2f}",
        ])

    items_table = Table(table_data, colWidths=[3.0 * inch, 0.6 * inch, 0.6 * inch, 1.2 * inch, 1.2 * inch])
    items_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(PRIMARY)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (1, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (3, 0), (-1, 0), 'RIGHT'),

        # Body
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor(TEXT_DARK)),
        ('ALIGN', (1, 1), (2, -1), 'CENTER'),
        ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),

        # Alternating rows
        *[('BACKGROUND', (0, i), (-1, i), colors.HexColor(BG_LIGHT))
          for i in range(2, len(table_data), 2)],

        # Borders
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor(BORDER)),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor(PRIMARY_DARK)),

        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 12))

    # ============ SUMMARY - Right aligned totals ============
    subtotal = quote.get("subtotal", 0)
    tax = quote.get("tax", 0)
    fees = quote.get("fees", [])
    total = quote.get("total", 0)

    summary_rows = [["", "Subtotal:", f"{currency}{subtotal:,.2f}"]]

    for fee in fees:
        fee_name = fee.get("name", fee.get("rule", "Fee")).replace("_", " ")
        fee_amount = fee.get("amount", 0)
        summary_rows.append(["", f"{fee_name}:", f"{currency}{fee_amount:,.2f}"])

    summary_rows.append(["", "Tax:", f"{currency}{tax:,.2f}"])
    summary_rows.append(["", "", ""])  # Spacer
    summary_rows.append(["", "TOTAL:", f"{currency}{total:,.2f}"])

    summary_table = Table(summary_rows, colWidths=[4.5 * inch, 1.5 * inch, 1.5 * inch])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -2), 9),
        ('TEXTCOLOR', (1, 0), (1, -2), colors.HexColor(TEXT_MED)),
        ('TEXTCOLOR', (2, 0), (2, -2), colors.HexColor(TEXT_DARK)),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),

        # Total row
        ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (1, -1), (-1, -1), 12),
        ('TEXTCOLOR', (1, -1), (1, -1), colors.HexColor(TEXT_DARK)),
        ('TEXTCOLOR', (2, -1), (2, -1), colors.HexColor(SUCCESS)),
        ('LINEABOVE', (1, -1), (-1, -1), 1, colors.HexColor(PRIMARY)),

        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 10))

    # ============ AI NOTES - Compact ============
    notes = quote.get("notes", [])
    if notes:
        story.append(Paragraph("AI COPILOT NOTES", styles['SectionTitle']))

        # Only show first 2 notes to save space
        for note in notes[:2]:
            clean_note = str(note).strip()
            if clean_note:
                story.append(Paragraph(f"• {clean_note}", styles['Note']))

        story.append(Spacer(1, 8))

    # ============ TERMS & CONDITIONS ============
    story.append(Paragraph("TERMS & CONDITIONS", styles['SectionTitle']))

    # Professional terms list
    terms_list = [
        ("Quote Validity", "This quote is valid for 30 days from the date of issuance."),
        ("Reservation & Deposit", "25% non-refundable deposit required. Balance due upon delivery."),
        ("Cancellation Policy", "7+ days: full deposit refund. Within 7 days: deposit forfeited."),
        ("Delivery & Pickup", "Times are estimates. Clear access required. Additional charges may apply."),
        ("Equipment Condition", "Customer responsible from delivery to pickup. Damage charged at replacement cost."),
        ("Damage Waiver", "Covers accidental damage up to $1,000/item. Excludes intentional damage/theft."),
        ("Setup & Breakdown", "Basic delivery is drop-off only. Setup services available at additional cost."),
        ("Weather Policy", "Customer assumes responsibility for weather-related decisions."),
        ("Extension Policy", "24-hour advance notice required. Late returns: 1.5x daily rate."),
        ("Liability", "Customer agrees to indemnify rental company from claims arising from use."),
    ]

    # Create terms table for better formatting
    terms_data = []
    term_num_style = ParagraphStyle(
        'TermNum',
        fontSize=7,
        textColor=colors.HexColor(PRIMARY),
        fontName='Helvetica-Bold',
    )
    term_text_style = ParagraphStyle(
        'TermText',
        fontSize=7,
        textColor=colors.HexColor(TEXT_MED),
    )

    for i, (title, desc) in enumerate(terms_list, 1):
        terms_data.append([
            Paragraph(f"{i}.", term_num_style),
            Paragraph(f"<b>{title}:</b> {desc}", term_text_style)
        ])

    terms_table = Table(terms_data, colWidths=[0.25 * inch, 7.0 * inch])
    terms_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))

    story.append(terms_table)
    story.append(Spacer(1, 6))

    # Terms footer
    terms_footer = "By proceeding with this quote, customer acknowledges and agrees to the above terms."
    story.append(Paragraph(terms_footer, styles['Terms']))
    story.append(Spacer(1, 8))

    # ============ FOOTER ============
    footer_text = f"RentalAI Copilot • Quote #{run_id} • Generated {generated_date} at {generated_time} • quotes@rentalai.demo"
    story.append(Paragraph(footer_text, styles['Footer']))

    # Build PDF
    doc.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    logger.info(
        f"Generated PDF quote for run {run_id}",
        extra={"extra_fields": {"run_id": run_id, "pdf_size_bytes": len(pdf_bytes)}},
    )

    return pdf_bytes
