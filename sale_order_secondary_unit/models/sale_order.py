<<<<<<< HEAD
# Copyright 2018-2020 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = ["sale.order.line", "product.secondary.unit.mixin"]
    _name = "sale.order.line"
    _secondary_unit_fields = {
        "qty_field": "product_uom_qty",
        "uom_field": "product_uom",
    }

    secondary_uom_qty = fields.Float(string="2nd Qty", digits="Product Unit of Measure")
    secondary_uom_id = fields.Many2one(
        comodel_name="product.secondary.unit",
        string="2nd uom",
        ondelete="restrict",
    )

    secondary_uom_unit_price = fields.Float(
        string="2nd unit price",
        digits="Product Unit of Measure",
        store=False,
        readonly=True,
        compute="_compute_secondary_uom_unit_price",
    )

    product_uom_qty = fields.Float(
        store=True, readonly=False, compute="_compute_product_uom_qty", copy=True
    )

    @api.depends("secondary_uom_qty", "secondary_uom_id", "product_uom_qty")
    def _compute_product_uom_qty(self):
        self._compute_helper_target_field_qty()

    @api.onchange("product_uom")
    def onchange_product_uom_for_secondary(self):
        self._onchange_helper_product_uom_for_secondary()

    @api.onchange("product_id")
    def product_id_change(self):
        """
        If default sales secondary unit set on product, put on secondary
        quantity 1 for being the default quantity. We override this method,
        that is the one that sets by default 1 on the other quantity with that
        purpose.
        """
        # Determine if we compute the sale line with one unit of secondary uom as default.
        # Based on method of sale order line _update_taxes
        default_secondary_qty = 0.0
        if (
            not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id)
        ) and not self.product_uom_qty:
            default_secondary_qty = 1.0
        res = super().product_id_change()
        if self.product_id.sale_secondary_uom_id:
            line_uom_qty = self.product_uom_qty
            self.secondary_uom_id = self.product_id.sale_secondary_uom_id
            if default_secondary_qty:
                self.secondary_uom_qty = default_secondary_qty
                self.onchange_product_uom_for_secondary()
            else:
                self.product_uom_qty = line_uom_qty
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
=======
# Copyright 2018 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_compare, float_round


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    secondary_uom_qty = fields.Float(
        string='Secondary Qty',
        digits=dp.get_precision('Product Unit of Measure'),
    )
    secondary_uom_id = fields.Many2one(
        comodel_name='product.secondary.unit',
        string='Secondary uom',
        ondelete='restrict',
    )

    @api.onchange('secondary_uom_id', 'secondary_uom_qty')
    def onchange_secondary_uom(self):
        if not self.secondary_uom_id:
            return
        factor = self.secondary_uom_id.factor * self.product_uom.factor
        qty = float_round(
            self.secondary_uom_qty * factor,
            precision_rounding=self.product_uom.rounding
        )
        if float_compare(
                self.product_uom_qty, qty,
                precision_rounding=self.product_uom.rounding) != 0:
            self.product_uom_qty = qty

    @api.onchange('product_uom_qty')
    def onchange_secondary_unit_product_uom_qty(self):
        if not self.secondary_uom_id:
            return
        factor = self.secondary_uom_id.factor * self.product_uom.factor
        qty = float_round(
            self.product_uom_qty / (factor or 1.0),
            precision_rounding=self.secondary_uom_id.uom_id.rounding
        )
        if float_compare(
                self.secondary_uom_qty, qty,
                precision_rounding=self.secondary_uom_id.uom_id.rounding) != 0:
            self.secondary_uom_qty = qty

    @api.onchange('product_uom')
    def onchange_product_uom_for_secondary(self):
        if not self.secondary_uom_id:
            return
        factor = self.product_uom.factor * self.secondary_uom_id.factor
        qty = float_round(
            self.product_uom_qty / (factor or 1.0),
            precision_rounding=self.product_uom.rounding
        )
        if float_compare(
                self.secondary_uom_qty, qty,
                precision_rounding=self.product_uom.rounding) != 0:
            self.secondary_uom_qty = qty

    @api.onchange('product_id')
    def onchange_secondary_unit_product_id(self):
        self.secondary_uom_id = self.product_id.sale_secondary_uom_id
>>>>>>> [11.0][NEW] sale_order_secondary_unit: New module for sale in a secondary product unit
