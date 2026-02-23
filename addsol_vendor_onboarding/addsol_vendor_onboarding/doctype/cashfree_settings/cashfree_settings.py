# -*- coding: utf-8 -*-
# Copyright (c) 2025, Addition Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

SANDBOX_API_URL = "https://sandbox.cashfree.com/verification"
PRODUCTION_API_URL = "https://api.cashfree.com/verification"

MANDATORY_VALIDATION_FIELDS = (
    ("enable_gstn_validation", "GSTN"),
    ("enable_pan_validation", "PAN"),
    ("enable_bank_validation", "Bank Account"),
)


def get_disabled_mandatory_validations(settings):
    return [label for fieldname, label in MANDATORY_VALIDATION_FIELDS if not getattr(settings, fieldname, 0)]


class CashfreeSettings(Document):
    def validate(self):
        self.api_url = SANDBOX_API_URL if self.is_sandbox else PRODUCTION_API_URL
        disabled = get_disabled_mandatory_validations(self)
        if disabled:
            frappe.msgprint(
                _(
                    "Warning: Mandatory validations are disabled in Cashfree Settings: {0}. "
                    "Supplier verification can be blocked or produce incomplete validation outcomes."
                ).format(", ".join(disabled)),
                title=_("Strong Warning"),
                indicator="orange",
                alert=True,
            )
