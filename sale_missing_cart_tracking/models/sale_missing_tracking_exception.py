# Copyright 2021 Tecnativa - Carlos Dauden
# Copyright 2021 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class SaleMissingTrackingException(models.Model):
    _name = "sale.missing.tracking.exception"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Sale Missing Cart Tracking Exceptions"
    _order = "date desc, id desc"

    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company,
        required=True
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    user_id = fields.Many2one(comodel_name="res.users")
    partner_id = fields.Many2one(comodel_name="res.partner", required=True)
    product_id = fields.Many2one(comodel_name="product.product", required=True)
    request_date = fields.Datetime(
        string="Request date",
        default=fields.Datetime.now,
    )
    date = fields.Datetime()
    state = fields.Selection([
        ('request', 'Requested'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('recovered', 'Recovered')
    ], default="request")
    active = fields.Boolean(default=True)
    missing_tracking_ids = fields.Many2many(
        comodel_name="sale.missing.tracking",
        relation="missing_tracking_exception_missing_tracking_rel",
        column1="exception_id",
        column2="tracking_id",
        string="Missing cart tracking"
    )
    reason_id = fields.Many2one(
        comodel_name="sale.missing.tracking.reason", index=True)
    reason_note = fields.Text(
        compute="_compute_reason_note",
        store=True,
        readonly=False
    )
    consumption = fields.Monetary()

    @api.constrains("partner_id", "product_id")
    def _check_unique_partner_product_approved(self):
        exceptions = self.search([
            ("partner_id", "in", self.mapped("partner_id").ids),
            ("product_id", "=", self.mapped("product_id").ids),
            ("state", "in", ["approved", "request"]),
            ("id", "not in", self.ids),
        ])
        message = ""
        for rec in self:
            if exceptions.filtered(lambda e: e.partner_id == rec.partner_id and
                                             e.product_id == rec.product_id):
                message += "\nPartner: %s Product: %s" % (rec.partner_id.name, rec.product_id.display_name)
        if message:
            raise ValidationError(
                _("You already have exceptions for" + message)
            )

    @api.depends("reason_id")
    def _compute_reason_note(self):
        for rec in self:
            rec.reason_note = rec.reason_id.note

    def action_request(self):
        """To extend in other modules
        """
        pass

    def action_approve(self):
        self.state = "approved"
        self.date = fields.Datetime.now()

    def action_refuse(self):
        self.state = "refused"
        self.date = fields.Datetime.now()

    # @api.model
    # def get_exceptions(self, partners, products, states=["request, approved"]):
    #     exceptions = self.search([
    #         ("partner_id", "in", partners.ids),
    #         ("product_id", "in", products.ids),
    #         ("state", "in", states),
    #     ])
    #     return exceptions

    def _update_tracking_state(self, vals):
        if vals["state"] == "request":
            states = ["draft"]
        else:
            states = ["draft", "request"]
        for rec in self:
            trackings = self.env["sale.missing.tracking"].search([
                ("partner_id", "=", rec.partner_id.id),
                ("product_id", "=", rec.product_id.id),
                ("state", "in", states),
            ])
            trackings.state = vals["state"]
            rec.missing_tracking_ids = trackings

    @api.model
    def create(self, vals):
        rec = super().create(vals)
        if rec and "state" in vals:
            rec._update_tracking_state(vals)
        return rec

    def write(self, vals):
        if "state" in vals:
            self._update_tracking_state(vals)
        return super().write(vals)

    def _log_activity(self):
        self.activity_schedule(
            'sale_missing_cart_tracking.mail_activity_data_warning',
            summary="Sale missing cart tracking exception request",
            note="To approve",
            user_id=responsible.id or SUPERUSER_ID
        )
