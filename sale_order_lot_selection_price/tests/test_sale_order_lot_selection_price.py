# Copyright 2025 Tecnativa - Víctor Martínez
# Copyright 2026 Tecnativa - Eduardo Ezerouali
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command
from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestSaleOrderLotSelectionPrice(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test product",
                "type": "consu",
                "is_storable": True,
                "tracking": "lot",
                "standard_price": 5,
                "lst_price": 50,
            }
        )
        cls.lot_a = cls.env["stock.lot"].create(
            {"product_id": cls.product.id, "standard_price": 10, "lst_price": 100}
        )
        cls.lot_b = cls.env["stock.lot"].create(
            {"product_id": cls.product.id, "standard_price": 20, "lst_price": 200}
        )
        cls.pricelist_list_price = cls.env["product.pricelist"].create(
            {
                "company_id": cls.env.company.id,
                "name": "Test pricelist list_price",
                "currency_id": cls.env.company.currency_id.id,
                "item_ids": [
                    Command.create(
                        {
                            "applied_on": "3_global",
                            "compute_price": "formula",
                            "base": "list_price",
                            "price_discount": 10,
                        }
                    )
                ],
            }
        )
        cls.pricelist_standard_price = cls.env["product.pricelist"].create(
            {
                "company_id": cls.env.company.id,
                "name": "Test pricelist standard_price",
                "currency_id": cls.env.company.currency_id.id,
                "item_ids": [
                    Command.create(
                        {
                            "applied_on": "3_global",
                            "compute_price": "formula",
                            "base": "standard_price",
                            "price_discount": 10,
                        }
                    )
                ],
            }
        )

    def test_sale_order_pricelist_list_price(self):
        self.partner.property_product_pricelist = self.pricelist_list_price
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.lot_id = self.lot_a
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.lot_id = self.lot_b
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
        order = order_form.save()
        line_lot_a = order.order_line.filtered(lambda x: x.lot_id == self.lot_a)
        self.assertEqual(line_lot_a.price_unit, 90)  # 90=100-10%
        line_lot_b = order.order_line.filtered(lambda x: x.lot_id == self.lot_b)
        self.assertEqual(line_lot_b.price_unit, 180)  # 180=200-10%
        line_without_lot = order.order_line.filtered(lambda x: not x.lot_id)
        self.assertEqual(line_without_lot.price_unit, 45)  # 45=50-10%

    def test_sale_order_change_lot_recomputes_price(self):
        self.partner.property_product_pricelist = self.pricelist_list_price
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.lot_id = self.lot_a
        order = order_form.save()
        line = order.order_line
        self.assertEqual(line.price_unit, 90)  # 90=100-10%
        self.assertEqual(line.technical_price_unit, 90)
        line.lot_id = self.lot_b
        self.assertEqual(line.price_unit, 180)  # 180=200-10%
        self.assertEqual(line.technical_price_unit, 180)

    def test_sale_order_zero_price_product_technical_price_unit(self):
        """The lot price must not be flagged as a manually set price."""
        self.product.lst_price = 0
        self.partner.property_product_pricelist = self.pricelist_list_price
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.lot_id = self.lot_a
        order = order_form.save()
        line = order.order_line
        self.assertEqual(line.price_unit, 90)  # 90=100-10%
        self.assertEqual(line.technical_price_unit, 90)

    def test_sale_order_stale_technical_price_unit(self):
        """The web client sends price_unit with a technical_price_unit stuck at
        the 0 price of the product, which sale would keep as is."""
        self.product.lst_price = 0
        self.partner.property_product_pricelist = self.pricelist_list_price
        order = self.env["sale.order"].create({"partner_id": self.partner.id})
        line = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product.id,
                "lot_id": self.lot_a.id,
                "price_unit": 90,  # 90=100-10%
                "technical_price_unit": 0,
            }
        )
        self.assertEqual(line.technical_price_unit, 90)
        # The line is not flagged as manually priced, so it is priced again
        line.lot_id = self.lot_b
        self.assertEqual(line.price_unit, 180)  # 180=200-10%
        self.assertEqual(line.technical_price_unit, 180)

    def test_sale_order_stale_technical_price_unit_on_write(self):
        """Changing the lot from the UI also sends a stale technical price."""
        self.partner.property_product_pricelist = self.pricelist_list_price
        order = self.env["sale.order"].create({"partner_id": self.partner.id})
        line = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product.id,
                "lot_id": self.lot_a.id,
            }
        )
        line.write(
            {
                "lot_id": self.lot_b.id,
                "price_unit": 180,  # 180=200-10%
                "technical_price_unit": 90,  # stale, from lot_a
            }
        )
        self.assertEqual(line.technical_price_unit, 180)

    def test_sale_order_pricelist_standard_price(self):
        self.partner.property_product_pricelist = self.pricelist_standard_price
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.lot_id = self.lot_a
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.lot_id = self.lot_b
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
        order = order_form.save()
        line_lot_a = order.order_line.filtered(lambda x: x.lot_id == self.lot_a)
        self.assertEqual(line_lot_a.price_unit, 9)  # 9=10-10%
        line_lot_b = order.order_line.filtered(lambda x: x.lot_id == self.lot_b)
        self.assertEqual(line_lot_b.price_unit, 18)  # 18=20-10%
        line_without_lot = order.order_line.filtered(lambda x: not x.lot_id)
        self.assertEqual(line_without_lot.price_unit, 4.5)  # 4.5=5-10%
