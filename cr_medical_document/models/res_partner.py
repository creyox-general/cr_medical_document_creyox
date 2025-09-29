# -*- coding: utf-8 -*-
# Part of Creyox Technologies

from odoo import fields, models, api, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    rating = fields.Selection([("0", "0"), ("1", "1"), ("2", "2"), ("3", "3")], string="Rating")
    sex = fields.Selection([("male", "Male"), ("female", "Female")], string="Sex")
    system_field_10 = fields.Char(string="System Field 10")
    taz = fields.Char(string="Taz")
    valid_taz = fields.Boolean(string="Valid Taz", readonly=True)
    private_insurance = fields.Many2many('private.insurance.tag', string="Private Insurance")
    kupa = fields.Selection([("כללית", "כללית"), ("לאומית", "לאומית"), ("מאוחדת", "מאוחדת"), ("מכבי", "מכבי"),
                             ("משרד ביטחון", "משרד ביטחון"), ("תייר", "תייר"), ("---", "---")], string="Kupa")
    medical_service = fields.Many2one('medical.services', string="Medical Service")
    activity_user_id = fields.Many2one('res.users', string="Owner", readonly=True)
    originating_lead_code = fields.Selection(
        [("דף פייסבוק/ אתר אישי", "דף פייסבוק/ אתר אישי"), ("המלצת לקוח", "המלצת לקוח"), ("המלצת רופא", "המלצת רופא"),
         ("מנוע חיפוש", "מנוע חיפוש"), ("כללית מושלם", "כללית מושלם"), ("חברת ביטוח", "חברת ביטוח"),
         ("המלצת עסק", "המלצת עסק"), ("המלצת איש צוות", "המלצת איש צוות"), ("המלצת רב", "המלצת רב"),
         ("מכבי שבן", "מכבי שבן"), ("אחר", "אחר")],
        string="Rating")
    needs = fields.Html(string="Needs")
    write_uid = fields.Many2one('res.users', string="Updated By", readonly=True)
    write_date = fields.Datetime(string="Updated On", readonly=True)
    id_number = fields.Char(string="Id Number")
    phone_number = fields.Char(string="Phone #2")
    phone_number_search = fields.Char(string="Fax")
    birth_date = fields.Date(string="Date Of Birth")
    action_status_code = fields.Selection(
        [("חדש פלוני", "חדש פלוני"), ("אין מענה", "אין מענה"), ("קשר ראשוני", "קשר ראשוני"),
         ("לא מעוניין", "לא מעוניין"), ("הומר ללקוח", "הומר ללקוח")], string="Action Status Code")
    campaign_id = fields.Char(string="Campaign ID")
    convert_date = fields.Datetime(string="Convert date")
    create_uid = fields.Many2one('res.users', string="Created By", readonly=True)
    create_date = fields.Date(string="Created On", readonly=True)
    income_fireberry = fields.Float(string="Income Fireberry")
