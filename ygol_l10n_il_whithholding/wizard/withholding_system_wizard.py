#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################

import base64
from odoo import models, fields, _
import logging
import re
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)
from datetime import datetime

main_counter = 0


class Israel1000System(models.TransientModel):
    """Class Added to Extract TXT report for withholding."""
    _name = 'withholding.supplier.system'
    _description = "1000 System"

    # Field for export data
    state = fields.Selection(
        [('choose', 'Choose'), ('get', 'Get'), ('done', 'Done')],
        default='choose')
    extraction_data = fields.Binary(
        '1000 System Report', readonly=True, attachment=False)
    extraction_filename = fields.Char()
    # fields for import data
    upload_ita_file = fields.Binary("Upload File", attachment=True)

    def count_length(self, records, length):
        """Find and passed length of each record."""
        value = ''
        if len(records) < length:
            value = records.rjust(length, '0')
        elif len(records) > length:
            value = records[:length]
        else:
            value = records
        return value

    def opening_record(self):
        vals = {
            'type_of_record': 'A',
            'supplier_tax_id': str(self.count_length(
                str(self.env.company.l10n_il_withh_tax_id_number or ''), 9))
        }
        return vals

    def main_record(self):
        supplier_obj = self.env['res.partner'].search(
            [
                ('code', '=', 'IL'),
                ('invoice_ids', 'in', self.env['account.move'].search(
                    [
                        ('move_type', 'in', ['in_invoice', 'in_refund'])
                    ]
                ).ids),
            ]
        )
        # Ticket HT01460 Added domain for draft bill
        main_data_list = []
        global main_counter
        for data in supplier_obj:
            if not data.supplier_id:
                data.update({
                    'supplier_id': str(self.count_length(
                        str(data.id), 15))
                })
            main_counter += 1
            vals = {
                'type_of_record': 'B',
                'supplier_id': str(self.count_length(
                    str(data.id), 15)),
                'supplier_tax_id': str(self.count_length(
                    str(data.l10n_il_income_tax_id_number or ''), 9)),
                'supplier_vat_id': str(self.count_length(
                    str(data.vat or ''), 9))
            }
            main_data_list.append(vals)
        return main_data_list

    def closing_record(self):
        vals = {
            'type_of_record': 'Z',
            'representing_number': str(self.count_length(
                str(self.env.company.l10n_il_withh_tax_id_number or ''), 9)),
            'total_no_record': str(self.count_length(
                str(main_counter), 4))
            # total no of record updates under function
        }
        return vals

    def print_1000_txt_report(self):
        supplier_list = []
        opening_data = self.opening_record()
        main_data = self.main_record()
        closing_data = self.closing_record()
        if main_data:
            supplier_list.append(main_data)
        archive = open('Supplier.TXT', 'w')
        # Append opening record
        archive.write(opening_data.get('type_of_record') + opening_data.get(
            'supplier_tax_id') + "\n")
        for data in main_data:
            archive.write(
                str(data["type_of_record"]) +
                str(data["supplier_id"]) +
                str(data["supplier_tax_id"]) +
                str(data["supplier_vat_id"]) + "\n")
        # Append closing record
        archive.write(closing_data.get('type_of_record') + closing_data.get(
            'representing_number') + closing_data.get(
            'total_no_record') + "\n")
        archive.close()
        zip_data = open('Supplier.TXT', 'r')
        zip_data = base64.b64encode(zip_data.read().encode('utf-8'))
        attachment_obj = self.env['ir.attachment'].create({
            'name': '1000_system' + '.txt',
            'datas': zip_data,
        })
        self.write({
            'state': 'get',
            'extraction_data': attachment_obj.datas,
            'extraction_filename': attachment_obj.name,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'withholding.supplier.system',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    def upload_1000_txt_report(self):
        import os
        import codecs
        directory = "PDF"
        # get dir
        parent_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(parent_dir, directory)
        if not os.path.exists(path):
            os.mkdir(path)
        # Added path
        first_text_file = path + '/first_text_file.txt'
        if str(self.extraction_filename.split(".")[1]) != 'txt':
            raise ValidationError(
                "Please upload data in .txt file extension only..!!")
        # Open and write data
        with open(first_text_file, 'wb') as fout1:
            fout1.write(base64.b64decode(self.upload_ita_file))

        file_data = codecs.open(first_text_file, "r", "cp1255")
        is_imported = False
        line_record = 0
        for line in file_data:
            data = repr(line)
            if 'B' in data:
                supplier_id = data[2:17]
                # Get supplier data
                supplier_data = self.env['res.partner'].search(
                    [('supplier_id', '=', supplier_id)])
                for supp in supplier_data:
                    line_record += 1
                    len_characters = {
                        'l10n_il_income_tax_id_number': 9,
                        'vat': 9,
                        'located_ita_file': 9,
                        'located_vat_file': 9,
                        'name': 22,
                        'withholding_tax_approval': 1,
                        'withholding_tax_rate': 10,
                        'valid_start_date': 8,
                        'valid_until_date': 8,
                        'app_issuing_date': 8,
                        'valid_for': 3,
                        'valid_for_deduction_file': 9,
                        'limited_amount': 10,
                        'entity_no': 9
                    }
                    starting_index = 17
                    for char in len_characters:
                        # Mapped len char and data from the file.
                        characters = len_characters[char]
                        if not char == 'name':
                            len_characters[char] = data[
                                                   starting_index:starting_index + characters]
                        else:
                            pass
                        starting_index += characters
                    del len_characters['name']
                    # added rate condition
                    if len_characters.get('valid_start_date') != '00000000':
                        valid_start_date = datetime.strptime(
                            len_characters.get('valid_start_date'), "%Y%m%d")
                    if len_characters.get('valid_until_date') != '00000000':
                        valid_until_date = datetime.strptime(
                            len_characters.get('valid_until_date'), "%Y%m%d")
                    if len_characters.get('app_issuing_date') != '00000000':
                        app_issuing_date = datetime.strptime(
                            len_characters.get('app_issuing_date'), "%Y%m%d")
                    line = len_characters.get('withholding_tax_rate')
                    withholding_regx_99 = re.match(r'99.*99', line)
                    withholding_regx_00 = re.match(r'00.*00', line)
                    withholding_regx_9999 = re.match(r'99.*9999', line)
                    withholding_regx_9900 = re.match(r'99.*00', line)

                    withholding_tax_rate = 0
                    if withholding_regx_99:
                        if withholding_regx_9999:
                            groups = list(map(int, [line[i:i + 2] for i in
                                                    range(0, len(line[2:6]),
                                                          2)]))
                            withholding_tax_rate = 0 if max(
                                groups) == 99 and all(i == 00 for i in list(
                                filter(lambda x: x != 99, groups))) else \
                            sorted(groups)[-2]
                        else:
                            groups = list(map(int, [line[i:i + 2] for i in
                                                    range(0, len(line[2:8]),
                                                          2)]))
                            withholding_tax_rate = 0 if max(
                                groups) == 99 else max(groups)
                    elif line == '0000000000':
                        withholding_tax_rate = 30
                    elif withholding_regx_00:
                        groups = list(map(int, [line[i:i + 2] for i in
                                                range(0, len(line[2:8]), 2)]))
                        withholding_tax_rate = max(groups)
                    elif withholding_regx_9900:
                        groups = list(map(int, [line[i:i + 2] for i in
                                                range(0, len(line[2:8]), 2)]))
                        withholding_tax_rate = 0 if max(groups) == 99 and all(
                            i == 00 for i in
                            list(filter(lambda x: x != 99, groups))) else \
                        sorted(list(filter(lambda x: x != 99, groups)))[-2]
                    # Updated supplier data
                    len_characters.update({
                        'withholding_tax_approval': 'yes' if len_characters.get(
                            'withholding_tax_approval') == '1' else 'no',
                        'valid_start_date': valid_start_date,
                        'valid_until_date': valid_until_date,
                        'app_issuing_date': app_issuing_date,
                        'withholding_tax_rate': withholding_tax_rate
                    })
                    supp.write(len_characters)
                    self.write({'state': 'done'})
                # raised bad data warning
                if not supplier_data and self.state != 'done':
                    raise ValidationError("Import Process Error..!!")
                if supplier_data and self.state == 'done':
                    is_imported = True
                    for s in supplier_data: s.accounting_authorization = True

        # Commited all data to supplier
        self._cr.commit()
        # Added successfully updated message.
        if is_imported:
            raise UserError(
                "%s Suppliers Updated Successfully..!!" % line_record)
        os.remove(first_text_file)
