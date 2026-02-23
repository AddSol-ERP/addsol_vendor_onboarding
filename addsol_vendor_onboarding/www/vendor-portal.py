# -*- coding: utf-8 -*-
# Copyright (c) 2025, Addition Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import get_url

PUBLIC_VALIDATION_FAILURE_MESSAGE = _(
    "We could not validate your submitted details at this time. "
    "Please review and resubmit, or contact support."
)

def _sanitize_vendor_remarks(onboarding_status, validation_remarks):
    if onboarding_status == "Validation Failed":
        message = (validation_remarks or "").lower()
        failed_sections = []

        if "gstn" in message:
            failed_sections.append(_("GSTN details"))
        if "pan" in message:
            failed_sections.append(_("PAN details"))
        if "cin" in message:
            failed_sections.append(_("CIN details"))
        if "bank" in message:
            failed_sections.append(_("Bank details"))
        if "udyam" in message or "udyog" in message:
            failed_sections.append(_("Udyam details"))

        if failed_sections:
            if len(failed_sections) == 1:
                section_text = failed_sections[0]
            elif len(failed_sections) == 2:
                section_text = _("{0} and {1}").format(failed_sections[0], failed_sections[1])
            else:
                section_text = _("{0}, and {1}").format(", ".join(failed_sections[:-1]), failed_sections[-1])
            return _(
                "{0} could not be verified. Please review and resubmit, or contact support."
            ).format(section_text)

        if validation_remarks and "api error" not in message and "traceback" not in message:
            return validation_remarks
        return PUBLIC_VALIDATION_FAILURE_MESSAGE
    return validation_remarks


def get_context(context):
    """
    Context for supplier portal page.
    This is a WEB PAGE for Website Users (Suppliers).
    """
    context.no_cache = 1
    
    # Check if user is logged in
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login"
        raise frappe.Redirect
    
    # Get current user's email
    user_email = frappe.session.user
    
    # Check if this user has Supplier role
    if not ("Supplier" in frappe.get_roles(user_email)):
        # Show user-friendly message instead of technical error
        context.access_denied = True
        context.error_title = _("Supplier Portal Access Required")
        context.error_message = _("This portal is only for registered suppliers. Please contact the Purchase team if you believe you should have access.")
        context.support_email = "contact@aitspl.com"
        return context
    
    # Get supplier associated with this email (include disabled suppliers for onboarding)
    supplier = frappe.db.get_value("Supplier", {"email_id": user_email}, ["name", "disabled"])
    
    # Check if supplier is disabled and add context for messaging
    if supplier and supplier[1]:  # disabled = True
        context.supplier_disabled = True
        context.redirect_reason = "supplier_disabled"
    
    # Check for pending onboarding
    if supplier:
        supplier_name = supplier[0]
        pending_onboarding = frappe.db.exists("Supplier Onboarding", {
            "supplier": supplier_name,
            "email": user_email,
            "onboarding_status": ["in", ["Pending Submission", "Validation Failed", "Data Submitted", "Validation Successful"]]
        })
        
        if pending_onboarding:
            context.has_pending_redirect = True
            context.redirect_reason = "pending_onboarding"
    
    if supplier:
        supplier_name = supplier[0]
        # Get onboarding records for this supplier
        onboarding_list = frappe.get_list(
            "Supplier Onboarding",
            filters={"supplier": supplier_name, "email": user_email},
            fields=[
                "name", 
                "onboarding_status", 
                "validation_status", 
                "creation", 
                "modified",
                "gstn",
                "pan",
                "cin",
                "bank_account_no",
                "udyog_aadhaar",
                "gstn_validated",
                "pan_validated",
                "cin_validated",
                "bank_validated",
                "udyam_validated",
                "validation_remarks",
                "rejection_reason"
            ],
            order_by="creation desc"
        )
        
        context.supplier = supplier_name
        for rec in onboarding_list:
            rec.validation_remarks = _sanitize_vendor_remarks(
                rec.onboarding_status, rec.validation_remarks
            )
        context.onboarding_list = onboarding_list
        context.has_pending = any(
            rec.onboarding_status == "Pending Submission" 
            for rec in onboarding_list
        )
    else:
        context.supplier = None
        context.onboarding_list = []
        context.has_pending = False
    
    context.title = _("Supplier Onboarding Portal")
    context.show_sidebar = False
    
    return context
