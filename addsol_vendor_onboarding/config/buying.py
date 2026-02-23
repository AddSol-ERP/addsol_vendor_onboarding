# Copyright (c) 2025, Addition Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe import _


def get_data():
    """
    Add Vendor Onboarding items to Buying module.
    This will appear in the Buying workspace/dashboard.
    """
    return [
        {
            "label": _("Vendor Onboarding"),
            "icon": "fa fa-star",
            "items": [
                {
                    "type": "doctype",
                    "name": "Supplier Onboarding",
                    "label": _("Supplier Onboarding"),
                    "description": _("Manage supplier onboarding process"),
                    "onboard": 1,
                },
                {
                    "type": "doctype",
                    "name": "Supplier Validation Log",
                    "label": _("Validation Logs"),
                    "description": _("View supplier validation logs"),
                },
                {
                    "type": "doctype",
                    "name": "Cashfree Settings",
                    "label": _("Cashfree Settings"),
                    "description": _("Configure Cashfree API settings"),
                },
            ]
        },
        {
            "label": _("Reports"),
            "icon": "fa fa-list",
            "items": [
                {
                    "type": "report",
                    "name": "Supplier Onboarding Status",
                    "label": _("Onboarding Status Report"),
                    "doctype": "Supplier Onboarding",
                    "is_query_report": True,
                },
            ]
        },
    ]