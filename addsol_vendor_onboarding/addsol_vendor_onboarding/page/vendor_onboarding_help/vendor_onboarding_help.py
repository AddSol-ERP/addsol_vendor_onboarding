# Copyright (c) 2026, Addition Solutions and contributors
# For license information, please see license.txt

"""Desk reader for the Markdown guides shipped with this app."""

import os

import frappe
from frappe.utils.data import md_to_html

GUIDE_FILES = {"Purchase_Manager_User_Manual.md", "Supplier_User_Manual.md"}


def _docs_dir():
    return os.path.realpath(os.path.join(frappe.get_app_path("addsol_vendor_onboarding"), "public", "docs"))


def _first_heading(markdown):
    for line in (markdown or "").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


@frappe.whitelist()
def get_toc():
    """Return titles and routes for Markdown documents in the app's docs folder."""
    docs = _docs_dir()
    items = []

    for filename in sorted(os.listdir(docs)):
        if filename not in GUIDE_FILES:
            continue

        path = os.path.join(docs, filename)
        with open(path, encoding="utf-8") as markdown_file:
            markdown = markdown_file.read(4096)

        route = filename[:-3]
        items.append({
            "route": route,
            "title": _first_heading(markdown) or route.replace("_", " "),
        })

    return {"items": items, "default_route": "Purchase_Manager_User_Manual"}


@frappe.whitelist()
def get_markdown(route):
    """Render one Markdown document, constrained to the app's public/docs folder."""
    route = (route or "").strip().strip("/")
    docs = _docs_dir()
    target = os.path.realpath(os.path.join(docs, route + ".md"))

    if (
        not target.startswith(docs + os.sep)
        or os.path.basename(target) not in GUIDE_FILES
        or not os.path.isfile(target)
    ):
        frappe.throw("Document not found.", frappe.ValidationError)

    with open(target, encoding="utf-8") as markdown_file:
        markdown = markdown_file.read()

    return {
        "route": route,
        "title": _first_heading(markdown) or route.replace("_", " "),
        "html": str(md_to_html(markdown) or ""),
    }
