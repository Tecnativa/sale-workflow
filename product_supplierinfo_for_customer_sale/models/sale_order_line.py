# Copyright 2013-2017 Agile Business Group sagl
#     (<http://www.agilebg.com>)
# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# Copyright 2024 Tecnativa - Víctor Martínez
# Copyright 2024 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    product_customer_code = fields.Char(
        compute="_compute_product_customer_code",
    )

    @api.depends("product_id")
    def _compute_product_customer_code(self):
        for line in self:
            if line.product_id:
                customerinfo = line.product_id._select_customerinfo(
                    partner=line.order_partner_id
                )
                code = customerinfo.product_code
            else:
                code = ""
            line.product_customer_code = code

    def _update_description(self):
        """Add the customer code in the description when applicable.

        This also takes from context the possible customerinfo already searched in
        product_id_change for avoiding duplicated searches.
        """
        if "customerinfo_id" in self.env.context:
            customerinfo = self.env["product.customerinfo"].browse(
                self.env.context["customerinfo_id"]
            )
        else:
            customerinfo = self.product_id._select_customerinfo(
                partner=self.order_partner_id
            )
        if customerinfo and customerinfo.product_code:
            # Avoid to put the standard internal reference
            self = self.with_context(display_default_code=False)
        res = super()._update_description()
        if customerinfo and customerinfo.product_code:
            self.name = f"[{customerinfo.product_code}] {self.name}"
        return res

    @api.onchange("product_id")
    def product_id_change(self):
        """Inject the customerinfo in the context for not repeating the search in
        _update_description + assign the mininum quantity if set.
        """
        for line in self:
            customerinfo = False
            if line.product_id:
                customerinfo = line.product_id._select_customerinfo(
                    partner=line.order_partner_id
                )
            super(
                SaleOrderLine,
                line.with_context(
                    customerinfo_id=customerinfo.id if customerinfo else False
                ),
            ).product_id_change()
            if customerinfo and customerinfo.min_qty:
                line.product_uom_qty = customerinfo.min_qty
        return {}
