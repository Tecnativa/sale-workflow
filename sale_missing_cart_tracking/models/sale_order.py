# Copyright 2021 Tecnativa - Carlos Dauden
# Copyright 2021 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sale_missing_tracking_ids = fields.One2many(
        comodel_name="sale.missing.tracking",
        inverse_name="order_id",
        ondelete="cascade",
    )

    def _get_missing_exception(self):
        self.ensure_one()
        return self.env["sale.missing.tracking.exception"].search(
            [
                ("partner_id", "=", self.partner_id.id),
                ("state", "=", "approved"),
                ("product_id.sale_missing_tracking", "=", True),
            ]
        )

    def _get_missing_product_domain(self):
        self.ensure_one()
        now = fields.Datetime.now()
        missing_product_exception = self._get_missing_exception().mapped("product_id")
        domain = [
            ("company_id", "=", self.company_id.id),
            ("order_partner_id", "=", self.partner_id.id),
            (
                "product_id",
                "not in",
                (self.order_line.mapped("product_id") + missing_product_exception).ids,
            ),
            ("product_id.sale_missing_tracking", "=", True),
            ("state", "in", ["sale", "done"]),
            (
                "order_id.date_order",
                ">=",
                now - relativedelta(days=self.company_id.sale_missing_days_from),
            ),
            (
                "order_id.date_order",
                "<=",
                now - relativedelta(days=self.company_id.sale_missing_days_to),
            ),
        ]
        return domain

    def _get_missing_products(self):
        self.ensure_one()
        SaleOrderLine = self.env["sale.order.line"]
        groups = SaleOrderLine.sudo().read_group(
            domain=self._get_missing_product_domain(),
            fields=["product_id"],
            groupby=["product_id"],
        )
        missing_product_ids = [group["product_id"][0] for group in groups]
        groups = SaleOrderLine.sudo().read_group(
            domain=[
                ("product_id", "in", missing_product_ids),
                (
                    "order_id.date_order",
                    ">=",
                    fields.Datetime.now()
                    - relativedelta(
                        months=self.company_id.sale_missing_months_consumption
                    ),
                ),
            ],
            fields=["product_id", "price_subtotal"],
            groupby=["product_id"],
        )
        missing_product_dict = {}
        minimal_consumption = self.company_id.sale_missing_minimal_consumption
        for group in groups:
            if group["price_subtotal"] >= minimal_consumption:
                missing_product_dict[group["product_id"][0]] = group["price_subtotal"]
        return missing_product_dict

    def _create_missing_cart_tracking(self):
        missing_product_dict = self._get_missing_products()
        vals_list = []
        for product_id, consumption in missing_product_dict.items():
            vals_list.append(
                {
                    "order_id": self.id,
                    "product_id": product_id,
                    "consumption": consumption,
                    # TODO: To remove because these fields when related works
                    # "partner_id": self.partner_id.id,
                    # "commercial_partner_id": self.partner_id.commercial_partner_id.id,
                    # "date_order": self.date_order,
                    # "user_id": self.user_id.id,
                }
            )
        missing_tracking = self.env["sale.missing.tracking"].sudo().create(vals_list)
        return missing_tracking

    @api.model
    def _action_missing_tracking(self, missing_trackings):
        wiz = self.env["sale.missing.tracking.wiz"].create(
            {"missing_tracking_ids": [(6, 0, missing_trackings.ids)]}
        )
        action = self.env.ref(
            "sale_missing_cart_tracking.action_sale_missing_cart_tracking_wiz"
        ).read()[0]
        action["view_mode"] = "form"
        # action["context"] = {"sale_missing_tracking_ids": missing_trackings.ids}
        action["res_id"] = wiz.id
        action["flags"] = {
            "withControlPanel": False,
        }
        action["context"] = {"form_view_initial_mode": "edit"}
        return action

    def action_confirm(self):
        if not self.env.context.get("bypass_missing_cart_tracking"):
            SaleMissingTracking = self.env["sale.missing.tracking"]
            missing_trackings = SaleMissingTracking.browse()
            # Remove old tracking linked to this order
            SaleMissingTracking.sudo().search([("order_id", "in", self.ids)]).unlink()
            for order in self:
                if not order.partner_id.sale_missing_tracking:
                    continue
                missing_trackings += self._create_missing_cart_tracking()
            if missing_trackings:
                return self._action_missing_tracking(missing_trackings)
        res = super().action_confirm()
        return res

    def action_pending_missing_tracking_reason(self):
        missing_trackings = self.env["sale.missing.tracking"].search(
            [("reason_id", "=", False),]
        )
        return self._action_missing_tracking(missing_trackings)

    def action_cancel(self):
        """ Remove missing tracking linked
        """
        res = super().action_cancel()
        trackings = self.env["sale.missing.tracking"].search([
            ("order_id", "in", self.ids)
        ])
        trackings.state = "cancel"
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines:
            if line.product_id and line.order_id.state == 'sale':
                trackings = self.env["sale.missing.tracking"].search([
                    ("order_id", "=", line.order_id.id),
                    ("product_id", "=", line.product_id.id),
                ])
                trackings.state = "recovered"
        return lines
