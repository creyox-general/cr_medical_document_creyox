def zero_pad(number_str, length):
    """
    For numeric fields: pad on the left with '0' to ensure the exact field length.
    If the input is empty or invalid, we pad with zeros.
    """
    if not number_str:
        number_str = ''
    # Remove any minus signs, decimals, etc. if your data might have them
    # or handle them as needed. This is just a simple approach:
    number_str = str(number_str).replace('.', '').replace('-', '')
    return number_str.rjust(length, '0')  # left-pad with '0'


def space_pad(text, length):
    """
    For alphanumeric fields: pad on the right with spaces to ensure the exact field length.
    If it's longer than `length`, we truncate it.
    """
    if not text:
        text = ''
    text = str(text)
    if len(text) > length:
        text = text[:length]
    return text.rjust(length, ' ')


def build_record_60_line(r60_data):
    """
    Builds one line (record) for the '60' structure, total 216 bytes + CRLF.
    Positions/lengths below follow the PDF guidelines for record type "60" (years 2017–2023).

    IMPORTANT: You must adapt the dictionary keys to match your actual data fields.
    The example keys used below (e.g. `r60_data["Company Withholding Tax Number"]`)
    match the code sample you shared, but rename as needed.
    """

    # 1) Numeric field (9 bytes): 'מספר תיק ניכויים'
    field1 = zero_pad(r60_data.get("Company Withholding Tax Number"), 9)

    # 2) Numeric field (2 bytes): 'קוד הדיווח' (the PDF often says "96" or "??")
    #   '96' Is always the constant report code
    field2 = zero_pad('96', 2)

    # 3) Numeric field (4 bytes): 'שנת המס'
    field3 = zero_pad(r60_data.get("Tax Year"), 4)

    # 4) Numeric field (1 byte): 'זיהוי עובד'
    field4 = zero_pad(r60_data.get("Receiver Special Code"), 1)

    # 5) Numeric field (1 byte): 'הסבר על מספר התיק במס הכנסה'
    field5 = zero_pad(r60_data.get("Receiver Business Code"), 1)

    # 6) Numeric field (9 bytes): 'מס' תיק מס הכנסה / תעודת זהות / ח.פ. ...
    field6 = zero_pad(r60_data.get("Receiver Income Tax Number"), 9)

    # 7) Numeric field (14 bytes): 'מס ספק/חשבון של המשלם'
    field7 = zero_pad(r60_data.get("Receiver System ID"), 14)

    # 8) Alphanumeric (22 bytes): 'שם משפחה ופרטי/שם החברה'
    field8 = space_pad(r60_data.get("Receiver Name"), 22)

    # 9) Alphanumeric (21 bytes): 'רחוב/שכונה ומס בית'
    field9 = space_pad(r60_data.get("Receiver Street Address"), 21)

    # 10) Alphanumeric (13 bytes): 'עיר'
    field10 = space_pad(r60_data.get("Receiver City"), 13)

    # 11) Numeric (11 bytes): 'סה"כ תשלומים ששולמו ברוטו (כולל מע"מ)'
    total_paid_str = "{:.0f}".format(r60_data.get("Total Amount Paid", 0.0))
    field11 = zero_pad(total_paid_str, 11)

    # 12) Numeric (9 bytes): 'סה"כ מס הכנסה שנוכה'
    total_withheld_str = "{:.0f}".format(r60_data.get("Withheld Amount", 0.0))
    field12 = zero_pad(total_withheld_str, 9)

    # 13) Numeric (8 bytes): 'סה"כ מע"מ'
    total_tax_str = "{:.0f}".format(r60_data.get("Taxed Amount", 0.0))
    field13 = zero_pad(total_tax_str, 8)

    # 14) Numeric (8 bytes): 'יתרות לזכות המקבל לסוף השנה'
    #   If your code tracks leftover balances, otherwise zero:
    field14 = zero_pad('0', 8)

    # 15) Numeric (2 bytes): 'שיעור הניכוי'
    #   e.g. "10" if 10%
    wth_rate = r60_data.get("Withholding Rate (%)", '0')
    wth_rate_str = int(float(wth_rate.replace('%', '').strip()))
    field15 = zero_pad(wth_rate_str, 2)

    # 16) Alphanumeric (12 bytes): 'שם משרד/פקיד השומה נותן האישור'
    #   The doc’s table calls for length 12 from col 135-146.
    #   Possibly for storing something like “01Tveria”?
    field16 = space_pad(r60_data.get("TA Branch Name and Code"), 12)

    # 17) Alphanumeric (14 bytes): 'עיסוק המקבל'
    field17 = space_pad(r60_data.get("Vendor Business Description"), 14)

    # 18) Alphanumeric (52 bytes): 'FILLER ריק'
    field18 = space_pad('', 52)

    # 19) Numeric (2 bytes): 'סוג הניכוי'
    withholding_reason = r60_data.get("Withholding Reason", '01')  # or however you store it
    field19 = zero_pad(withholding_reason, 2)

    # 20) Numeric (2 bytes): 'סוג רשומה' => always "60" for record 60
    field20 = zero_pad('60', 2)

    # Concatenate everything (216 chars total)
    record = (
            field1 + field2 + field3 + field4 + field5 +
            field6 + field7 + field8 + field9 + field10 +
            field11 + field12 + field13 + field14 + field15 +
            field16 + field17 + field18 + field19 + field20
    )

    print(" ".join(str(len(field)) for field in [field1, field2, field3, field4, field5,
                                                 field6, field7, field8, field9, field10,
                                                 field11, field12, field13, field14, field15,
                                                 field16, field17, field18, field19, field20]))

    # Sanity-check length
    if len(record) != 216:
        raise ValueError(f"Record 60 line must be 216 characters; got {len(record)}.")

    # Add CR+LF
    return record + "\r\n"


def build_record_70_line(r70_data):
    """
    Builds one line for '70' record (the "Rishumat Sikum" for the payer).
    This is similar to build_record_60_line but with the 70 layout from the PDF.
    """
    # The doc says total 216 data bytes, plus CRLF => 218 total with CR+LF.
    # Positions (1-9), (10-11), (12-15), etc. vary for record 70.

    # 1) Numeric (9 bytes): מספר תיק ניכויים
    field1 = zero_pad(r70_data.get("Company Withholding Tax Number"), 9)

    # 2) Numeric (2 bytes): קוד סוג הדיווח (often "96" or "??")
    field2 = zero_pad('96', 2)

    # 3) Numeric (4 bytes): שנת מס
    field3 = zero_pad(r70_data.get("Tax Year"), 4)

    # 4) Alphanumeric (3 bytes): filler ריק
    field4 = space_pad('', 3)

    # 5) Alphanumeric (1 byte): filler ריק
    field5 = space_pad('', 1)

    # 6) Numeric (1 byte): 'האם קיים דו"ח משלים?' (0=לא, 2=כן)
    field6 = zero_pad(r70_data.get("Additional Report Indicator"), 1)

    # 7) Numeric (1 byte): 'מעמד המשלם' (1=חברה, 2=יחיד, etc.)
    field7 = zero_pad(r70_data.get("Company Payer Status Code"), 1)

    # 8) Numeric (9 bytes): 'מס' תיק מס הכנסה של המשלם
    field8 = zero_pad(r70_data.get("Company Income Tax Number", ''), 9)

    # 9) Numeric (12 bytes): "סה'כ תשלומים לתושבי חוץ באמצעות בנק (08) ..."
    total_fr_str = "{:.0f}".format(r70_data.get("Payments Total Sum (Foreign Resident)", 0.0))
    field9 = zero_pad(total_fr_str, 12)

    # 10) Numeric (10 bytes): "מס הכנסה שנוכה לתושבי חוץ"
    tax_fr_str = "{:.0f}".format(r70_data.get("Total Tax Withheld (Foreign Resident)", 0.0))
    field10 = zero_pad(tax_fr_str, 10)

    # 11) Numeric (11 bytes): "סה'כ יתרות לזכות המקבלים לסוף שנת המס"
    #    The PDF shows different fields for record 70. Let’s pick one:
    #    Possibly 11 is another 9 or 10 bytes. We’ll just do 10 for demonstration:
    field11 = zero_pad('0', 11)

    # 12) Numeric (10 bytes): "מספר הטלפון של החברה שהכינה את הדו"ח"
    field12 = zero_pad(r70_data.get("Company Phone Number"), 10)

    # 13) Alphanumeric (28 bytes): filler ריק
    field13 = space_pad('', 28)

    # 14) Numeric (12 bytes): 'סה"כ תשלומים ברוטו'
    total_paid_str = "{:.0f}".format(r70_data.get("Total Amount Paid", 0.0))
    field14 = zero_pad(total_paid_str, 12)

    # 15) Numeric (10 bytes): 'סה"כ ניכוי מס הכנסה'
    withheld_str = "{:.0f}".format(r70_data.get("Withheld Amount", 0.0))
    field15 = zero_pad(withheld_str, 10)

    # 16) Numeric (9 bytes): 'סה"כ מע"מ'
    total_tax_str = "{:.0f}".format(r70_data.get("Taxed Amount", 0.0))
    field16 = zero_pad(total_tax_str, 9)

    # 17) Alphanumeric (9 bytes): filler ריק
    field17 = space_pad('', 9)

    # 18) Numeric (6 bytes): 'מספר המקבלים'
    recipients_str = "{:d}".format(r70_data.get("Number of Recipients", 0))
    field18 = zero_pad(recipients_str, 6)

    # 19) Numeric (6 bytes): 'סה"כ רשומות'
    records_str = "{:d}".format(r70_data.get("Number of Records", 0))
    field19 = zero_pad(records_str, 6)

    # 20) Alphanumeric (50 bytes): 'כתובת דוא"ל'
    field20 = space_pad(str(r70_data.get("Company Email")).upper(), 50)

    # 21) Alphanumeric (5 bytes): 'בדיקה'
    field21 = space_pad("הקידב", 5)

    # 22) Alphanumeric (6 bytes): filler ריק
    field22 = space_pad('', 6)

    # 23) Numeric (2 bytes): 'סוג רשומה' => "70"
    field23 = zero_pad('70', 2)

    # Concatenate (make sure total is 216):
    record = (
            field1 + field2 + field3 + field4 + field5 +
            field6 + field7 + field8 + field9 + field10 +
            field11 + field12 + field13 + field14 + field15 +
            field16 + field17 + field18 + field19 + field20 +
            field21 + field22 + field23
    )
    if len(record) != 216:
        raise ValueError(f"Record 70 line must be 216 characters; got {len(record)}.")
    return record + "\r\n"


def build_record_80_line(r80_data):
    """
    Builds one line for '80' record (the monthly summary).
    Per the PDF, it’s also 216 data bytes plus CRLF.
    Adjust indexes & lengths to your real needs.
    """
    # 1) Numeric (9 bytes): מספר תיק ניכויים
    field1 = zero_pad(r80_data.get("Company Withholding Tax Number"), 9)

    # 2) Numeric (2 bytes): קוד סוג דיווח ('96' or whatever)
    field2 = zero_pad('96', 2)

    # 3) Numeric (4 bytes): שנת מס
    field3 = zero_pad(r80_data.get("Tax Year"), 4)

    # 4) Numeric (2 bytes): 'חודש משכורת'
    month_str = "{:02d}".format(int(r80_data.get("Tax Month", '0')))
    field4 = zero_pad(month_str, 2)

    # 5) Numeric (6 bytes): 'מספר מנוכים'
    recipients_str = "{:d}".format(r80_data.get("Number of Recipients", 0))
    field5 = zero_pad(recipients_str, 6)

    # 6) Numeric (12 bytes): 'תשלומים ששולמו (לא כולל דיבידנד?)'
    non_div_paid = "{:.0f}".format(r80_data.get("Non-Dividend Payments", 0.0))
    field6 = zero_pad(non_div_paid, 12)

    # 7) Numeric (12 bytes): 'ניכוי מס הכנסה (לא כולל דיבידנד?)'
    non_div_withheld = "{:.0f}".format(r80_data.get("Non-Dividend Withheld Tax", 0.0))
    field7 = zero_pad(non_div_withheld, 12)

    # 8) Numeric (12 bytes): 'סה"כ מע"מ או סכום מס?'
    total_tax_str = "{:.0f}".format(r80_data.get("Total Tax Paid", 0.0))
    field8 = zero_pad(total_tax_str, 12)

    # 9) Numeric (12 bytes): 'תשלומים בגין דיבידנד'
    div_paid_str = "{:.0f}".format(r80_data.get("Dividend Payments", 0.0))
    field9 = zero_pad(div_paid_str, 12)

    # 10) Numeric (12 bytes): 'ניכוי מס בגין דיבידנד'
    div_withheld_str = "{:.0f}".format(r80_data.get("Dividend Withheld Tax", 0.0))
    field10 = zero_pad(div_withheld_str, 12)

    # 11) Alphanumeric (131 bytes): filler ריק
    field11 = space_pad('', 131)

    # 12) Numeric (2 bytes): 'סוג רשומה' => "80"
    field12 = zero_pad('80', 2)

    record = (
            field1 + field2 + field3 + field4 + field5 +
            field6 + field7 + field8 + field9 + field10 +
            field11 + field12
    )
    if len(record) != 216:
        raise ValueError(f"Record 80 line must be 216 characters; got {len(record)}.")
    if month_str == "12":
        return record
    return record + "\r\n"


def export_856_to_txt(r60_dicts, r70_dict, r80_dicts):
    """
    Main function that:
    1) Builds lines for each R60 record
    2) Builds a single R70 record line
    3) Builds lines for each R80 record
    4) Writes them all (in that order) to a .txt file

    :param r60_dicts: List of dictionaries (each for a single "60" record)
    :param r70_dict:  One dictionary for the "70" record
    :param r80_dicts: List of dictionaries (each for a single "80" record)
    :param output_path: Path to write the .txt file
    """
    lines = []

    # Build all 60-record lines
    for r60 in r60_dicts.values():
        print(r60)
        line = build_record_60_line(r60)
        lines.append(line)

    # Build the single 70-record line
    line_70 = build_record_70_line(r70_dict)
    lines.append(line_70)

    # Build all 80-record lines
    for r80 in r80_dicts.values():
        print(r80)
        line = build_record_80_line(r80)
        lines.append(line)

    # Join and return the file's bytestream
    file_content = "".join(lines)
    file_content.encode("windows-1255", errors="replace")
    return file_content
