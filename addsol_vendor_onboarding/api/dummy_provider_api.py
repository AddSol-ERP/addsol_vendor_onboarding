# Copyright (c) 2026, Addition Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _


def validate_supplier_details(supplier_onboarding, validation_requested_at=None):
    """
    Placeholder validation entrypoint for future provider implementations.

    Current behavior marks validation as failed with a clear template message,
    so this provider can be selected safely without breaking background jobs.
    """
    doc = frappe.get_doc("Supplier Onboarding", supplier_onboarding)
    message = _(
        "Dummy Provider is a template only and is not implemented yet. "
        "Please switch provider or implement addsol_vendor_onboarding.api.dummy_provider_api.validate_supplier_details."
    )

    doc.validation_status = "Failed"
    doc.onboarding_status = "Validation Failed"
    doc.validation_remarks = message
    doc.gstn_validated = 0
    doc.pan_validated = 0
    doc.cin_validated = 0
    doc.bank_validated = 0
    doc.udyam_validated = 0
    doc.save(ignore_permissions=True)

    frappe.log_error(
        message=f"{supplier_onboarding}: {message}",
        title="Dummy Provider Placeholder Triggered",
    )


@frappe.whitelist()
def test_connection():
    return {
        "success": False,
        "message": _(
            "Dummy Provider is a placeholder template. "
            "Implement test_connection and validate_supplier_details before production use."
        ),
    }
