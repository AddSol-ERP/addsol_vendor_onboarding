# Copyright (c) 2025, Addition Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _


def boot_session(bootinfo):
    """
    Add custom items to bootinfo.
    This will be available in frappe.boot
    """
    # Debug: Always log that boot script is running
    frappe.logger().info(f"Boot session running for user: {frappe.session.user}")
    frappe.logger().info(f"User roles: {frappe.get_roles()}")
    
    # Add basic flag to test if boot script is working
    bootinfo["addsol_vendor_boot_test"] = True
    
    # Add custom menu items for different roles
    if "Supplier" in frappe.get_roles():
        bootinfo["vendor_onboarding_enabled"] = True
        
        # Debug: Log current user
        frappe.logger().info(f"Boot session for supplier: {frappe.session.user}")
        
        # Check if supplier needs to be redirected to vendor portal
        user_email = frappe.session.user
        supplier = frappe.db.get_value("Supplier", {"email_id": user_email}, ["name", "disabled"])
        
        frappe.logger().info(f"Supplier lookup result: {supplier}")
        
        if supplier:
            supplier_name, disabled = supplier
            frappe.logger().info(f"Supplier {supplier_name}, disabled: {disabled}")
            
            # Check if supplier is disabled or has pending onboarding
            if disabled:
                bootinfo["redirect_to_vendor_portal"] = True
                bootinfo["redirect_reason"] = "supplier_disabled"
                frappe.logger().info("Setting redirect flag - supplier disabled")
            else:
                # Check for pending onboarding applications
                pending_onboarding = frappe.db.exists("Supplier Onboarding", {
                    "supplier": supplier_name,
                    "email": user_email,
                    "onboarding_status": ["in", ["Pending Submission", "Validation Failed", "Data Submitted", "Validation Successful"]]
                })
                
                frappe.logger().info(f"Pending onboarding check: {pending_onboarding}")
                
                if pending_onboarding:
                    bootinfo["redirect_to_vendor_portal"] = True
                    bootinfo["redirect_reason"] = "pending_onboarding"
                    frappe.logger().info("Setting redirect flag - pending onboarding")
        else:
            frappe.logger().info("No supplier record found for user")
    else:
        frappe.logger().info("User does not have Supplier role")
        
    if "Purchase Manager" in frappe.get_roles():
        bootinfo["vendor_onboarding_manager"] = True