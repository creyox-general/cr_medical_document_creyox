import logging
from odoo import models, fields


from odoo.fields import Datetime
_logger = logging.getLogger(__name__)


class R60Lineholder(models.TransientModel):
    _name = 'bizzup.856.r60.lineholder'
    _description = 'Lines to hold R60 PDFs for 856 wizard'

    wizard_id = fields.Many2one('bizzup.856.wizard', ondelete='cascade')
    name = fields.Char("R60 Condition String")
    pdf_data = fields.Binary("PDF File", readonly=True, attachment=False)
    pdf_filename = fields.Char("PDF Filename")

