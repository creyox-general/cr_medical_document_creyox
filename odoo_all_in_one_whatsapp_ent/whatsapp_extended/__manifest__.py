{
    "name": "Whatsapp Extended  | Odoo Meta WhatsApp Graph API | Odoo V18 Enterprise Edition",
    "version": "18.0",
    "author": "TechUltra Solutions Private Limited",
    "live_test_url": "https://www.youtube.com/playlist?list=PL8o8i9mlxsWivZfvRKeNHP_sXrgvEYD59",
    "website": "www.techultrasolutions.com",
    "category": "Discuss",
    "live_test_url": "https://www.youtube.com/playlist?list=PL8o8i9mlxsWivZfvRKeNHP_sXrgvEYD59",
    "company": "TechUltra Solutions Private Limited",
    "website": "https://www.techultrasolutions.com/",
    "summary": "Odoo Whatsapp Extended module is extended version of whatsapp enterprise",
    "description": """
        Whatsapp Extended,
        Interactive Templates,
        Odoo
        ERP
        Odoo ERP
        WhatsApp
        Whats-App
        Odoo V18 Enterprise Edition""",
    "depends": ["whatsapp", "base_automation"],
    "data": [
        "security/ir.model.access.csv",
        "views/interactive_buttons_views.xml",
        "views/interactive_list_views.xml",
        "views/interactive_product_list_views.xml",
        "views/whatsapp_interactive_template_views.xml",
        "views/whatsapp_template_inherit_views.xml",
        # "views/ir_actions.xml",
        "views/res_partner_inherit_views.xml",
        "views/whatsapp_account_views.xml",

    ],
    'assets': {
        'web.assets_backend': [
            'whatsapp_extended/static/src/xml/message.xml',
            # 'whatsapp_extended/static/src/xml/AgentsList.xml',
            # 'whatsapp_extended/static/src/js/agents/**/*',
            'whatsapp_extended/static/src/scss/*.scss',
            # 'whatsapp_extended/static/src/js/templates/**/*',
        ],
    },
    "price": 19,
    "currency": "USD",
    "installable": True,
    "auto_install": False,
    "application": True,
    "license": "OPL-1",
    "images": ["static/description/main_screen.gif"],
}
