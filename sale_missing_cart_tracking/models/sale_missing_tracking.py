# Copyright 2021 Tecnativa - Carlos Dauden
# Copyright 2021 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class SaleMissingTrackingReason(models.Model):
    _name = "sale.missing.tracking.reason"
    _description = "Sale Missing Cart Tracking Reason"

    name = fields.Char()
    note = fields.Text()
    recovered = fields.Boolean()


class SaleMissingTracking(models.Model):
    _name = "sale.missing.tracking"
    _inherit = ["mail.thread"]
    _description = "Sale Missing Cart Tracking"
    _order = "partner_id, date_order desc, id desc"

    order_id = fields.Many2one(
        comodel_name="sale.order",
        string="Sale order"
    )
    company_id = fields.Many2one(comodel_name="res.company", realated="order_id.company_id", store=True)
    currency_id = fields.Many2one(comodel_name="res.currency", realated="order_id.currency_id", store=True)
    date_order = fields.Datetime(realated="order_id.date_order", store=True, index=True)
    commercial_partner_id = fields.Many2one(comodel_name="res.partner", realated="order_id.commercial_partner_id", store=True)
    partner_id = fields.Many2one(comodel_name="res.partner", realated="order_id.partner_id", store=True, index=True)
    user_id = fields.Many2one(comodel_name="res.users", realated="order_id.user_id", store=True)
    product_id = fields.Many2one(comodel_name="product.product", index=True)
    last_sale_line_id = fields.Many2one(comodel_name="sale.order.line")
    reason_id = fields.Many2one(comodel_name="sale.missing.tracking.reason", index=True)
    reason_note = fields.Text(
        compute="_compute_reason_note",
        store=True,
        readonly=False
    )
    consumption = fields.Monetary()

    def action_open_sale_order(self):
        """
        Action to open sale order related
        """
        self.ensure_one()
        return self.order_id.get_formview_action()

    @api.depends("reason_id")
    def _compute_reason_note(self):
        for rec in self:
            rec.reason_note = rec.reason_id.note
