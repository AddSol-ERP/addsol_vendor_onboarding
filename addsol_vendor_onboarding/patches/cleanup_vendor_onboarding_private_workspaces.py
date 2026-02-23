# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import frappe


def execute():
    private_workspaces = frappe.get_all(
        "Workspace",
        filters={"for_user": ["!=", ""]},
        or_filters=[
            {"title": ["in", ["Supplier Onboarding", "Vendor Onboarding"]]},
            {"name": ["like", "Supplier Onboarding-%"]},
            {"name": ["like", "Vendor Onboarding-%"]},
            {"label": ["like", "Supplier Onboarding-%"]},
            {"label": ["like", "Vendor Onboarding-%"]},
        ],
        pluck="name",
    )

    for workspace_name in private_workspaces:
        try:
            frappe.delete_doc("Workspace", workspace_name, ignore_permissions=True, force=True)
        except Exception:
            frappe.log_error(
                title="Workspace Cleanup Error",
                message=f"Failed to delete private workspace {workspace_name}",
            )

    frappe.clear_cache()
