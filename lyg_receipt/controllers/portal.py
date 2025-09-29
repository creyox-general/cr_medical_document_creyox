#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, \
    pager as portal_pager
from odoo.exceptions import AccessError, MissingError, ValidationError
from collections import OrderedDict
from odoo.http import request
from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment.controllers import portal as payment_portal
from odoo.osv import expression

class Portal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'receipt_count' in counters:
            receipt_count = request.env['lyg.account.receipt'].search_count(
                self.common_domain_for_receipt()) \
                if request.env['lyg.account.receipt'].check_access_rights(
                'read', raise_exception=False) else 0
            values['receipt_count'] = receipt_count
        return values

    def _receipt_get_page_view_values(self, receipt, access_token, **kwargs):
        values = {
            'page_name': 'receipt',
            'receipt': receipt,
        }
        return self._get_page_view_values(receipt, access_token, values,
                                          'my_receipt_history', False,
                                          **kwargs)
    def common_domain_for_receipt(self):
        """ Define: #HT01338
        :return: domain for search receipt
        """
        domain = [
            ('state', '=', 'post'),
            # '|',
            # ('receipt_user_id', '=', request.env.user.id),
            ('partner_id', '=', request.env.user.partner_id.id)
        ]
        return domain

    def _get_receipt_searchbar_filters(self):
        """Define: #HT01338

        Returns a dictionary of filters for the receipt search bar.

        :return: Dictionary where keys are filter identifiers and values are dictionaries with 'label' for display name
              and 'domain' for filter conditions
        """
        return {
            'all': {'label': _('All'), 'domain': []},
            'receipt': {'label': _('Receipt'),
                        'domain': [('is_credit_receipt', '=', False)]},
            'credit_receipt': {'label': _('Credit Receipt'),
                               'domain': [('is_credit_receipt', '=', True)]},
        }

    def _prepare_my_receipt_values(self, page, date_begin, date_end, sortby,
                                   filterby, domain=None, url="/my/receipt"):
        """Define: #HT01338

         Prepares the values required to render the receipt view in the portal.

        :param page: Current page number for pagination.
        :param date_begin: Start date for filtering receipts by creation date.
        :param date_end: End date for filtering receipts by creation date.
        :param sortby: Key for determining sorting method (currently unused).
        :param filterby: Key for filtering receipts using predefined filter domains.
        :param domain: Additional domain conditions to apply to the search.
        :param url: Base URL for pagination and filtering actions.
        :return: Dictionary of values used for rendering the portal receipt view
        """
        values = self._prepare_portal_layout_values()
        receipt_obj = request.env['lyg.account.receipt']
        domain = expression.AND([
            domain or [],
            self.common_domain_for_receipt(),
        ])

        # searchbar_sortings = self._get_account_searchbar_sortings()
        # default sort by order
        # if not sortby:
        #     sortby = 'date'
        # order = searchbar_sortings[sortby]['order']

        searchbar_filters = self._get_receipt_searchbar_filters()
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin),
                       ('create_date', '<=', date_end)]

        values.update({
            'date': date_begin,
            # content according to pager and archive selected
            # lambda function to get the receipts recordset
            # when the pager will be defined in the main method of a route
            'receipts': lambda pager_offset: (
                [
                    receipt
                    for receipt in receipt_obj.search(
                    domain, limit=self._items_per_page, offset=pager_offset,
                    order='date desc'
                )
                ]
                if receipt_obj.has_access('read') else
                receipt_obj
            ),
            'page_name': 'receipt',
            'pager': {  # vals to define the pager.
                "url": url,
                "url_args": {'date_begin': date_begin, 'date_end': date_end,
                             'sortby': sortby, 'filterby': filterby},
                "total": receipt_obj.search_count(
                    domain) if receipt_obj.has_access('read') else 0,
                "page": page,
                "step": self._items_per_page,
            },
            'default_url': url,
            # 'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(
                sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
        return values

    @http.route(['/my/receipt', '/my/receipt/page/<int:page>'], type='http',
                auth="public", website=True)
    def portal_my_receipts(self, page=1, date_begin=None, date_end=None,
                           sortby=None, filterby=None, **kw):
        """Define: #HT01338
        Handles the HTTP route for displaying receipts in the user portal.

        This method prepares the data needed to render the receipts page for the logged-in user,
        including pagination, filtering, and date range selection. It stores the recent receipt
        history in the session and renders the appropriate QWeb template.

        :param page: The current page number for pagination. Defaults to 1.
        :param date_begin: The start date for filtering receipts. Defaults to None
        :param date_end: The end date for filtering receipts. Defaults to None.
        :param sortby: Sorting option (currently not implemented). Defaults to None.
        :param filterby: Selected filter for receipt types (e.g., 'all', 'receipt', 'credit_receipt').
        :param kw: Additional keyword arguments from the request
        :return:  werkzeug.wrappers.Response: Rendered QWeb template for the receipts portal page.
        """
        values = self._prepare_my_receipt_values(page, date_begin, date_end,
                                                 sortby, filterby)
        # pager
        pager = portal_pager(**values['pager'])

        # content according to pager and archive selected
        receipts = values['receipts'](pager['offset'])
        request.session['my_receipts_history'] = [i.id for i in
                                                  receipts][:100]
        values.update({
            'receipts': receipts,
            'pager': pager,
        })
        return request.render("lyg_receipt.portal_my_receipts", values)

    @http.route(['/my/receipt/<int:receipt_id>'], type='http', auth="user",
                website=True)
    def portal_my_receipt_detail(self, receipt_id, access_token=None,
                                 report_type=None, download=False, **kw):
        try:
            receipt_sudo = self._document_check_access('lyg.account.receipt',
                                                       receipt_id,
                                                       access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=receipt_sudo,
                                     report_type=report_type,
                                     report_ref='lyg_receipt.action_report_receipt',
                                     download=download)

        values = self._receipt_get_page_view_values(receipt_sudo, access_token,
                                                    **kw)
        return request.render("lyg_receipt.portal_receipt_page", values)
