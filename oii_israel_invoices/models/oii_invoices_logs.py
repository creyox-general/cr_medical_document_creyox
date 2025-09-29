from odoo import _, api, Command, fields, models


def scrub_text(json, item):
    if json.get(item):
        json[item] = '*' * (len(json[item]) - 4) + json[item][-4:]


def scrub_request(json):
    if json and isinstance(json, dict):
        scrub_text(json, 'client_id')
        scrub_text(json, 'client_secret')
        scrub_text(json, 'refresh_token')
        scrub_text(json, 'access_token')
    return json


def scrub_header(json):
    if json and isinstance(json, dict) and json.get('Authorization') and 'Bearer' in json.get('Authorization'):
        auth = json['Authorization']
        parts = auth.split(' ')
        parts[1] = '*' * (len(parts[1]) - 4) + parts[1][-4:]
        json['Authorization'] = ' '.join(parts)
    return json


class OiiInvoicesLogs(models.Model):
    _name = 'oii.invoices.logs'
    _description = "Israel Invoices API Logs"
    _order = 'create_date desc'
    _rec_name = 'object_id'

    @api.model
    def _get_model_selection(self):
        _LIST = ['account.move', 'res.config.settings']
        models = self.env['ir.model'].search(
            [('model', 'in', _LIST)])
        return [(m.model, m.name) for m in models]

    object_id = fields.Reference(
        _get_model_selection,
        compute='_compute_object_id_ref',
        string="Record"
    )
    parent_res_id = fields.Integer('Res ID', index=True)
    parent_res_model = fields.Char('Model', index=True)
    method = fields.Selection([
        ('post', "POST"),
        ('put', "PUT"),
        ('get', "GET"),
        ('delete', "DELETE")
    ], string="Method")
    type = fields.Selection([
        ('setting', 'Settings'),
        ('invoice', 'Invoices'),
    ], string="Type")
    state = fields.Selection([
        ('new', "New"), ('success', 'Successful'), ('fail', "Failed")],
        default='new'
    )
    user_id = fields.Many2one(
        'res.users', string="Executed By", default=lambda self: self.env.user
    )
    end_point = fields.Char("EndPoint")
    headers = fields.Char("Headers")
    request_body = fields.Text("Request Body")
    response = fields.Text("Response")
    failure_reason = fields.Text("Failure Reason")
    status_code = fields.Char("Status Code")

    @api.depends('parent_res_model', 'parent_res_id')
    def _compute_object_id_ref(self):
        self.object_id = None
        for this in self:
            if this.parent_res_id and this.parent_res_model and self.env[this.parent_res_model].browse(
                    this.parent_res_id).exists():
                this.object_id = '%s,%s' % (
                    this.parent_res_model, this.parent_res_id or 0
                )
            else:
                this.object_id = None

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['request_body'] = scrub_request(vals['request_body'])
            vals['headers'] = scrub_header(vals['headers'])
            if 'oauth2' in vals.get('end_point') and vals.get('response'):
                vals['response'] = scrub_request(vals['response'])
        return super().create(vals_list)
