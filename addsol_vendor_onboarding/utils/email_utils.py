# ============================================================================
# EMAIL UTILITIES
# File: utils/email_utils.py
# ============================================================================

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import get_url

from addsol_vendor_onboarding.utils.validation_utils import PUBLIC_VALIDATION_REVIEW_MESSAGE


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
    from addsol_vendor_onboarding.api.private_onboarding import issue_invitation
    return issue_invitation(frappe.get_doc("Supplier Onboarding", onboarding_name))


def _get_desk_onboarding_url(onboarding_name):
    return f"{get_url()}/app/supplier-onboarding/{onboarding_name}"


def send_supplier_credentials(supplier_onboarding):
    """
    Send a private onboarding invitation without creating a user.
    
    Args:
        supplier_onboarding: Supplier Onboarding document
    """
    if not supplier_onboarding.email:
        return
    
    from html import escape
    from addsol_vendor_onboarding.api.private_onboarding import issue_invitation

    url = issue_invitation(supplier_onboarding)
    frappe.sendmail(
        recipients=[supplier_onboarding.email],
        subject=_("Supplier Onboarding - Private Invitation"),
        message=(
            f"<p>Dear {escape(supplier_onboarding.supplier_name or '')},</p>"
            f'<p><a href="{escape(url, quote=True)}">Complete your onboarding details</a></p>'
            "<p>No account or login is required. This private link expires in 7 days "
            "and can be submitted once. Please do not forward it.</p>"
        ),
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
    
    <p>Private submission link: <a href="{2}">Click here</a></p>
    
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


def send_validation_review_email(supplier_onboarding, mismatch_details=None):
    """
    Notify the Purchase Manager that provider-valid identifiers carry name
    mismatches and the record awaits review.

    Only the Purchase Manager is notified: vendor-facing remarks stay generic
    and the detailed comparison lives on the onboarding record itself.

    Args:
        supplier_onboarding: Supplier Onboarding document
        mismatch_details: List of detailed mismatch messages (internal use)
    """
    if not supplier_onboarding.purchase_manager:
        return

    from html import escape

    mismatch_items = "".join(
        f"<li>{escape(str(item))}</li>"
        for item in (mismatch_details or [])
    ) or f"<li>{escape(PUBLIC_VALIDATION_REVIEW_MESSAGE)}</li>"

    pm_subject = _("Supplier Validation Review Required - {0}").format(
        supplier_onboarding.supplier_name
    )
    pm_message = """
    <p>Dear Purchase Manager,</p>

    <p>All identifiers for supplier <strong>{}</strong> passed provider
    validation, but at least one registered name does not match the name
    entered on the onboarding record.</p>

    <div style="background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffeeba;">
        <strong>Name mismatches to review:</strong>
        <ul>
            {}
        </ul>
    </div>

    <p>Open the onboarding record to compare the entered details against the
    registered names shown in the Registered Name Verification section, then
    approve or reject the record.</p>

    <p>Review Now: <a href="{}">Click here</a></p>

    <p>Best regards,<br>
    {}</p>""".format(
        escape(supplier_onboarding.supplier_name or ""),
        mismatch_items,
        _get_desk_onboarding_url(supplier_onboarding.name),
        get_system_name(),
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


    <p>Best regards,<br>
    {1}</p>""".format(
        supplier_onboarding.supplier_name,
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
    from html import escape
    url = _get_portal_onboarding_url(supplier_onboarding.name)
    subject = _("Supplier Onboarding - Rejected")
    message = """
    <p>Dear {0},</p>
    
    <p>We regret to inform you that your supplier onboarding application has been rejected.</p>
    
    <div style="background-color: #f8d7da; padding: 10px; border-left: 4px solid #f5c6cb;">
        <strong>Rejection Reason:</strong><br>
        {1}
    </div>
    
    <p>Please correct your details and resubmit using this new private link:</p>
    <p><a href="{3}">Update onboarding details</a> (expires in 7 days)</p>
    
    <p>Best regards,<br>
    {2}</p>""".format(escape(supplier_onboarding.supplier_name or ""), escape(reason or ""), get_purchase_team_name(), escape(url, quote=True))
    
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
