import base64
import io

import xlsxwriter

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class CustomerStatementWizard(models.TransientModel):
    _name = "portfolio.customer.statement.wizard"
    _description = "Portfolio Customer Statement"

    partner_id = fields.Many2one("res.partner", required=True)
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True, default=fields.Date.context_today)
    company_currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id, readonly=True)
    line_ids = fields.One2many("portfolio.customer.statement.line", "wizard_id", readonly=True)
    file_data = fields.Binary(readonly=True)
    file_name = fields.Char(readonly=True)

    def _move_lines(self):
        self.ensure_one()
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError(_("The start date must not be after the end date."))
        return self.env["account.move.line"].search([
            ("partner_id", "=", self.partner_id.id), ("parent_state", "=", "posted"),
            ("date", ">=", self.date_from), ("date", "<=", self.date_to),
            ("account_id.account_type", "in", ("asset_receivable", "liability_payable")),
        ], order="date, id")

    def action_generate(self):
        self.ensure_one()
        self.line_ids.unlink()
        running = 0.0
        values = []
        for line in self._move_lines():
            running += line.debit - line.credit
            values.append((0, 0, {"date": line.date, "move_id": line.move_id.id, "label": line.name, "debit": line.debit, "credit": line.credit, "balance": running}))
        self.line_ids = values
        return {"type": "ir.actions.act_window", "res_model": self._name, "view_mode": "form", "res_id": self.id, "target": "new"}

    def action_export_xlsx(self):
        self.ensure_one()
        if not self.line_ids:
            self.action_generate()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = workbook.add_worksheet("Statement")
        header = workbook.add_format({"bold": True, "bg_color": "#D9EAF7"})
        money = workbook.add_format({"num_format": "#,##0.00"})
        for col, title in enumerate(["Date", "Move", "Description", "Debit", "Credit", "Balance"]):
            sheet.write(0, col, title, header)
        for row, line in enumerate(self.line_ids, 1):
            sheet.write(row, 0, str(line.date)); sheet.write(row, 1, line.move_id.name)
            sheet.write(row, 2, line.label or ""); sheet.write_number(row, 3, line.debit, money)
            sheet.write_number(row, 4, line.credit, money); sheet.write_number(row, 5, line.balance, money)
        sheet.set_column(0, 0, 12); sheet.set_column(1, 2, 25); sheet.set_column(3, 5, 14)
        workbook.close()
        self.write({"file_data": base64.b64encode(output.getvalue()), "file_name": f"statement-{self.partner_id.id}.xlsx"})
        return {"type": "ir.actions.act_url", "url": f"/web/content/{self._name}/{self.id}/file_data/{self.file_name}?download=true", "target": "self"}


class CustomerStatementLine(models.TransientModel):
    _name = "portfolio.customer.statement.line"
    _description = "Portfolio Customer Statement Line"
    _order = "date, id"

    wizard_id = fields.Many2one("portfolio.customer.statement.wizard", required=True, ondelete="cascade")
    date = fields.Date(readonly=True)
    move_id = fields.Many2one("account.move", readonly=True)
    label = fields.Char(readonly=True)
    debit = fields.Monetary(readonly=True)
    credit = fields.Monetary(readonly=True)
    balance = fields.Monetary(readonly=True)
    currency_id = fields.Many2one(related="wizard_id.company_currency_id")
