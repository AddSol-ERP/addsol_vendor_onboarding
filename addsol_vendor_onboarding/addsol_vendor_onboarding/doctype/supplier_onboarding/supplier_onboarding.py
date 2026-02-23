# Copyright (c) 2025, Addition IT Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from addsol_vendor_onboarding.utils.validation_utils import (
    validate_gstn_format,
    validate_pan_format,
    validate_ifsc_format,
    validate_phone_format
)
from addsol_vendor_onboarding.utils.email_utils import (
    send_supplier_credentials,
    send_validation_started_email,
    send_validation_success_email,
    send_validation_failure_email,
    send_approval_email,
    send_rejection_email,
)

PUBLIC_VALIDATION_FAILURE_MESSAGE = _(
    "We could not validate your submitted details at this time. "
    "Please review and resubmit, or contact support."
)


def _public_validation_failure_message(error_message):
    message = (error_message or "").lower()
    failed_sections = []

    if "gstn" in message:
        failed_sections.append(_("GSTN details"))
    if "pan" in message:
        failed_sections.append(_("PAN details"))
    if "bank" in message:
        failed_sections.append(_("Bank details"))

    if failed_sections:
        if len(failed_sections) == 1:
            section_text = failed_sections[0]
        elif len(failed_sections) == 2:
            section_text = _("{0} and {1}").format(failed_sections[0], failed_sections[1])
        else:
            section_text = _("{0}, {1} and {2}").format(
                failed_sections[0], failed_sections[1], failed_sections[2]
            )
        return _(
            "{0} could not be verified. Please review and resubmit, or contact support."
        ).format(section_text)

    return PUBLIC_VALIDATION_FAILURE_MESSAGE


def _assert_onboarding_manager():
    if not {"Purchase Manager", "System Manager", "DeVoltrans Management"} & set(frappe.get_roles()):
        frappe.throw(_("Not permitted"), frappe.PermissionError)


class SupplierOnboarding(Document):
    
    def validate(self):
        """Validate the document before saving."""
        self.validate_mandatory_fields()
        self.check_supplier_status()
    
    def validate_mandatory_fields(self):
        """Check if all mandatory fields are filled when data is submitted."""
        if self.onboarding_status == "Data Submitted":
            mandatory_fields = {
                "gstn": "GSTN",
                "pan": "PAN",
                "bank_account_no": "Bank Account Number",
                "bank_ifsc_code": "Bank IFSC Code",
                "phone_number": "Phone Number",
                "email": "Email"
            }
            
            for field, label in mandatory_fields.items():
                if not self.get(field):
                    frappe.throw(_("Please provide {0}").format(label))
    
    def check_supplier_status(self):
        """Ensure supplier is disabled until approved."""
        if self.supplier and self.onboarding_status != "Approved":
            supplier_doc = frappe.get_doc("Supplier", self.supplier)
            if not supplier_doc.disabled:
                supplier_doc.disabled = 1
                supplier_doc.save(ignore_permissions=True)
    
    def after_insert(self):
        """Send login credentials to supplier after creation."""
        if self.supplier and self.email:
            try:
                send_supplier_credentials(self)
                frappe.msgprint(_("Login credentials sent to supplier"))
            except frappe.exceptions.DuplicateEntryError:
                # User already exists, continue with onboarding
                frappe.clear_messages()
                frappe.msgprint(_("Supplier user already exists. Onboarding process continued."))
            except Exception as e:
                # Log error but don't fail the entire onboarding process
                frappe.log_error(
                    message=str(e),
                    title="Failed to send supplier credentials"
                )
                frappe.msgprint(_("Warning: Could not send login credentials, but onboarding process continues. Please check user setup manually."))
        elif self.supplier and not self.email:
            # Log warning for missing email
            frappe.log_error(
                message=f"Supplier {self.supplier} onboarding created but no email provided. Cannot send login credentials.",
                title="Missing Email for Supplier Onboarding"
            )
            frappe.msgprint(_("Warning: No email provided for supplier. Login credentials cannot be sent. Please update the email field."))
    
    def on_update(self):
        """Handle updates to the document."""
        # Trigger validation when data is submitted
        if (self.has_value_changed("onboarding_status") and 
            self.onboarding_status == "Data Submitted"):
            self.trigger_validation()
        
        # Send credentials if email is added and credentials haven't been sent yet
        if (self.has_value_changed("email") and self.email and self.supplier):
            try:
                send_supplier_credentials(self)
                frappe.msgprint(_("Login credentials sent to supplier"))
            except frappe.exceptions.DuplicateEntryError:
                frappe.clear_messages()
                frappe.msgprint(_("Supplier user already exists. Onboarding process continued."))
            except Exception as e:
                frappe.log_error(
                    message=str(e),
                    title="Failed to send supplier credentials"
                )
                frappe.msgprint(_("Warning: Could not send login credentials. Please check user setup manually."))
    
    def trigger_validation(self):
        """Trigger Cashfree API validation."""
        try:
            frappe.msgprint(_("Starting validation process..."))
            self.validation_status = "In Progress"
            # Clear stale failure remarks when re-validation starts.
            self.validation_remarks = None
            self.save(ignore_permissions=True)
            frappe.db.commit()

            try:
                send_validation_started_email(self)
            except Exception as email_error:
                frappe.log_error(
                    message=str(email_error),
                    title=f"Failed to send validation started email for {self.name}"
                )
            
            # Enqueue validation to run in background
            frappe.enqueue(
                method="addsol_vendor_onboarding.api.cashfree_api.validate_supplier_details",
                queue="default",
                timeout=300,
                is_async=True,
                **{"supplier_onboarding": self.name}
            )
            
            frappe.msgprint(_(
                "Validation process started. You will receive an email notification once completed."
            ))
            
        except Exception as e:
            frappe.log_error(
                message=str(e),
                title="Validation Trigger Failed"
            )
            frappe.throw(_("Failed to trigger validation: {0}").format(str(e)))
    
    def on_validation_success(self):
        """Called when validation is successful."""
        self.validation_status = "Validated"
        self.onboarding_status = "Validation Successful"
        self.validation_date = frappe.utils.now()
        self.validation_remarks = None
        
        # Get Purchase Manager for notification
        if not self.purchase_manager:
            self.purchase_manager = frappe.db.get_single_value(
                "Buying Settings",
                "purchase_manager"
            )
        
        self.save(ignore_permissions=True)
        
        # Send email notifications without affecting validation result state.
        try:
            send_validation_success_email(self)
        except Exception as e:
            frappe.log_error(
                message=str(e),
                title=f"Failed to send validation success email for {self.name}"
            )
    
    def on_validation_failure(self, error_message):
        """Called when validation fails."""
        self.validation_status = "Failed"
        self.onboarding_status = "Validation Failed"
        # Keep vendor-facing remarks generic. Detailed errors remain in validation logs.
        self.validation_remarks = _public_validation_failure_message(error_message)
        self.save(ignore_permissions=True)
        
        # Send email notifications without affecting failed-state persistence.
        try:
            send_validation_failure_email(self, error_message)
        except Exception as e:
            frappe.log_error(
                message=str(e),
                title=f"Failed to send validation failure email for {self.name}"
            )
    
    def approve_supplier(self):
        """Approve the supplier and enable them."""
        if self.onboarding_status != "Validation Successful":
            frappe.throw(_("Supplier can only be approved after successful validation"))
        
        # Enable supplier
        if self.supplier:
            supplier_doc = frappe.get_doc("Supplier", self.supplier)
            supplier_doc.disabled = 0
            
            # Update supplier with validated data
            if self.gstn:
                supplier_doc.gstin = self.gstn
            if self.pan:
                supplier_doc.pan = self.pan
            
            supplier_doc.save(ignore_permissions=True)
        
        # Lock the onboarding record
        self.onboarding_status = "Approved"
        self.approved_by = frappe.session.user
        self.approved_date = frappe.utils.now()
        self.save(ignore_permissions=True)
        
        # Send approval email
        send_approval_email(self)
        
        frappe.msgprint(_("Supplier {0} has been approved").format(self.supplier))
    
    def reject_supplier(self, reason):
        """Reject the supplier onboarding."""
        self.onboarding_status = "Rejected"
        self.rejection_reason = reason
        self.save(ignore_permissions=True)
        
        # Send rejection email
        send_rejection_email(self, reason)
        
        frappe.msgprint(_("Supplier {0} has been rejected").format(self.supplier))
    
    def initiate_reverification(self, reason):
        """Re-initiate the onboarding process for changes."""
        if self.onboarding_status != "Approved":
            frappe.throw(_("Only approved suppliers can be re-verified"))
        
        self.re_verification_reason = reason
        self.onboarding_status = "Pending Submission"
        self.validation_status = "Not Validated"
        self.gstn_validated = 0
        self.pan_validated = 0
        self.bank_validated = 0
        
        # Disable supplier until re-verification
        if self.supplier:
            supplier_doc = frappe.get_doc("Supplier", self.supplier)
            supplier_doc.disabled = 1
            supplier_doc.save(ignore_permissions=True)
        
        self.save(ignore_permissions=True)
        
        frappe.msgprint(_(
            "Re-verification process initiated. Supplier will need to update their information."
        ))
    
    def before_cancel(self):
        """Prevent cancellation if there are restrictions."""
        frappe.throw(_("Supplier Onboarding cannot be cancelled directly"))
    
    @frappe.whitelist()
    def get_attached_documents(self):
        """Get list of attached documents."""
        from frappe.desk.form.load import get_attachments
        return get_attachments("Supplier Onboarding", self.name)


# Whitelisted methods for API access

@frappe.whitelist()
def submit_supplier_data(supplier_onboarding, data):
    """
    API method for suppliers to submit their data via portal.
    
    Args:
        supplier_onboarding: Name of Supplier Onboarding document
        data: Dictionary containing supplier data
    """
    try:
        if isinstance(data, str):
            data = frappe.parse_json(data)

        doc = frappe.get_doc("Supplier Onboarding", supplier_onboarding)
        
        # Check permissions
        if frappe.session.user != doc.email and not frappe.has_permission(doc=doc, ptype="write", user=frappe.session.user):
            frappe.throw(_("Not authorized to update this record"))
        
        # Validate data format before submission
        validation_errors = []
        
        # Validate GSTN
        if data.get('gstn'):
            is_valid, error = validate_gstn_format(data['gstn'])
            if not is_valid:
                validation_errors.append(f"GSTN: {error}")
        
        # Validate PAN
        if data.get('pan'):
            is_valid, error = validate_pan_format(data['pan'])
            if not is_valid:
                validation_errors.append(f"PAN: {error}")
        
        # Validate IFSC
        if data.get('bank_ifsc_code'):
            is_valid, error = validate_ifsc_format(data['bank_ifsc_code'])
            if not is_valid:
                validation_errors.append(f"IFSC: {error}")
        
        # Validate Phone Number
        if data.get('phone_number'):
            is_valid, error = validate_phone_format(data['phone_number'])
            if not is_valid:
                validation_errors.append(f"Phone Number: {error}")
        
        # If validation errors exist, return them
        if validation_errors:
            return {
                "success": False,
                "message": _("Validation failed. Please correct the following errors: {0}").format("; ".join(validation_errors)),
                "errors": validation_errors
            }
        
        # Update fields
        for field in ["gstn", "pan", "bank_account_no", "bank_ifsc_code", 
                      "udyog_aadhaar", "phone_number", "email"]:
            if field in data:
                doc.set(field, data.get(field))
        
        doc.onboarding_status = "Data Submitted"
        doc.save(ignore_permissions=True)
        
        return {
            "success": True,
            "message": "Data submitted successfully. Validation in progress."
        }
        
    except Exception as e:
        frappe.log_error(message=str(e), title="Supplier Data Submission Failed")
        return {
            "success": False,
            "message": _("Unable to submit supplier data. Please try again later.")
        }


@frappe.whitelist()
def send_credentials_manually(supplier_onboarding):
    """Manually send login credentials to supplier."""
    try:
        _assert_onboarding_manager()
        doc = frappe.get_doc("Supplier Onboarding", supplier_onboarding)
        if not doc.email:
            return {"success": False, "message": "No email provided for supplier"}
        
        send_supplier_credentials(doc)
        return {"success": True, "message": "Login credentials sent successfully"}
    except Exception as e:
        frappe.log_error(f"Failed to send credentials manually: {str(e)}", "Manual Credential Send Error")
        return {"success": False, "message": _("Failed to send credentials. Please check error logs.")}


@frappe.whitelist()
def approve_supplier_onboarding(supplier_onboarding):
    """Approve supplier onboarding."""
    _assert_onboarding_manager()
    doc = frappe.get_doc("Supplier Onboarding", supplier_onboarding)
    doc.approve_supplier()
    return {"success": True, "message": "Supplier approved successfully"}


@frappe.whitelist()
def reject_supplier_onboarding(supplier_onboarding, reason):
    """Reject supplier onboarding."""
    _assert_onboarding_manager()
    doc = frappe.get_doc("Supplier Onboarding", supplier_onboarding)
    doc.reject_supplier(reason)
    return {"success": True, "message": "Supplier rejected"}


@frappe.whitelist()
def reinitiate_verification(supplier_onboarding, reason):
    """Re-initiate verification for approved supplier."""
    _assert_onboarding_manager()
    doc = frappe.get_doc("Supplier Onboarding", supplier_onboarding)
    doc.initiate_reverification(reason)
    return {"success": True, "message": "Re-verification initiated"}


@frappe.whitelist()
def get_timeline_data(doctype, name):
    """
    Get timeline data for Supplier.
    This will show onboarding history in Supplier timeline.
    """
    if not frappe.has_permission("Supplier", "read", name):
        return []

    timeline_data = []
    records = frappe.get_list(
        "Supplier Onboarding",
        filters={"supplier": name},
        fields=["creation", "name", "onboarding_status", "validation_status"],
        order_by="creation desc",
        limit_page_length=20,
    )

    for record in records:
        timeline_data.append(
            {
                "creation": record.creation,
                "icon": "solid small-file",
                "content": _(
                    "Supplier Onboarding {0}: {1} (Validation: {2})"
                ).format(
                    frappe.bold(record.name),
                    frappe.bold(record.onboarding_status or _("Unknown")),
                    frappe.bold(record.validation_status or _("Unknown")),
                ),
            }
        )

    return timeline_data
