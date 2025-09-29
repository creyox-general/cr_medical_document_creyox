import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from bidi.algorithm import get_display
from io import BytesIO
from odoo.fields import Datetime


# This is a PDF creator for the 857 report
def create_857_pdf(report_database):
    """
    Creates a multipage PDF for the 857 report, where each element in
    'report_database' is one record for a given vendor, and presented as one page.
    """

    # Prepare fonts, doc, and styles parameters, same as the 856 handler
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    # Register local font for Hebrew support
    current_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(current_dir, '..', 'fonts', 'SecularOne-Regular.ttf')
    pdfmetrics.registerFont(TTFont("SecularOne", font_path))

    styles = getSampleStyleSheet()

    header_style = ParagraphStyle(
        "HeaderStyle",
        parent=styles["Title"],
        fontName="SecularOne",
        fontSize=18,
        alignment=1,  # Center
        textColor=colors.black,
    )

    section_header_style = ParagraphStyle(
        "SectionHeaderStyle",
        parent=styles["Heading2"],
        fontName="SecularOne",
        fontSize=14,
        alignment=2,  # Right-align for Hebrew
        textColor=colors.darkblue,
        spaceBefore=15,
        spaceAfter=10,
        underline=True,
    )

    field_label_style = ParagraphStyle(
        "FieldLabelStyle",
        parent=styles["Normal"],
        fontName="SecularOne",
        fontSize=12,
        alignment=2,
    )

    field_placeholder_style = ParagraphStyle(
        "FieldPlaceholderStyle",
        parent=styles["Normal"],
        fontName="SecularOne",
        fontSize=12,
        alignment=2,
        textColor=colors.gray,
    )

    table_header_style = ParagraphStyle(
        "TableHeaderStyle",
        parent=styles["Normal"],
        fontName="SecularOne",
        fontSize=14,
        alignment=1,
        textColor=colors.black,
    )

    # Initialise the document builder
    elements = []

    # Assign a document Title
    title = Paragraph(get_display("דו״ח 857 - פירוט תשלומים וניכויים"), header_style)
    elements.append(title)
    elements.append(Spacer(1, 20))

    # Initialise months as strings
    verbal_month_list = ["ינו\'", "פבר\'", "מרץ", "אפר\'", "מאי", "יונ\'", "יול\'", "אוג\'", "ספט\'", "אוק\'", "נוב\'", "דצמ\'"]

    # Loop over each record in the 857 report database, since there is more than 1
    for idx, record in enumerate(report_database, start=1):

        # 857 Report page header for vendor
        report_header = Paragraph(
            get_display(f" #{idx} - {record.get('vendor_name', '')}"),
            section_header_style
        )
        elements.append(report_header)
        elements.append(Spacer(1, 20))

        # We need to handle the month activity dicionary in a different way,
        # since it is a standalone unique field. So we'll dedicate a section for that.

        # A heading for the months section
        months_header = Paragraph(get_display("חודשים פעילים במהלך השנה"), section_header_style)
        elements.append(months_header)
        elements.append(Spacer(1, 5))

        months_row_names = []
        months_row_indicators = []

        months_dict = record.get("report_months", {})

        for month_num in reversed(range(1, 13)):
            key_str = str(month_num)
            indicator = months_dict.get(key_str, " ")  # 'X' for True, else empty
            # Top: month name
            months_row_names.append(
                Paragraph(get_display(verbal_month_list[month_num - 1]), field_label_style)
            )
            # Bottom: indicator
            months_row_indicators.append(
                Paragraph(get_display(indicator), field_label_style)
            )

        # Initialise list for horizontal display
        months_data = [
            months_row_names,
            months_row_indicators
        ]

        # Create the table with 12 columns:
        months_table = Table(
            months_data,
            colWidths=[doc.width / 12.0] * 12  # 12 equal columns
        )

        months_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, -1), "SecularOne"),
            ("FONTSIZE", (0, 0), (-1, -1), 12),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),  # top row background
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))

        elements.append(months_table)
        elements.append(Spacer(1, 30))

        # A heading for the activity/report section
        vendor_header = Paragraph(
            get_display("פרטי פעילות"),
            section_header_style
        )
        elements.append(vendor_header)
        elements.append(Spacer(1, 10))

        main_fields = [
            # (Hebrew label, default placeholder, key in record)
            ("שם חברה", "___", "company_name"),
            ("כתובת חברה", "___", "company_address"),
            ("מספר תיק ניכויים של החברה", "___", "company_withhold_tax_number"),
            ("שם ספק/מוכר", "___", "vendor_name"),
            ("כתובת ספק/מוכר", "___", "vendor_address"),
            ("תיק ניכויים/תיק במס הכנסה של ספק", "___", "vendor_income_tax_number"),
            ("שנת דיווח", "____", "report_year"),
            ("סך תשלומים (ברוטו)", "0.00", "report_total_amount"),
            ("סך תשלומים נוספים", "0.00", "report_additional_amount"),
            ("סך מס ערך מוסף", "0.00", "report_vat_amount"),
        ]

        # Convert field list to table data
        table_data = [[
            Paragraph(get_display("ערך השדה"), table_header_style),
            Paragraph(get_display("שם השדה"), table_header_style),
        ]]

        for heb_label, placeholder, key in main_fields:
            value_str = placeholder
            if key in record:
                value_str = str(record[key])
            # Add the row
            table_data.append([
                Paragraph(get_display(value_str), field_placeholder_style),
                Paragraph(get_display(heb_label), field_label_style),
            ])

        # Create the main table
        main_table = Table(
            table_data,
            colWidths=[doc.width * 0.55, doc.width * 0.40]
        )
        main_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
            ("FONTNAME", (0, 0), (-1, -1), "SecularOne"),
            ("FONTSIZE", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black)
        ]))

        elements.append(main_table)
        elements.append(Spacer(1, 20))

        # Add a page break before the next record (if there are multiple reports)
        if idx < len(report_database):
            elements.append(PageBreak())

    # Add a timestamp at the end of the file
    timestamp_paragraph = Paragraph(
        get_display(f"חותמת זמן: {Datetime.now()}"),
        field_placeholder_style
    )
    elements.append(timestamp_paragraph)

    # Build PDF and return byte-file
    doc.build(elements)
    pdf_value = buffer.getvalue()
    buffer.close()
    return pdf_value
