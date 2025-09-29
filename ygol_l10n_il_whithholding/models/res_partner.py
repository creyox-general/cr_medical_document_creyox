#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################
from odoo import fields, models, api, _
from datetime import date
from odoo.exceptions import UserError


class ResPartner(models.Model):
    """Class inherited to add withholding information at partner."""
    _inherit = "res.partner"

    withholding_tax_rate = fields.Float("Withholding Tax Rate(%)",
                                        tracking=True)
    valid_until_date = fields.Date("Valid Until Date", tracking=True)
    l10n_il_withh_tax_id_number = fields.Char(string='WHT ID', tracking=True)
    vendor_occupation = fields.Char(string='Vendor Occupation', tracking=True)
    accounting_authorization = fields.Boolean(
        string="Accounting authorization", tracking=True)
    withholding_tax_reason = fields.Many2one('l10n.il.tax.reason',
                                             string="Withholding Tax Reason",
                                             tracking=True)
    company_status = fields.Selection([
        ('company', 'Company'),
        ('single_person', 'Single Person'),
        ('partnership', 'Partnership'),
        ('ngo', 'NGO'), ('state_company', 'State Company')], tracking=True)
    code = fields.Char(related="country_id.code", string="Code")
    located_ita_file = fields.Char("Located ITA File")
    located_vat_file = fields.Char("Located Vat File")
    withholding_tax_approval = fields.Selection([('yes', 'Yes'), ('no', 'No')])
    valid_start_date = fields.Date("Valid Start Date", tracking=True)
    app_issuing_date = fields.Date("Approval Issuing Date", tracking=True)
    valid_for = fields.Char("Valid For")
    valid_for_deduction_file = fields.Char("Valid for deduction file")
    limited_amount = fields.Float("Limited amount")
    entity_no = fields.Integer("Entity Number")
    supplier_id = fields.Char("1000 System SupplierID")

    @api.constrains('valid_until_date', 'withholding_tax_rate')
    def _constrains_valid_until_date(self):
        """Function call to add user warning when there is no valid date added."""
        for rec in self:
            if rec.company_id and rec.company_id.account_fiscal_country_id.code == 'IL' and rec.withholding_tax_rate != rec.company_id.def_withholding_tax_rate:
                if not rec.valid_until_date:
                    raise UserError(_('Please add withholding Validity date'))
                if rec.valid_until_date and rec.valid_until_date < date.today():
                    raise UserError(
                        _('You can not choose past date for validity date'))

    @api.onchange('company_id')
    def _onchange_company(self):
        """FUnction update withholding tax (%) in partner from the selected company."""
        if self.company_id.account_fiscal_country_id.code == 'IL' and self.company_id.def_withholding_tax_rate:
            self.withholding_tax_rate = self.company_id.def_withholding_tax_rate

    def write(self, vals):
        """It will update child's withholding rate if partner have it."""
        res = super(ResPartner, self).write(vals)
        if 'company_id' in vals:
            company = self.env['res.company'].browse(
                vals.get('company_id')).filtered(
                lambda c: c.account_fiscal_country_id.code == 'IL')
            if company and self.child_ids:
                self.child_ids.write(
                    {'withholding_tax_rate': company.def_withholding_tax_rate})
        return res
