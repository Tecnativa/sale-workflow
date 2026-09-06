# Copyright 2025 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import models
from odoo.tools import float_is_zero, float_round


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_procurement_values(self):
        values = super()._prepare_procurement_values()
        values["secondary_uom_id"] = self.secondary_uom_id.id
        values["secondary_uom_qty"] = self.env.context.get(
            "procure_secondary_uom_qty", {}
        ).get(self.id, self.secondary_uom_qty)
        return values

    def write(self, vals):
        lines = self.env["sale.order.line"]
        digits = self.env["decimal.precision"].precision_get("Product Unit")
        if "secondary_uom_qty" in vals:
            lines = self.filtered(lambda r: r.state == "sale" and not r.is_expense)
            procure_secondary_uom_qty = {
                line.id: float_round(
                    vals["secondary_uom_qty"] - line.secondary_uom_qty,
                    precision_digits=digits,
                )
                for line in lines
            }
            self = self.with_context(  # noqa: PLW0642
                procure_secondary_uom_qty=procure_secondary_uom_qty
            )
        res = super().write(vals)
        if lines and "product_uom_qty" not in vals:
            # A pure secondary_uom_qty edit never changes product_uom_qty, so
            # launching the stock rules creates no move for it and the moves
            # already created keep their count: the correction goes to the
            # moves still pending instead, which also recomputes their
            # quantity from the new count
            for line in lines:
                pending_moves = line.move_ids.filtered(
                    lambda m: m.state not in ("done", "cancel")
                )
                if len(pending_moves) == 1:
                    pending_moves.secondary_uom_qty = line.secondary_uom_qty
                elif len(pending_moves) > 1:
                    # Several pending moves (e.g. a backorder alongside an
                    # earlier leg not processed yet) share the corrected total
                    # as they shared the previous one, the last one taking
                    # what is left so that the total adds up exactly
                    previous_total = sum(pending_moves.mapped("secondary_uom_qty"))
                    remaining = line.secondary_uom_qty
                    *moves_to_share, last_move = pending_moves
                    for move in moves_to_share:
                        if float_is_zero(previous_total, precision_digits=digits):
                            # Nothing to base a proportion on: split evenly
                            share = float_round(
                                line.secondary_uom_qty / len(pending_moves),
                                precision_digits=digits,
                            )
                        else:
                            share = float_round(
                                line.secondary_uom_qty
                                * move.secondary_uom_qty
                                / previous_total,
                                precision_digits=digits,
                            )
                        move.secondary_uom_qty = share
                        remaining -= share
                    last_move.secondary_uom_qty = remaining
        return res
