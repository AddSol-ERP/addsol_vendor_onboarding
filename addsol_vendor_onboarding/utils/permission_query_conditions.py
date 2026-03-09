# ============================================================================
# PERMISSION QUERY CONDITIONS
# File: utils/permission_query_conditions.py
# ============================================================================

from __future__ import unicode_literals
import frappe


def get_supplier_onboarding_conditions(user, doctype=None):
    """
    Get permission query conditions for Supplier Onboarding based on user role.
    
    Args:
        user: User name
        
    Returns:
        String of SQL conditions
    """
    user_roles = frappe.get_roles(user)

    if (
        "System Manager" in user_roles
        or "Purchase Manager" in user_roles
        or "Vendor Management" in user_roles
    ):
        # Admin users can see all records
        return ""
    
    if "Supplier" in user_roles:
        # Suppliers can only see their own onboarding records
        user_email = frappe.db.get_value("User", user, "email")
        if user_email:
            return "`tabSupplier Onboarding`.`email` = {0}".format(
                frappe.db.escape(user_email, percent=False)
            )
    
    # Other roles get no access
    return "1=0"


def has_supplier_onboarding_permission(doc, ptype=None, user=None, debug=False):
    """
    Check if user has permission for a specific Supplier Onboarding document.
    
    Args:
        doc: Supplier Onboarding document
        ptype: Permission type (read, write, etc.)
        user: User name
        
    Returns:
        Boolean indicating permission
    """
    if not user or not doc:
        return None
    
    user_roles = frappe.get_roles(user)
    
    # System Manager and Purchase Manager have full access
    if "System Manager" in user_roles or "Purchase Manager" in user_roles:
        return None
    
    # Suppliers can only access their own records
    if "Supplier" in user_roles:
        user_email = frappe.db.get_value("User", user, "email")
        if user_email and doc.email == user_email:
            return None
    
    # Vendor Management role has access
    if "Vendor Management" in user_roles:
        return None
    
    return False
