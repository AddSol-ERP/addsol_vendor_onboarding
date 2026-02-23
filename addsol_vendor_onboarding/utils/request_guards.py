# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import frappe
from frappe import _


def block_supplier_profile_edit():
    """
    Prevent Supplier portal users from editing profile through /update-profile.
    """
    user = frappe.session.user
    if not user or user == "Guest":
        return

    request_path = (getattr(frappe.local, "request", None) and frappe.local.request.path) or ""
    if not request_path.startswith("/update-profile"):
        return

    user_roles = frappe.get_roles(user)
    if "Supplier" in user_roles:
        frappe.throw(
            _("Profile updates are not permitted from this portal. Please contact support."),
            frappe.PermissionError,
        )
