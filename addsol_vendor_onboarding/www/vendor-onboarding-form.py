# -*- coding: utf-8 -*-
# Copyright (c) 2025, Addition Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import get_url
import json

VENDOR_EDITABLE_ONBOARDING_STATUSES = ("Pending Submission", "Validation Failed", "Rejected")


def get_context(context):
    """
    Form page for suppliers to submit onboarding data.
    """
    context.no_cache = 1
    
    # Check if user is logged in
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login"
        raise frappe.Redirect
    
    # Get onboarding ID from query string
    onboarding_id = frappe.form_dict.get('id')
    
    if not onboarding_id:
        frappe.throw(_("Onboarding ID is required"))
    
    # Get the onboarding record
    try:
        doc = frappe.get_doc("Supplier Onboarding", onboarding_id)
        
        # Check if current user is authorized
        if doc.email != frappe.session.user:
            frappe.throw(_("You are not authorized to access this record"), frappe.PermissionError)
        
        if doc.onboarding_status not in VENDOR_EDITABLE_ONBOARDING_STATUSES:
            frappe.throw(
                _(
                    "You can update details only when onboarding is in Pending Submission, Validation Failed, or Rejected status."
                )
            )
        
        context.doc = doc
        context.title = _("Submit Onboarding Details")
        context.show_sidebar = False
        
    except Exception as e:
        frappe.throw(_("Error loading onboarding record: {0}").format(str(e)))
    
    return context

@frappe.whitelist()
def submit_onboarding_data(onboarding_id, data):
    """
    Submit onboarding data from web form.
    """
    try:
        import json
        if isinstance(data, str):
            data = json.loads(data)
        
        doc = frappe.get_doc("Supplier Onboarding", onboarding_id)
        
        # Security check
        if doc.email != frappe.session.user:
            return {"success": False, "message": "Not authorized"}
        if doc.onboarding_status not in VENDOR_EDITABLE_ONBOARDING_STATUSES:
            return {
                "success": False,
                "message": _(
                    "Details can be updated only when onboarding is Pending Submission, Validation Failed, or Rejected."
                ),
            }
        
        # Update fields
        doc.gstn = data.get('gstn')
        doc.pan = data.get('pan')
        doc.cin = data.get('cin')
        doc.bank_account_no = data.get('bank_account_no')
        doc.bank_ifsc_code = data.get('bank_ifsc_code')
        doc.udyog_aadhaar = data.get('udyog_aadhaar')
        doc.phone_number = data.get('phone_number')
        doc.onboarding_status = "Data Submitted"
        doc.validation_status = "Not Validated"
        doc.gstn_validated = 0
        doc.pan_validated = 0
        doc.cin_validated = 0
        doc.bank_validated = 0
        doc.udyam_validated = 0
        doc.validation_date = None
        doc.validation_remarks = None
        
        doc.save(ignore_permissions=True)
        
        return {"success": True, "message": "Data submitted successfully"}
        
    except Exception as e:
        frappe.log_error(message=str(e), title="Supplier Data Submission Failed")
        return {"success": False, "message": str(e)}
