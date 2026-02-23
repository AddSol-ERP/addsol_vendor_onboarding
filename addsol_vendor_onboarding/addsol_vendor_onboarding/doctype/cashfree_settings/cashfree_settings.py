# -*- coding: utf-8 -*-
# Copyright (c) 2025, Addition Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

SANDBOX_API_URL = "https://sandbox.cashfree.com/verification"
PRODUCTION_API_URL = "https://api.cashfree.com/verification"


class CashfreeSettings(Document):
    def validate(self):
        self.api_url = SANDBOX_API_URL if self.is_sandbox else PRODUCTION_API_URL
