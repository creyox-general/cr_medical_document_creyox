import os
from io import BytesIO

from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from datetime import datetime
from odoo.fields import Datetime


def import_local_font():
    """
    Imports hebrew-supporting font locally,
    so the reports can be correctly issued.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(current_dir, '..', 'fonts', 'SecularOne-Regular.ttf')
    pdfmetrics.registerFont(TTFont("SecularOne", font_path))


def get_report_construction_params():
    """
    Get the initial parameters for the report
    """
    # Initialise required report parameters in one phase, so there are no code redundancies
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    # Define styles
    styles = getSampleStyleSheet()

    # Import used font
    import_local_font()

    header_style = ParagraphStyle(
        "HeaderStyle",
        parent=styles["Title"],
        fontName="SecularOne",
        fontSize=18,
        alignment=1,
        justification="center",
        textColor=colors.black,
    )

    section_header_style = ParagraphStyle(
        "SectionHeaderStyle",
        parent=styles["Heading2"],
        fontName="SecularOne",
        fontSize=14,
        alignment=2,  # Right-align for Hebrew support
        justification="center",
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
        justification="center",
    )

    field_placeholder_style = ParagraphStyle(
        "FieldPlaceholderStyle",
        parent=styles["Normal"],
        fontName="SecularOne",
        fontSize=12,
        alignment=2,
        justification="center",
        textColor=colors.gray,
    )

    field_table_header_style = ParagraphStyle(
        "FieldTableHeaderStyle",
        parent=styles["Normal"],
        fontName="SecularOne",
        fontSize=14,
        alignment=1,
        justification="center",
        textColor=colors.black,
    )
    return buffer, doc, header_style, section_header_style, field_label_style, field_placeholder_style, field_table_header_style


def calculate_report_data(form_fields, record):
    """
    Assigns the values to report fields
    """

    (_, _, header_style, section_header_style,
     field_label_style, field_placeholder_style, field_table_header_style) = get_report_construction_params()

    table_header_data = [[
        Paragraph(get_display("ערך השדה"), field_table_header_style),
        Paragraph(get_display("שם השדה"), field_table_header_style)
    ]]

    body_rows = []
    for heb_label, placeholder, rec_key in form_fields:
        if rec_key and rec_key in record:
            value = str(record[rec_key])
        else:
            value = placeholder

        body_rows.append([
            Paragraph(get_display(value), field_placeholder_style),
            Paragraph(get_display(heb_label), field_label_style)
        ])

    return table_header_data + body_rows


def create_table(field_data, doc):
    table = Table(field_data, colWidths=[doc.width * 0.55, doc.width * 0.40])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, -1), "SecularOne"),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black)
    ]))
    return table


def create_r60_pdf(r60_database):
    """
    Creates a PDF using the same layout as create_pdf(),
    but modifies the placeholders with the actual r60_record data.
    Returns PDF as raw bytes.
    @param r60_record: R60 record
    """

    (buffer, doc, header_style, section_header_style,
     field_label_style, field_placeholder_style, field_table_header_style) = get_report_construction_params()

    elements = []

    # Title for R60 report
    title = Paragraph(get_display("דו״ח 856 - רשומה 60"), header_style)
    elements.append(title)
    elements.append(Spacer(1, 20))

    # # Title generation
    # company_name = r60_record['Receiver Name']
    # withholding_rate = r60_record['Withholding Rate (%)']
    # title = Paragraph(get_display(f'דו\"ח 856 - רשומה 60 עבור הלקוח \'{company_name}\' בסך ניכוי {withholding_rate}%'),
    #                   header_style)
    #
    # # Section Headers
    # section_general_info = Paragraph(get_display("פרטי הדו\"ח"), section_header_style)

    # Build a field list of (hebrew_label, default_placeholder_with_length, r60_record_key)
    form_fields = [
        ("מספר תיק ניכויים", "__________", "Company Withholding Tax Number"),
        ("קוד הדיווח", "___", "Report Code"),
        ("שנת מס", "____", "Tax Year"),
        ("זיהוי עובד", "_", "Receiver System ID"),
        ("הסבר על מספר תיק במס הכנסה", "_", "Receiver Business Code"),
        ("מספר תיק / ת.ז. / מספר חברה", "__________", "Receiver Income Tax Number"),
        ("מספר ספק / חשבון במערכת", "______________", "Receiver System ID"),
        ("שם משפחה ושם פרטי / שם החברה", "______________________", "Receiver Name"),
        ("רחוב / שכונה ומספר בית", "_____________________", "Receiver Street Address"),
        ("עיר", "___________", "Receiver City"),
        ("סה\"כ תשלומים ששולמו ברוטו", "___________", "Total Amount Paid"),
        ("סה\"כ מס הכנסה שנוכה", "_________", "Withheld Amount"),
        ("סה\"כ מס ערך מוסף ששולם למס הכנסה", "________", "Taxed Amount"),
        ("יתרות לזכות המקבל לסוף שנת המס", "0", "Additional Fees"),
        ("שיעור ניכוי ברשומה זו (לפי החברה)", "__", "Withholding Rate (%)"),
        ("שם משרד וסמל פקיד השומה", "___________", "TA Branch Name and Code"),
        ("תיאור העסק", "__________________", "Vendor Business Description"),
        ("סוג ניכוי", "__", "Withholding Reason"),
        ("סוג רשומה (חייב להיות 60)", "__", "Record Type"),
    ]

    # For each month, add a section (each on its own page)
    # Reversed collection to match month order
    for idx, (condition_string, r60_record) in enumerate(reversed(r60_database.items()), start=1):
        # Adjust and match month number to verbal description
        section_title = Paragraph(
            get_display(
                f'דו\"ח 856 - רשומה 60 עבור הלקוח \'{r60_record["Receiver Name"]}\' בסך ניכוי רשום {r60_record["Withholding Rate (%)"]}%'),
            section_header_style)
        elements.append(section_title)

        # Build a table from the report dictionary
        field_data = calculate_report_data(form_fields, r60_record)
        table = create_table(field_data, doc)
        elements.append(Spacer(1, 10))
        elements.append(table)
        elements.append(Spacer(1, 30))

        # Add a page break before the next month (as long as it's not the last month)
        if idx < len(r60_database.items()):
            elements.append(PageBreak())

    # Add a timestamp at the end of the file
    timestamp_paragraph = Paragraph(
        get_display(f"חותמת זמן: {Datetime.now()}"),
        field_placeholder_style
    )
    elements.append(timestamp_paragraph)

    # Build and return PDF as BYTES (not as doc, because it's ODOO)
    doc.build(elements)
    pdf_value = buffer.getvalue()
    buffer.close()
    return pdf_value


from datetime import datetime

def create_r70_pdf(r70_record):
    print('\n\n\n---r70_record', r70_record)
    import_local_font()
    (buffer, doc, header_style, section_header_style,
     field_label_style, field_placeholder_style, field_table_header_style) = get_report_construction_params()

    # Title for R70 report
    title = Paragraph(get_display(f"דו״ח 856 - רשומה 70"), header_style)

    section_general_info = Paragraph(get_display("פרטי הדו״ח - R70"), section_header_style)

    # >>> FIX: read dates from _report_period and pass a proper Paragraph STYLE <<<
    period = r70_record.get('_report_period', {}) or {}
    start_date_str = period.get('start_date', '')
    end_date_str = period.get('end_date', '')

    # Parse the date strings to datetime objects and format them as dd-mm-yyyy
    start_date = ""
    end_date = ""
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").strftime("%d-%m-%Y")
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").strftime("%d-%m-%Y")

    # Now pass the formatted dates
    start_date_paragraph = Paragraph(get_display(f"תאריך התחלה:  {start_date}"), field_label_style)
    end_date_paragraph = Paragraph(get_display(f"תאריך סיום:  {end_date}"), field_label_style)
    # <<< END FIX >>>

    table_header_data = [[
        Paragraph(get_display("ערך השדה"), field_table_header_style),
        Paragraph(get_display("שם השדה"), field_table_header_style)
    ]]

    form_fields = [
        ("מספר תיק ניכויים", "_________", "Company Withholding Tax Number"),
        ("קוד דיווח", "___", "Report Code"),
        ("שנת מס", "____", "Tax Year"),
        ("סימון דו\"ח נוסף", " ", "Additional Report Indicator"),
        ("סטטוס משלם", "_", "Company Payer Status Code"),
        ("מספר תיק במס הכנסה", "_________", "Company Income Tax Number"),
        ("תשלומים לתושבי חוץ", "________", "Payments Total Sum (Foreign Resident)"),
        ("מס הכנסה שנוכה לתושבי חוץ", "________", "Total Tax Withheld (Foreign Resident)"),
        ("יתרות נוספות לתושבי חוץ", " ", "Additional Fees (Foreign Resident)"),
        ("טלפון החברה", "__________", "Company Phone Number"),
        ("סה\"כ תשלומים", "__________", "Total Amount Paid"),
        ("סה\"כ ניכוי מס", "__________", "Withheld Amount"),
        ("סה\"כ מס ערך מוסף", "__________", "Taxed Amount"),
        ("מספר המקבלים", "___", "Number of Recipients"),
        ("מספר הרשומות", "___", "Number of Records"),
        ("דואר אלקטרוני", "________________", "Company Email"),
        ("שדה בדיקה", "בדיקה", "Check Field"),
        ("סוג רשומה", "70", "Record Type"),
    ]

    field_data = calculate_report_data(form_fields, r70_record)
    table = create_table(field_data, doc)

    elements = [
        title,
        Spacer(1, 20),
        # dates printed first, as requested
        start_date_paragraph,
        end_date_paragraph,
        Spacer(1, 10),
        section_general_info,
        Spacer(1, 10),
        table,
        Spacer(1, 30),
        Paragraph(get_display(f"חותמת זמן: {Datetime.now()}"), field_placeholder_style),
        Spacer(1, 5),
    ]
    doc.build(elements)
    pdf_value = buffer.getvalue()
    buffer.close()
    return pdf_value


def create_r80_pdf(r80_database):
    """
    Create a single PDF that includes the R80 monthly reports.
    For each month in r80_database, a new page is added.
    """

    import_local_font()
    (buffer, doc, header_style, section_header_style,
     field_label_style, field_placeholder_style, field_table_header_style) = get_report_construction_params()

    elements = []

    # Title for R80 report
    title = Paragraph(get_display("דו״ח 856 - רשומה 80"), header_style)
    elements.append(title)
    elements.append(Spacer(1, 20))

    # For R80 – a monthly report record (each month has one set of fields)
    form_fields = [
        ("מספר תיק ניכויים", "_________", "Company Withholding Tax Number"),
        ("קוד דיווח", "___", "Report Code"),
        ("שנת מס", "____", "Tax Year"),
        ("חודש דיווח", "__", "Tax Month"),
        ("מספר מקבלים", "___", "Number of Recipients"),
        ("תשלומים לא דיבידנד", "__________", "Non-Dividend Payments"),
        ("ניכוי לא דיבידנד", "__________", "Non-Dividend Withheld Tax"),
        ("תשלומי דיבידנד", "__________", "Dividend Payments"),
        ("ניכוי דיבידנד", "__________", "Dividend Withheld Tax"),
        ("סה\"כ מס ששולם", "__________", "Total Tax Paid"),
        ("סוג רשומה", "__", "Record Type"),
    ]

    # Initialise months as strings
    verbal_month_list = ["ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני", "יולי", "אוגוסט", "ספטמבר", "אוקטובר",
                         "נובמבר",
                         "דצמבר"]

    # For each month, add a section (each on its own page)
    for idx, (month, report) in enumerate(r80_database.items(), start=1):
        # Adjust and match month number to verbal description
        section_title = Paragraph(get_display(f"דו״ח לחודש {verbal_month_list[int(month) - 1]}"), section_header_style)
        elements.append(section_title)

        # Build a table from the report dictionary
        field_data = calculate_report_data(form_fields, report)
        table = create_table(field_data, doc)
        elements.append(Spacer(1, 10))
        elements.append(table)
        elements.append(Spacer(1, 30))

        # Add a page break before the next month (as long as it's not the last month)
        if idx < len(r80_database.items()):
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
