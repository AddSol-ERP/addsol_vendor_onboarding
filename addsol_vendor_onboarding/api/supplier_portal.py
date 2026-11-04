# ============================================================================
# PURCHASE ORDER VALIDATION
# File: api/supplier_portal.py
# ============================================================================

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cint


def disable_new_supplier(doc, method=None):
    """
    Disable new suppliers by default until onboarding is completed.
    Also validate that email is provided for onboarding.
    
    Args:
        doc: Supplier document
        method: Event method (before_insert)
    """
    # Validate email is provided
    if not doc.email_id:
        frappe.throw(_("Email is mandatory for new suppliers as it is required for onboarding process."))
    
    # Set disabled by default for new suppliers
    doc.disabled = 1


def validate_supplier_email(doc, method=None):
    """
    Validate that supplier has email for onboarding process.
    This runs on every save to ensure email is always present.
    
    Args:
        doc: Supplier document
        method: Event method (validate)
    """
    # Check if supplier is being used for onboarding
    if frappe.db.exists("Supplier Onboarding", {"supplier": doc.name}):
        if not doc.email_id:
            frappe.throw(_("Email is mandatory for suppliers participating in onboarding process."))
    
    # Also validate for new suppliers
    if doc.is_new() and not doc.email_id:
        frappe.throw(_("Email is mandatory for new suppliers as it is required for onboarding process."))


def prevent_unapproved_supplier_enable(doc, method=None):
    """
    Block enabling a Supplier outside the approval flow.

    A Supplier may only transition from disabled to enabled when:
    - it has an Approved Supplier Onboarding record, or
    - an active management override is recorded on its onboarding record
      (set via force_enable_supplier by the Vendor Management role), or
    - the current user is a System Manager (administrative escape hatch).

    Disabling a supplier is always allowed.

    Args:
        doc: Supplier document
        method: Event method (validate)
    """
    previous = doc.get_doc_before_save()
    if not previous:
        # New suppliers are disabled by disable_new_supplier (before_insert).
        return

    previous_disabled = cint(previous.get("disabled"))
    current_disabled = cint(doc.get("disabled"))
    if previous_disabled == current_disabled or current_disabled:
        # No change, or the supplier is being disabled: always allowed.
        return

    # Enabling the supplier: require approval, an active override, or System Manager.
    if frappe.db.exists(
        "Supplier Onboarding", {"supplier": doc.name, "onboarding_status": "Approved"}
    ):
        return

    if frappe.db.exists(
        "Supplier Onboarding", {"supplier": doc.name, "supplier_enable_override": 1}
    ):
        return

    if "System Manager" in frappe.get_roles():
        return

    frappe.throw(
        _(
            "Supplier {0} cannot be enabled directly. Complete the onboarding "
            "approval, or ask a Vendor Management user to enable it with an "
            "override."
        ).format(frappe.bold(doc.name))
    )


@frappe.whitelist()
def validate_purchase_order(doc, method=None):
    """
    Validate that Purchase Order is only created for approved suppliers.
    Exception: Users with 'Vendor Management' role can create emergency POs.
    Suppliers enabled through a management override are also accepted.
    
    Args:
        doc: Purchase Order document
        method: Event method (before_validate/validate)
    """
    # Check if user has Vendor Management role (can create emergency PO)
    if "Vendor Management" in frappe.get_roles():
        return
    
    # Check if supplier is approved
    if doc.supplier:
        supplier_onboarding = frappe.db.exists("Supplier Onboarding", {
            "supplier": doc.supplier,
            "onboarding_status": "Approved"
        })
        
        if not supplier_onboarding:
            # A management override (Vendor Management) also opens the PO gate.
            overridden = frappe.db.exists("Supplier Onboarding", {
                "supplier": doc.supplier,
                "supplier_enable_override": 1
            })
            if overridden:
                return

            frappe.throw(_(
                "Purchase Order cannot be created for supplier {0}. "
                "The supplier must complete the onboarding process and be approved."
            ).format(frappe.bold(doc.supplier)))
