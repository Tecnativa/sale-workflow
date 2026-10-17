# Copyright 2018-2020 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from typing import ClassVar

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _update_order_line_info(self, product, quantity, uom, child_field, **kwargs):
        # The catalog quantity refers to the unit the card shows (see
        # ``SaleOrderLine._get_product_catalog_lines_data``): the secondary unit
        # of the existing line, even when it differs from the product default
        # or the line has none, and the product default sale secondary unit
        # for a new line.
        sol = self.order_line.filtered(lambda line: line.product_id == product)
        secondary_uom = sol.secondary_uom_id if sol else product.sale_secondary_uom_id
        if (
            child_field != "order_line"
            or len(sol) > 1
            or not secondary_uom
            or quantity <= 0
            or self._is_readonly()
        ):
            return super()._update_order_line_info(
                product, quantity, uom, child_field, **kwargs
            )
        # The line is created/updated here instead of delegating to super()
        # because the secondary unit must already be on the line when the stock
        # rule is launched: on create for a confirmed order, and on the
        # product_uom_qty write that `sale_stock` watches to propagate a
        # quantity change. Letting super() set product_uom_qty first and
        # patching the secondary unit afterwards leaves the generated moves
        # with the secondary quantity as their product quantity and no
        # secondary unit at all.
        if sol:
            sol.write(
                {
                    "secondary_uom_id": secondary_uom.id,
                    "secondary_uom_qty": quantity,
                    # `sale_stock` only propagates a quantity change when
                    # product_uom_qty is in the written values, and
                    # `sale_stock_secondary_unit` expects both quantities in the
                    # same write to size the procurement delta.
                    "product_uom_qty": sol._secondary_qty_to_product_qty(
                        secondary_uom, quantity
                    ),
                }
            )
        else:
            vals = self._catalog_prepare_new_line_vals(
                child_field, product, quantity, product.uom_id, **kwargs
            )
            vals.update(
                {
                    "secondary_uom_id": secondary_uom.id,
                    "secondary_uom_qty": quantity,
                }
            )
            # product_uom_qty must be set explicitly for dependent secondary
            # units. Relying on the compute chain fails at create: the
            # product_uom compute recomputes secondary_uom_qty from the
            # still-default product_uom_qty (1.0), and product_uom_qty then ends
            # up derived from that stale value instead of the requested
            # secondary quantity. Independent units keep the default quantity.
            if secondary_uom.dependency_type == "independent":
                vals.pop("product_uom_qty")
            else:
                vals["product_uom_qty"] = quantity * secondary_uom.factor
            sol = self.env["sale.order.line"].create(vals)
        return self._get_updated_order_line_info(sol, product, uom, **kwargs)

    def _get_product_catalog_order_data(self, products, **kwargs):
        # Products not in the order yet are added in their default sale
        # secondary unit, so the card shows it instead of the units of measure
        res = super()._get_product_catalog_order_data(products, **kwargs)
        for product in products.filtered("sale_secondary_uom_id"):
            res[product.id]["uomDisplayName"] = (
                product.sale_secondary_uom_id.display_name
            )
            res[product.id].pop("availableUoms", None)
        return res


class SaleOrderLine(models.Model):
    _inherit = ("sale.order.line", "product.secondary.unit.mixin")
    _name = "sale.order.line"
    _secondary_unit_fields: ClassVar[dict] = {
        "qty_field": "product_uom_qty",
        "uom_field": "product_uom_id",
    }

    secondary_uom_unit_price = fields.Float(
        string="2nd unit price",
        digits="Product Price",
        compute="_compute_secondary_uom_unit_price",
    )

    product_uom_qty = fields.Float(copy=True)

    def _secondary_qty_to_product_qty(self, secondary_uom, secondary_qty):
        """Return the product_uom_qty matching ``secondary_qty`` of
        ``secondary_uom``, the way ``_compute_helper_target_field_qty`` would.
        """
        self.ensure_one()
        if secondary_uom.dependency_type == "independent":
            return self.product_uom_qty
        qty_base = secondary_qty * secondary_uom.factor
        return self.product_id.uom_id._compute_quantity(qty_base, self.product_uom_id)

    @api.depends("secondary_uom_qty", "secondary_uom_id")
    def _compute_product_uom_qty(self):
        res = super()._compute_product_uom_qty()
        for line in self:
            line._compute_helper_target_field_qty()
        return res

    def _compute_product_uom_id(self):
        res = super()._compute_product_uom_id()
        for line in self:
            line._onchange_helper_product_uom_for_secondary()
        return res

    @api.onchange("product_id")
    def _onchange_product_id_secondary_uom(self):
        if self.product_id and not self.env.context.get("skip_secondary_uom_default"):
            self.secondary_uom_id = self.product_id.sale_secondary_uom_id
            if self.product_uom_qty == 1.0:
                self.secondary_uom_qty = 1.0
                self._onchange_helper_product_uom_for_secondary()

    def _get_product_catalog_lines_data(self, parent_record, **kwargs):
        """Show the secondary unit quantity in the catalog when the line uses
        a secondary unit of measure, so it stays consistent with the quantity
        handled in ``SaleOrder._update_order_line_info``. When the line has no
        secondary unit, show its unit of measure instead.
        """
        res = super()._get_product_catalog_lines_data(parent_record, **kwargs)
        if len(self) == 1:
            if self.secondary_uom_id:
                res["quantity"] = self.secondary_uom_qty
                res["uomDisplayName"] = self.secondary_uom_id.display_name
                res.pop("availableUoms", None)
            else:
                res["uomDisplayName"] = self.product_uom_id.display_name
        return res

    @api.depends("secondary_uom_qty", "product_uom_qty", "price_unit")
    def _compute_secondary_uom_unit_price(self):
        for line in self:
            if line.secondary_uom_id:
                try:
                    line.secondary_uom_unit_price = (
                        line.price_subtotal / line.secondary_uom_qty
                    )
                except ZeroDivisionError:
                    line.secondary_uom_unit_price = 0
            else:
                line.secondary_uom_unit_price = 0
