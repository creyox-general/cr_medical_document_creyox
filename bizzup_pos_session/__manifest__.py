# -*- coding: utf-8 -*-
{
    "name": "Bizzup Pos Session",
    "description": """
        US : HT01223, HT01376
          """,
    "version": "18.0.1.0.0",
    "license": "Other proprietary",
    "author": "Lilach Gilliam",
    "website": "https://bizzup.app",
    "depends": ["point_of_sale"],
    "data": {
        "security/base_groups.xml",
        "security/ir.model.access.csv",
        "views/pos_session_view.xml",
        "views/report_saledetails.xml",
        "views/res_config_view.xml",
    },
    "assets": {
        "point_of_sale._assets_pos": [
            "bizzup_pos_session/static/src/**/*",
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": False,
    "post_init_hook": "post_init",
}
