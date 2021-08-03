# Copyright 2021 Tecnativa - Carlos Dauden
# Copyright 2021 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class SaleMissingTrackingException(models.Model):
    _name = "sale.missing.tracking.exception"
    _inherit = ["mail.thread"]
    _description = "Sale Missing Cart Tracking Exceptions"
    _order = "date desc, id desc"

    company_id = fields.Many2one(
        comodel_name="res.company",
        default = lambda self: self.env.company,
        required=True
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    user_id = fields.Many2one(comodel_name="res.users")
    partner_id = fields.Many2one(comodel_name="res.partner", required=True)
    product_id = fields.Many2one(comodel_name="product.product", required=True)
    request_date = fields.Datetime(
        string="Request date",
        default=fields.Datetime.now,
    )
    date = fields.Datetime()
    state = fields.Selection([
        ('request', 'Requested'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('recovered', 'Recovered')
    ], default="request")
    active = fields.Boolean(default=True)
    missing_tracking_ids = fields.Many2many(
        comodel_name="sale.missing.tracking",
        string="Missing cart tracking"
    )
    consumption = fields.Monetary()
