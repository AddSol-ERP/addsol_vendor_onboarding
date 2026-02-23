# Copyright (c) 2025, Addition Solutions and contributors
# For license information, please see license.txt

import frappe

from addsol_vendor_onboarding.api import _deduplicate_all_onboarding_attachments


def execute():
    result = _deduplicate_all_onboarding_attachments()
    frappe.db.commit()
    frappe.logger().info(
        "Supplier onboarding attachment cleanup complete. "
        f"Processed={result['total_docs']}, "
        f"Cleaned={result['touched_docs']}, "
        f"Removed={result['removed_files']}"
    )

