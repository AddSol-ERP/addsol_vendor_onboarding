# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import glob
import json
import os

import frappe
from frappe.modules.import_file import import_file_by_path


WORKSPACE_META_KEYS = {
    "name",
    "owner",
    "creation",
    "modified",
    "modified_by",
    "docstatus",
    "doctype",
    "parent",
    "parentfield",
    "parenttype",
    "idx",
}

WORKSPACE_FIELDS = (
    "module",
    "label",
    "title",
    "icon",
    "public",
    "is_hidden",
    "content",
    "parent_page",
    "for_user",
    "sequence_id",
    "hide_custom",
)

WORKSPACE_CHILD_TABLES = (
    "links",
    "shortcuts",
    "number_cards",
    "charts",
    "quick_lists",
    "custom_blocks",
    "roles",
)


def _read_json(path):
    with open(path, "r") as handle:
        return json.load(handle)


def _clean_row(row):
    return {k: v for k, v in row.items() if k not in WORKSPACE_META_KEYS}


def _upsert_workspace_from_json(path):
    payload = _read_json(path)
    workspace_name = payload.get("name")
    if not workspace_name:
        return

    if frappe.db.exists("Workspace", workspace_name):
        workspace = frappe.get_doc("Workspace", workspace_name)
    else:
        workspace = frappe.new_doc("Workspace")
        workspace.name = workspace_name

    for fieldname in WORKSPACE_FIELDS:
        if fieldname in payload:
            workspace.set(fieldname, payload.get(fieldname))

    for child_table in WORKSPACE_CHILD_TABLES:
        rows = [_clean_row(row) for row in (payload.get(child_table) or [])]
        workspace.set(child_table, rows)

    workspace.flags.ignore_mandatory = True
    workspace.flags.ignore_validate = True
    workspace.save(ignore_permissions=True)


def execute():
    previous_in_patch = frappe.flags.in_patch
    frappe.flags.in_patch = True

    try:
        app_module_path = frappe.get_app_path("addsol_vendor_onboarding", "addsol_vendor_onboarding")

        workspace_json = os.path.join(
            app_module_path,
            "workspace",
            "vendor_onboarding",
            "vendor_onboarding.json",
        )

        number_card_glob = os.path.join(
            app_module_path,
            "number_card",
            "*",
            "*.json",
        )

        for json_path in sorted(glob.glob(number_card_glob)):
            import_file_by_path(json_path, force=True)

        if os.path.exists(workspace_json):
            _upsert_workspace_from_json(workspace_json)

        frappe.clear_cache()
    finally:
        frappe.flags.in_patch = previous_in_patch
