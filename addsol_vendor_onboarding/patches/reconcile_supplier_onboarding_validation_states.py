# Copyright (c) 2025, Addition Solutions and contributors
# For license information, please see license.txt

import frappe

from addsol_vendor_onboarding.api import _reconcile_supplier_onboarding_validation_states


def execute():
    result = _reconcile_supplier_onboarding_validation_states()
    frappe.db.commit()
    frappe.logger().info(
        "Supplier onboarding validation reconciliation complete. "
        f"Processed={result['processed']}, "
        f"Updated={result['updated']}, "
        f"Validated={result['validated']}, "
        f"Failed={result['failed']}, "
        f"InProgress={result['in_progress']}"
    )
