# Copyright 2025 Tecnativa - Víctor Martínez
# Copyright 2026 Tecnativa - Eduardo Ezerouali
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _get_product_price_context(self):
        ctx = super()._get_product_price_context()
        ctx.update(sol_lot=self.lot_id)
        return ctx

    @api.depends("lot_id")
    def _compute_price_unit(self):
        return super()._compute_price_unit()

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._sync_lot_technical_price_unit()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if {"lot_id", "price_unit"} & vals.keys():
            self._sync_lot_technical_price_unit()
        return res

    def _sync_lot_technical_price_unit(self):
        for line in self.filtered("lot_id"):
            currency = line.currency_id or line.company_id.currency_id
            if not currency.compare_amounts(line.technical_price_unit, line.price_unit):
                continue
            line.with_context(
                sale_write_from_compute=True
            ).technical_price_unit = line.price_unit
