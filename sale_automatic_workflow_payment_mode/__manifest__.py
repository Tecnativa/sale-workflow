# © 2016 Camptocamp SA, Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Sale Automatic Workflow - Payment Mode",
    "version": "16.0.1.0.0",
    "author": "Camptocamp,Sodexis,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Sales Management",
    "depends": ["sale_automatic_workflow", "account_payment_sale"],  # oca/bank-payment
    "website": "https://github.com/OCA/sale-workflow",
    "data": [
        "views/account_payment_mode_views.xml",
    ],
    "installable": False,
    "auto_install": True,
}
