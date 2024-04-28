# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from freezegun import freeze_time

from odoo.exceptions import UserError
from odoo.tests.common import users

from .common import TestSaleOrderLimitBase


class TestSaleOrderLimit(TestSaleOrderLimitBase):
    def test_partner_name(self):
        self.assertEqual(self.partner.name, "Mr Odoo")

    def test_partner_misc(self):
        partner = self.env["res.partner"].create({"name": "Mr Odoo"})
        self.assertEqual(partner.name, "Mr Odoo")
        self.assertNotEqual(partner.name, "Mrs Odoo")
        self.assertTrue(partner.active)
        self.assertFalse(partner.skip_sale_order_limit)
        all_partners = self.env["res.partner"].search([])
        self.assertIn(partner, all_partners)
        self.assertNotIn(partner, partner.child_ids)

    def test_products_category(self):
        self.assertTrue(self.product_a.categ_id)
        self.assertTrue(self.product_b.categ_id)

    def test_sale_order_01(self):
        order = self._create_sale_order()
        self.assertEqual(order.partner_id, self.partner)

    def test_sale_order_02(self):
        order = self._create_sale_order()
        self.assertEqual(order.partner_id, self.partner)
        self.assertEqual(order.state, "draft")
        self.assertEqual(len(order.order_line), 2)
        line_a = order.order_line.filtered(lambda x: x.product_id == self.product_a)
        self.assertEqual(line_a.price_unit, 100)
        self.assertEqual(line_a.price_subtotal, 100)
        line_b = order.order_line.filtered(lambda x: x.product_id == self.product_b)
        self.assertEqual(line_b.price_unit, 200)
        self.assertEqual(line_b.price_subtotal, 400)
        self.assertEqual(order.amount_untaxed, 500)  # 500 = 100 + 400
        order.action_confirm()
        self.assertEqual(order.state, "sale")

    @users("test-user")
    def test_sale_order_03(self):
        order = self._create_sale_order()
        self.assertEqual(order.user_id, self.user)

    @freeze_time("2024-01-01 08:00")
    def test_sale_order_04(self):
        order = self._create_sale_order()
        self.assertEqual(order.date_order.date(), date(2024, 1, 1))

    def test_sale_order_limit_01(self):
        order = self._create_sale_order()
        order.order_line.price_unit = 10
        with self.assertRaises(UserError):
            order.action_confirm()
        order.partner_id.skip_sale_order_limit = True
        order.action_confirm()
        self.assertEqual(order.state, "sale")

    def test_sale_order_limit_02(self):
        order = self._create_sale_order()
        order.action_confirm()
        self.assertEqual(order.state, "sale")

    def test_sale_order_report(self):
        order = self._create_sale_order()
        res = self.env["ir.actions.report"]._render(
            "sale.report_saleorder", order.ids, {}
        )
        self.assertRegex(str(res[0]), "Mr Odoo")
