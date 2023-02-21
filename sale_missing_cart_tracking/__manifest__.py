# Copyright 2021 Tecnativa - Carlos Dauden
# Copyright 2021 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Sale Missing Cart Tracking",
    "summary": "Tracking sale missing products",
    "version": "13.0.1.0.0",
    "development_status": "Beta",
    "category": "Sales",
    "website": "https://github.com/OCA/sale-workflow/",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["carlosdauden"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["sale"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "views/product_views.xml",
        "views/res_partner_views.xml",
        "views/sale_missing_cart_tracking_views.xml",
        "views/sale_missing_cart_tracking_reason_views.xml",
        "views/sale_missing_cart_tracking_exception_views.xml",
        "wizards/sale_missing_cart_tracking_wiz.xml",
    ],
}
