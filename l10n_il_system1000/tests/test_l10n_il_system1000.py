# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from base64 import b64decode

from odoo.tests.common import TransactionCase


class TestL10nIlSystem1000(TransactionCase):
    def test_export(self):
        wizard = (
            self.env["l10n.il.system1000.export"]
            .with_context(active_ids=self.env["account.move"].search([]).ids)
            .create({})
        )
        wizard.button_export()
        export_data = b64decode(wizard.export_file).decode("iso8859-8").splitlines()
        self.assertTrue(export_data[-1].startswith("Z"))
