# ============================================================================
# PURCHASE ORDER VALIDATION
# File: api/supplier_portal.py
# ============================================================================

from __future__ import unicode_literals
import frappe
from frappe import _


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


@frappe.whitelist()
def validate_purchase_order(doc, method=None):
    """
    Validate that Purchase Order is only created for approved suppliers.
    Exception: Users with 'Vendor Management' role can create emergency POs.
    
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
            frappe.throw(_(
                "Purchase Order cannot be created for supplier {0}. "
                "The supplier must complete the onboarding process and be approved."
            ).format(frappe.bold(doc.supplier)))
