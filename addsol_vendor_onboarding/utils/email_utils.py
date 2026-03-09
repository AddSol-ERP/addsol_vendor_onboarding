# ============================================================================
# EMAIL UTILITIES
# File: utils/email_utils.py
# ============================================================================

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import get_url


def get_company_name():
    """Get the company name from ERPNext system settings."""
    try:
        company_name = frappe.db.get_single_value("Global Defaults", "default_company")
        # if no company_name is found use user default value
        if not company_name:
            company_name = frappe.defaults.get_user_default("Company")
        return company_name or _("Your Company")
    except:
        return _("Your Company")


def get_purchase_team_name():
    """Get the purchase team name with company fallback."""
    return _("{0} Purchase Team").format(get_company_name())


def get_system_name():
    """Get the system name with company fallback."""
    return _("{0} ERP System").format(get_company_name())

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
    
    # Create or get supplier user. For new users, include password setup link
    # in the same credentials email to avoid duplicate emails.
    _user, _is_new_user, reset_link = get_or_create_supplier_user(
        supplier_onboarding.email,
        supplier_onboarding.supplier_name
    )
    
    # Generate supplier portal URLs
    portal_url = get_url() + "/vendor-portal"
    onboarding_url = _get_portal_onboarding_url(supplier_onboarding.name)
    
    # Email subject and message
    subject = _("Supplier Onboarding - Login Credentials")
    
    if reset_link:
        password_line = _(
            '<li><strong>Set Password:</strong> <a href="{0}">Click here</a></li>'
        ).format(reset_link)
    else:
        password_line = _(
            '<li><strong>Password:</strong> Use <a href="{0}">Forgot Password</a> if needed</li>'
        ).format(f"{get_url()}/login")

    message = """
    <p>Dear {0},</p>

    <p>Welcome to the {6} Supplier Onboarding Portal.</p>

    <p><strong>Application ID:</strong> {3}</p>
    <p><strong>Username:</strong> {2}</p>

    <p><strong>Please complete the following steps:</strong></p>
    <ol>
        <li><strong>Set your password</strong><br>{4}</li>
        <li><strong>Login to supplier portal</strong><br><a href="{1}">{1}</a></li>
        <li><strong>Complete onboarding form</strong><br><a href="{5}">{5}</a></li>
    </ol>

    <p><strong>Mandatory details to submit:</strong></p>
    <ul>
        <li>GSTN (15 characters)</li>
        <li>PAN (10 characters)</li>
        <li>Bank Account Number</li>
        <li>Bank IFSC Code (11 characters)</li>
        <li>Phone Number (10 digits)</li>
    </ul>
    <p><strong>Optional details:</strong> CIN/LLPIN, Udyam Registration Number.</p>

    <p><strong>Required documents:</strong> GSTN Certificate, PAN Card, Bank Document.</p>
    <p><strong>Optional documents:</strong> Udyam Registration Certificate.</p>
    <p><strong>Important:</strong> This is a web portal. Desk/app access is not required.</p>

    <p>Best regards,<br>
    {7}</p>""".format(
        supplier_onboarding.supplier_name,
        portal_url,
        supplier_onboarding.email,
        supplier_onboarding.name,
        password_line,
        onboarding_url,
        get_company_name(),
        get_purchase_team_name()
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
    {0}</p>""".format(
        supplier_onboarding.supplier_name,
        _public_validation_failure_message(error_message),
        _get_portal_onboarding_url(supplier_onboarding.name),
        get_purchase_team_name()
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
        {0}</p>""".format(
            supplier_onboarding.supplier_name,
            error_message,
            _get_desk_onboarding_url(supplier_onboarding.name),
            get_system_name()
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
    {1}</p>""".format(supplier_onboarding.supplier_name, get_purchase_team_name())
    
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
                <li>CIN / LLPIN: {3}</li>
                <li>Bank Account: {4}</li>
                <li>Udyam Registration: {5}</li>
            </ul>
        </div>
        
        <p>Please review the supplier documents and details, then approve or reject the onboarding request.</p>
        
        <p>Review Now: <a href="{6}">Click here</a></p>
        
        <p>Best regards,<br>
        {0}</p>""".format(
            supplier_onboarding.supplier_name,
            '✓ Validated' if supplier_onboarding.gstn_validated else '✗ Not Validated',
            '✓ Validated' if supplier_onboarding.pan_validated else ('Not Provided' if not supplier_onboarding.pan else '✗ Not Validated'),
            '✓ Validated' if getattr(supplier_onboarding, "cin_validated", 0) else ('Not Provided' if not getattr(supplier_onboarding, "cin", None) else '✗ Not Validated'),
            '✓ Validated' if supplier_onboarding.bank_validated else '✗ Not Validated',
            '✓ Validated' if supplier_onboarding.udyam_validated else '✗ Not Validated',
            _get_desk_onboarding_url(supplier_onboarding.name),
            get_system_name()
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
    {0}</p>""".format(
        supplier_onboarding.supplier_name,
        _get_portal_onboarding_url(supplier_onboarding.name),
        get_purchase_team_name()
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
    
    <p>Thank you for partnering with {3}!</p>
    
    <p>Best regards,<br>
    {4}</p>""".format(
        supplier_onboarding.supplier_name,
        supplier_onboarding.approved_by,
        frappe.utils.format_datetime(supplier_onboarding.approved_date),
        get_company_name(),
        get_purchase_team_name()
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
    {2}</p>""".format(supplier_onboarding.supplier_name, reason, get_purchase_team_name())
    
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
        tuple: (user_doc, is_new_user, reset_link_or_none)
    """
    # Check if user already exists
    if frappe.db.exists("User", email):
        user = frappe.get_doc("User", email)
        # Ensure user has Supplier role
        user_roles = {d.role for d in user.get("roles", [])}
        if "Supplier" not in user_roles:
            user.append("roles", {"role": "Supplier"})
            user.save(ignore_permissions=True)
        return user, False, None
    
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
        
        # Generate a valid reset URL and include it in onboarding credential email.
        reset_link = user.reset_password(send_email=False)
        return user, True, reset_link
        
    except frappe.exceptions.DuplicateEntryError:
        # User was created by another process, get existing user
        user = frappe.get_doc("User", email)
        user_roles = {d.role for d in user.get("roles", [])}
        if "Supplier" not in user_roles:
            user.append("roles", {"role": "Supplier"})
            user.save(ignore_permissions=True)
        return user, False, None
    except Exception as e:
        frappe.log_error(
            message=f"Failed to create user for {email}: {str(e)}",
            title="User Creation Failed"
        )
        raise
