# Copyright 2020 Tecnativa - Alexandre D. Díaz
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Sale PWA Cache Secondary Unit",
    "summary": "Adds support to cache secondary unit on sales",
    "version": "13.0.1.0.0",
    "development_status": "Beta",
    "category": "Website",
    "website": "https://github.com/OCA/web",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["Tardo"],
    "license": "LGPL-3",
    "application": True,
    "installable": True,
    "depends": [
        "sale_pwa_cache",
        "web_widget_one2many_product_picker_sale_secondary_unit",
    ],
    "data": [
        "templates/assets.xml",
        "views/sale_order_views.xml",
        "views/sale_order_line_views.xml",
        "data/data.xml",
    ],
}
