# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools import config, float_compare


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        res = super().action_confirm()
        if config["test_enable"] and not self.env.context.get("test_sale_order_limit"):
            return res
        for order in self:
            partner = order.partner_id.commercial_partner_id
            if partner.skip_sale_order_limit:
                continue
            min_amount = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("sale.order.limit_min_amount", default="100")
            )
            min_amount = float(min_amount)
            if (
                not config["test_enable"]
                or (
                    config["test_enable"]
                    and self.env.context.get("test_sale_order_limit")
                )
            ) and float_compare(
                min_amount,
                order.amount_total,
                precision_rounding=order.currency_id.rounding,
            ) == 1:
                raise UserError(
                    _("Order %(name)s does not have the minimum amount %(amount)s.")
                    % {"name": order.name, "amount": min_amount}
                )
        return res
