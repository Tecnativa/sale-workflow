# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import Form, new_test_user

from odoo.addons.base.tests.common import BaseCommon


class TestSaleOrderLimitBase(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, test_sale_order_limit=True))
        cls.partner = cls.env["res.partner"].create({"name": "Mr Odoo"})
        cls.product_a = cls.env["product.product"].create(
            {"name": "Test product A", "list_price": 100}
        )
        cls.product_b = cls.env["product.product"].create(
            {"name": "Test product B", "list_price": 200}
        )
        cls.user = new_test_user(
            cls.env,
            login="test-user",
            groups="sales_team.group_sale_salesman_all_leads",
        )

    def _create_sale_order(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product_a
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product_b
            line_form.product_uom_qty = 2
        return order_form.save()
