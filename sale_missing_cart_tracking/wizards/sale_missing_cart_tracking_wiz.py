# Copyright 2021 Tecnativa - Carlos Dauden
# Copyright 2021 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleMissingTrackingWiz(models.TransientModel):
    _name = "sale.missing.tracking.wiz"
    _description = "Sale missing tracking wizard"

    missing_tracking_ids = fields.Many2many(
        comodel_name="sale.missing.tracking",
        compute="_compute_missing_tracking_ids",
        readonly=False
    )
    reason_id = fields.Many2one(
        comodel_name="sale.missing.tracking.reason"
    )

    @api.depends("reason_id")
    def _compute_missing_tracking_ids(self):
        self.missing_tracking_ids = self.env["sale.missing.tracking"].browse(
            self.env.context.get("sale_missing_tracking_ids")
        )

    def missing_tracking_action_confirm(self):
        """Check conditions to allow to confirm a sale order
        """
        if 1 == 1:
            self.with_context(
                bypass_missing_cart_tracking=True
            ).missing_tracking_ids.mapped("order_id").action_confirm()
