# ============================================================================
# EMAIL UTILITIES
# File: utils/email_utils.py
# ============================================================================

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import get_url

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


def _get_portal_onboarding_url(onboarding_name):
    return f"{get_url()}/vendor-onboarding-form?id={onboarding_name}"


def _get_desk_onboarding_url(onboarding_name):
    return f"{get_url()}/app/supplier-onboarding/{onboarding_name}"


def send_supplier_credentials(supplier_onboarding):
    """
    Send login credentials to supplier.
    
    Args:
        supplier_onboarding: Supplier Onboarding document
    """
    if not supplier_onboarding.email:
        return
    
    # Create or get supplier user
    get_or_create_supplier_user(
        supplier_onboarding.email,
        supplier_onboarding.supplier_name
    )
    
    # Generate PORTAL URL (not desk URL)
    portal_url = get_url() + "/vendor-portal"
    
    # Email subject and message
    subject = _("Supplier Onboarding - Login Credentials")
    
    message = """
    <p>Dear {0},</p>
    
    <p>Welcome to DeVoltrans Vendor Onboarding Portal!</p>
    
    <p>Your supplier account has been created. Please use the following credentials to login:</p>
    
    <ul>
        <li><strong>Portal URL:</strong> <a href="{1}">{1}</a></li>
        <li><strong>Username:</strong> {2}</li>
        <li><strong>Password:</strong> You will receive a password reset email separately</li>
    </ul>
    
    <p><strong>Important:</strong> This is a web portal. You do NOT need desk/app access.</p>
    
    <p>Please login and submit the following mandatory details:</p>
    <ul>
        <li>GSTN (15 characters)</li>
        <li>PAN (10 characters)</li>
        <li>Bank Account Number</li>
        <li>Bank IFSC Code (11 characters)</li>
        <li>Udyog Aadhaar</li>
        <li>Phone Number (10 digits)</li>
    </ul>
    
    <p>You will also need to upload supporting documents for verification.</p>
    
    <p><strong>Application ID:</strong> {3}</p>
    
    <p>Best regards,<br>
    DeVoltrans Purchase Team</p>
    """.format(
        supplier_onboarding.supplier_name,
        portal_url,
        supplier_onboarding.email,
        supplier_onboarding.name
    )
    
    frappe.sendmail(
        recipients=[supplier_onboarding.email],
        subject=subject,
        message=message
    )


def send_validation_failure_email(supplier_onboarding, error_message):
    """
    Send email notification when validation fails.
    
    Args:
        supplier_onboarding: Supplier Onboarding document
        error_message: Validation error message
    """
    # Email to supplier
    supplier_subject = _("Supplier Onboarding - Validation Failed")
    supplier_message = """
    <p>Dear {0},</p>
    
    <p>Your submitted information could not be validated.</p>
    
    <div style="background-color: #f8d7da; padding: 10px; border-left: 4px solid #f5c6cb;">
        {1}
    </div>
    
    <p>Please review and update your information, then resubmit.</p>
    
    <p>Login URL: <a href="{2}">Click here</a></p>
    
    <p>Best regards,<br>
    DeVoltrans Purchase Team</p>
    """.format(
        supplier_onboarding.supplier_name,
        _public_validation_failure_message(error_message),
        _get_portal_onboarding_url(supplier_onboarding.name)
    )
    
    frappe.sendmail(
        recipients=[supplier_onboarding.email],
        subject=supplier_subject,
        message=supplier_message
    )
    
    # Email to Purchase Manager
    if supplier_onboarding.purchase_manager:
        pm_subject = _("Supplier Validation Failed - {0}").format(
            supplier_onboarding.supplier_name
        )
        pm_message = """
        <p>Dear Purchase Manager,</p>
        
        <p>Validation failed for supplier <strong>{0}</strong></p>
        
        <p><strong>Failure Reasons:</strong></p>
        <div style="background-color: #f8d7da; padding: 10px; border-left: 4px solid #f5c6cb;">
            {1}
        </div>
        
        <p>View Details: <a href="{2}">Click here</a></p>
        
        <p>Best regards,<br>
        DeVoltrans ERP System</p>
        """.format(
            supplier_onboarding.supplier_name,
            error_message,
            _get_desk_onboarding_url(supplier_onboarding.name)
        )
        
        frappe.sendmail(
            recipients=[supplier_onboarding.purchase_manager],
            subject=pm_subject,
            message=pm_message
        )


def send_validation_success_email(supplier_onboarding):
    """
    Send email notification when validation succeeds.
    
    Args:
        supplier_onboarding: Supplier Onboarding document
    """
    # Email to supplier
    supplier_subject = _("Supplier Onboarding - Validation Successful")
    supplier_message = """
    <p>Dear {0},</p>
    
    <p>Great news! Your submitted information has been successfully validated.</p>
    
    <div style="background-color: #d4edda; padding: 10px; border-left: 4px solid #c3e6cb;">
        ✓ All your details have been verified successfully!
    </div>
    
    <p>Your application is now pending review and approval by our Purchase Manager.</p>
    
    <p>You will receive another email once your application has been reviewed.</p>
    
    <p>Best regards,<br>
    DeVoltrans Purchase Team</p>
    """.format(supplier_onboarding.supplier_name)
    
    frappe.sendmail(
        recipients=[supplier_onboarding.email],
        subject=supplier_subject,
        message=supplier_message
    )
    
    # Email to Purchase Manager
    if supplier_onboarding.purchase_manager:
        pm_subject = _("Supplier Ready for Review - {0}").format(
            supplier_onboarding.supplier_name
        )
        pm_message = """
        <p>Dear Purchase Manager,</p>
        
        <p>Supplier <strong>{0}</strong> has been successfully validated and is ready for your review.</p>
        
        <div style="background-color: #d4edda; padding: 10px; border-left: 4px solid #c3e6cb;">
            <strong>Validation Status:</strong>
            <ul>
                <li>GSTN: {1}</li>
                <li>PAN: {2}</li>
                <li>Bank Account: {3}</li>
            </ul>
        </div>
        
        <p>Please review the supplier documents and details, then approve or reject the onboarding request.</p>
        
        <p>Review Now: <a href="{4}">Click here</a></p>
        
        <p>Best regards,<br>
        DeVoltrans ERP System</p>
        """.format(
            supplier_onboarding.supplier_name,
            '✓ Validated' if supplier_onboarding.gstn_validated else '✗ Not Validated',
            '✓ Validated' if supplier_onboarding.pan_validated else '✗ Not Validated',
            '✓ Validated' if supplier_onboarding.bank_validated else '✗ Not Validated',
            _get_desk_onboarding_url(supplier_onboarding.name)
        )
        
        frappe.sendmail(
            recipients=[supplier_onboarding.purchase_manager],
            subject=pm_subject,
            message=pm_message
        )


def send_validation_started_email(supplier_onboarding):
    """
    Send email notification when validation has started.

    Args:
        supplier_onboarding: Supplier Onboarding document
    """
    if not supplier_onboarding.email:
        return

    supplier_subject = _("Supplier Onboarding - Verification In Progress")
    supplier_message = """
    <p>Dear {0},</p>

    <p>Your details have been submitted successfully.</p>

    <div style="background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffeeba;">
        <strong>Verification Step 1:</strong> Completed<br>
        <strong>Verification Step 2:</strong> In Progress (details verification)<br>
        <strong>Verification Step 3:</strong> Pending (purchase team review)
    </div>

    <p>You will receive another update once verification is complete.</p>

    <p>Track status: <a href="{1}">Click here</a></p>

    <p>Best regards,<br>
    DeVoltrans Purchase Team</p>
    """.format(
        supplier_onboarding.supplier_name,
        _get_portal_onboarding_url(supplier_onboarding.name),
    )

    frappe.sendmail(
        recipients=[supplier_onboarding.email],
        subject=supplier_subject,
        message=supplier_message
    )


def send_approval_email(supplier_onboarding):
    """
    Send email notification when supplier is approved.
    
    Args:
        supplier_onboarding: Supplier Onboarding document
    """
    subject = _("Supplier Onboarding - Approved")
    message = """
    <p>Dear {0},</p>
    
    <p>Congratulations! Your supplier onboarding application has been approved.</p>
    
    <div style="background-color: #d4edda; padding: 10px; border-left: 4px solid #c3e6cb;">
        ✓ Your supplier account is now active!
    </div>
    
    <p>You can now participate in our procurement processes and receive purchase orders.</p>
    
    <p><strong>Approved By:</strong> {1}</p>
    <p><strong>Approved Date:</strong> {2}</p>
    
    <p>Thank you for partnering with DeVoltrans!</p>
    
    <p>Best regards,<br>
    DeVoltrans Purchase Team</p>
    """.format(
        supplier_onboarding.supplier_name,
        supplier_onboarding.approved_by,
        frappe.utils.format_datetime(supplier_onboarding.approved_date)
    )
    
    frappe.sendmail(
        recipients=[supplier_onboarding.email],
        subject=subject,
        message=message
    )


def send_rejection_email(supplier_onboarding, reason):
    """
    Send email notification when supplier is rejected.
    
    Args:
        supplier_onboarding: Supplier Onboarding document
        reason: Rejection reason
    """
    subject = _("Supplier Onboarding - Rejected")
    message = """
    <p>Dear {0},</p>
    
    <p>We regret to inform you that your supplier onboarding application has been rejected.</p>
    
    <div style="background-color: #f8d7da; padding: 10px; border-left: 4px solid #f5c6cb;">
        <strong>Rejection Reason:</strong><br>
        {1}
    </div>
    
    <p>If you have any questions, please contact our Purchase team.</p>
    
    <p>Best regards,<br>
    DeVoltrans Purchase Team</p>
    """.format(supplier_onboarding.supplier_name, reason)
    
    frappe.sendmail(
        recipients=[supplier_onboarding.email],
        subject=subject,
        message=message
    )


def get_or_create_supplier_user(email, full_name):
    """
    Get or create a user for the supplier.
    
    Args:
        email: Supplier email
        full_name: Supplier name
    
    Returns:
        User document
    """
    # Check if user already exists
    if frappe.db.exists("User", email):
        user = frappe.get_doc("User", email)
        # Ensure user has Supplier role
        user_roles = {d.role for d in user.get("roles", [])}
        if "Supplier" not in user_roles:
            user.append("roles", {"role": "Supplier"})
            user.save(ignore_permissions=True)
        return user
    
    # Create new user
    try:
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": full_name,
            "enabled": 1,
            "send_welcome_email": 0,  # We'll send our own custom email
            "user_type": "Website User",
            "roles": [{"role": "Supplier"}]
        })
        user.insert(ignore_permissions=True)
        
        # Send password reset email instead of welcome email
        # This is more reliable than reset_password() in ERPNext 15
        try:
            frappe.sendmail(
                recipients=[email],
                subject=_("Set Your Password - DeVoltrans Supplier Portal"),
                template="password_reset",
                args={
                    "user": user,
                    "reset_link": user.reset_password(send_email=False)
                },
                header=_("Set Your Password")
            )
            frappe.msgprint(_("Password reset email sent to {0}").format(email))
        except Exception as email_error:
            frappe.log_error(
                message=f"Failed to send password reset email to {email}: {str(email_error)}",
                title="Password Reset Email Failed"
            )
            frappe.msgprint(_("Warning: User created but password reset email could not be sent. Please contact support."))
        
        return user
        
    except frappe.exceptions.DuplicateEntryError:
        # User was created by another process, get existing user
        user = frappe.get_doc("User", email)
        user_roles = {d.role for d in user.get("roles", [])}
        if "Supplier" not in user_roles:
            user.append("roles", {"role": "Supplier"})
            user.save(ignore_permissions=True)
        return user
    except Exception as e:
        frappe.log_error(
            message=f"Failed to create user for {email}: {str(e)}",
            title="User Creation Failed"
        )
        raise
