{
    "name": "All In One WhatsApp For Odoo V18 Enterprise -  WhatsApp Extended | WhatsApp Automation | WhatsApp Marketing | WhatsApp Chatbot",
    "version": "18.1",
    "author": "TechUltra Solutions Private Limited",
    "category": "Marketing",
    "live_test_url": "https://youtube.com/playlist?list=PL8o8i9mlxsWg0R0lgWBXrDz6bGFJ64lOJ",
    "company": "TechUltra Solutions Private Limited",
    "website": "https://www.techultrasolutions.com/",
    "summary": "The All-in-One WhatsApp Enterprise module integrates comprehensive WhatsApp functionalities into Odoo, including WhatsApp Extended, WhatsApp Marketing, and WhatsApp Chatbot."
               "This module enhances customer communication, enabling real-time messaging, automated responses, and targeted marketing campaigns directly through WhatsApp. "
               "With seamless integration, businesses can manage and track all interactions from within the Odoo platform, improving efficiency and customer engagement",
    "description": """
        All-in-One WhatsApp Enterprise
        All-in-One WhatsApp
        All-in-One
        WhatsApp Marketing
        WhatsApp Extended
        WhatsApp
        WhatsApp Chatbot
        Chatbot
        Marketing
        Odoo ERP
        V18 WhatsApp
        Odoo WhatsApp
        WhatsApp Marketing Enterprise
        Meta
        Facebook
        Integration
        Cloud API
        WhatsApp Cloud API
        Enterprise
    """,
    "depends": ["whatsapp"],
    "data": [

        # whatsapp_extended
        "whatsapp_extended/security/ir.model.access.csv",
        "whatsapp_extended/views/interactive_buttons_views.xml",
        "whatsapp_extended/views/interactive_list_views.xml",
        "whatsapp_extended/views/interactive_product_list_views.xml",
        "whatsapp_extended/views/whatsapp_interactive_template_views.xml",
        "whatsapp_extended/views/whatsapp_template_inherit_views.xml",
        "whatsapp_extended/views/res_partner_inherit_views.xml",
        "whatsapp_extended/views/whatsapp_account_views.xml",

        # tus_whatsapp_marketing_enterprise
        "tus_whatsapp_marketing_enterprise/security/ir.model.access.csv",
        "tus_whatsapp_marketing_enterprise/data/whatsapp_messaging_data.xml",
        "tus_whatsapp_marketing_enterprise/wizard/whatsapp_messaging_schedule_date_views.xml",
        "tus_whatsapp_marketing_enterprise/wizard/test_whatsapp_marketing_views.xml",
        "tus_whatsapp_marketing_enterprise/views/whatsapp_messaging_view.xml",
        "tus_whatsapp_marketing_enterprise/views/whatsapp_messaging_lists_view.xml",
        "tus_whatsapp_marketing_enterprise/views/whatsapp_messaging_lists_contacts_vies.xml",

        # odoo_whatsapp_ent_chatbot
        "odoo_whatsapp_ent_chatbot/security/ir.model.access.csv",
        "odoo_whatsapp_ent_chatbot/data/wa_template.xml",
        "odoo_whatsapp_ent_chatbot/data/whatsapp_chatbot.xml",
        "odoo_whatsapp_ent_chatbot/views/whatsapp_chatbot_script_views.xml",
        "odoo_whatsapp_ent_chatbot/views/discuss_channel_views.xml",
        "odoo_whatsapp_ent_chatbot/views/whatsapp_chatbot_views.xml",
        "odoo_whatsapp_ent_chatbot/views/whatsapp_ir_action_views.xml",
        "odoo_whatsapp_ent_chatbot/views/whatsapp_account_inherit_view.xml",
    ],
    'assets': {
        'web.assets_backend': [
            # whatsapp_extended
            'odoo_all_in_one_whatsapp_ent/static/whatsapp_extended/static/src/xml/AgentsList.xml',
            'odoo_all_in_one_whatsapp_ent/static/whatsapp_extended/static/src/js/agents/**/*',
            'odoo_all_in_one_whatsapp_ent/static/whatsapp_extended/static/src/scss/*.scss',
            'odoo_all_in_one_whatsapp_ent/static/whatsapp_extended/static/src/js/templates/**/*',

            # odoo_whatsapp_ent_chatbot
            'odoo_all_in_one_whatsapp_ent/static/odoo_whatsapp_ent_chatbot/static/src/scss/kanban_view.scss'
        ],
    },
    "price": 249,
    "currency": "USD",
    "installable": True,
    "auto_install": False,
    "license": "OPL-1",
    "images": ["static/description/main_screen.gif"],
}
