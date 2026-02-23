from frappe import _

def get_data():
    """
    Desktop configuration for Supplier Onboarding module.
    This creates a separate module icon on the desk.
    """
    return [
        {
            "module_name": "Addsol Vendor Onboarding",
            "category": "Modules",
            "label": _("Supplier Onboarding"),
            "color": "#FF5733",
            "icon": "octicon octicon-organization",
            "type": "module",
            "description": _("Manage supplier onboarding and validation"),
            "onboard": 1,
        }
    ]
