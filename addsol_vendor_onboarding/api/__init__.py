import frappe
import re
from frappe import _
from addsol_vendor_onboarding.utils.validation_utils import (
    validate_gstn_format,
    validate_pan_format,
    validate_cin_format,
    validate_ifsc_format,
    validate_phone_format,
)


REQUIRED_UPLOAD_FIELDS = ("gstn_certificate", "pan_card", "bank_cheque")
ALL_UPLOAD_FIELDS = REQUIRED_UPLOAD_FIELDS + (
    "udyog_aadhaar_certificate",
    "cin_certificate",
    "company_logo",
)
VENDOR_EDITABLE_ONBOARDING_STATUSES = ("Pending Submission", "Validation Failed", "Rejected")
PUBLIC_VALIDATION_FAILURE_MESSAGE = _(
    "We could not validate your submitted details at this time. "
    "Please review and resubmit, or contact support."
)


def _has_attachment(docname, fieldname):
    return bool(
        frappe.db.exists(
            "File",
            {
                "attached_to_doctype": "Supplier Onboarding",
                "attached_to_name": docname,
                "attached_to_field": fieldname,
                "is_folder": 0,
            },
        )
    )


def _validate_supplier_payload(data):
    validation_errors = []

    if data.get("gstn"):
        ok, error = validate_gstn_format(data["gstn"])
        if not ok:
            validation_errors.append(f"GSTN: {error}")

    if data.get("pan"):
        ok, error = validate_pan_format(data["pan"])
        if not ok:
            validation_errors.append(f"PAN: {error}")

    if data.get("cin"):
        ok, error = validate_cin_format(data["cin"])
        if not ok:
            validation_errors.append(f"CIN: {error}")

    if data.get("bank_ifsc_code"):
        ok, error = validate_ifsc_format(data["bank_ifsc_code"])
        if not ok:
            validation_errors.append(f"IFSC: {error}")

    if data.get("phone_number"):
        ok, error = validate_phone_format(data["phone_number"])
        if not ok:
            validation_errors.append(f"Phone Number: {error}")

    if data.get("udyog_aadhaar"):
        udyam_alnum = re.sub(r"[^A-Z0-9]", "", str(data.get("udyog_aadhaar")).upper())
        if not re.fullmatch(r"UDYAM[A-Z]{2}\d{2}\d{7}", udyam_alnum):
            validation_errors.append(
                "Udyam: Please enter Udyam Registration Number in format UDYAM-XX-00-0000000"
            )

    return validation_errors


def _normalize_supplier_payload(data):
    normalized = dict(data or {})

    for field in ("gstn", "pan", "cin", "bank_ifsc_code"):
        value = normalized.get(field)
        if isinstance(value, str):
            normalized[field] = value.strip().replace(" ", "").upper()

    account_number = normalized.get("bank_account_no")
    if isinstance(account_number, str):
        normalized["bank_account_no"] = account_number.strip().replace(" ", "")

    phone_number = normalized.get("phone_number")
    if isinstance(phone_number, str):
        digits = re.sub(r"\D", "", phone_number)
        # Accept +91XXXXXXXXXX / 91XXXXXXXXXX inputs
        if len(digits) == 12 and digits.startswith("91"):
            digits = digits[-10:]
        normalized["phone_number"] = digits

    for field in ("udyog_aadhaar",):
        value = normalized.get(field)
        if isinstance(value, str):
            normalized[field] = value.strip()

    return normalized


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


def _prepare_onboarding_for_resubmission(doc):
    doc.onboarding_status = "Data Submitted"
    doc.validation_status = "Not Validated"
    doc.gstn_validated = 0
    doc.pan_validated = 0
    doc.cin_validated = 0
    doc.bank_validated = 0
    doc.udyam_validated = 0
    doc.validation_date = None
    doc.validation_remarks = None


def _get_existing_required_files(docname):
    return {field: _has_attachment(docname, field) for field in REQUIRED_UPLOAD_FIELDS}


def _deduplicate_attachments(docname, fields=None):
    fields = tuple(fields or ALL_UPLOAD_FIELDS)
    if not fields:
        return

    files = frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": "Supplier Onboarding",
            "attached_to_name": docname,
            "attached_to_field": ["in", list(fields)],
            "is_folder": 0,
        },
        fields=["name", "attached_to_field", "modified", "creation"],
        order_by="attached_to_field asc, modified desc, creation desc",
    )

    seen = set()
    for file_doc in files:
        fieldname = file_doc.attached_to_field
        if fieldname in seen:
            try:
                frappe.delete_doc("File", file_doc.name, ignore_permissions=True)
            except Exception:
                frappe.log_error(
                    message=f"Failed to remove duplicate attachment {file_doc.name} for {docname}",
                    title="Attachment Deduplication Error",
                )
        else:
            seen.add(fieldname)


def _deduplicate_all_onboarding_attachments():
    onboarding_names = frappe.get_all("Supplier Onboarding", pluck="name")
    total_docs = 0
    touched_docs = 0
    removed_files = 0

    for docname in onboarding_names:
        total_docs += 1
        files = frappe.get_all(
            "File",
            filters={
                "attached_to_doctype": "Supplier Onboarding",
                "attached_to_name": docname,
                "attached_to_field": ["in", list(ALL_UPLOAD_FIELDS)],
                "is_folder": 0,
            },
            fields=["name", "attached_to_field", "modified", "creation"],
            order_by="attached_to_field asc, modified desc, creation desc",
        )

        seen = set()
        removed_for_doc = 0
        for file_doc in files:
            fieldname = file_doc.attached_to_field
            if fieldname in seen:
                try:
                    frappe.delete_doc("File", file_doc.name, ignore_permissions=True)
                    removed_files += 1
                    removed_for_doc += 1
                except Exception:
                    frappe.log_error(
                        message=f"Failed to remove duplicate attachment {file_doc.name} for {docname}",
                        title="Attachment Deduplication Error",
                    )
            else:
                seen.add(fieldname)

        if removed_for_doc:
            touched_docs += 1

    return {
        "total_docs": total_docs,
        "touched_docs": touched_docs,
        "removed_files": removed_files,
    }


@frappe.whitelist()
def cleanup_supplier_onboarding_attachments():
    """One-time cleanup: remove duplicate onboarding attachments per attachment field."""
    frappe.only_for("System Manager")
    result = _deduplicate_all_onboarding_attachments()
    frappe.db.commit()
    return {
        "success": True,
        "message": _(
            "Cleanup complete. Processed {0} records, cleaned {1} records, removed {2} duplicate files."
        ).format(result["total_docs"], result["touched_docs"], result["removed_files"]),
        "result": result,
    }


def _build_reconcile_failure_message(failed_sections):
    section_labels = []
    for section in failed_sections:
        if section == "GSTN":
            section_labels.append(_("GSTN details"))
        elif section == "PAN":
            section_labels.append(_("PAN details"))
        elif section == "CIN":
            section_labels.append(_("CIN details"))
        elif section == "Bank Account":
            section_labels.append(_("Bank details"))
        elif section == "Udyog Aadhaar":
            section_labels.append(_("Udyam details"))

    if not section_labels:
        return PUBLIC_VALIDATION_FAILURE_MESSAGE

    if len(section_labels) == 1:
        section_text = section_labels[0]
    elif len(section_labels) == 2:
        section_text = _("{0} and {1}").format(section_labels[0], section_labels[1])
    else:
        section_text = _("{0}, and {1}").format(", ".join(section_labels[:-1]), section_labels[-1])

    return _(
        "{0} could not be verified. Please review and resubmit, or contact support."
    ).format(section_text)


def _latest_validation_log_statuses(onboarding_name):
    logs = frappe.get_all(
        "Supplier Validation Log",
        filters={
            "supplier_onboarding": onboarding_name,
            "validation_type": ["in", ["GSTN", "PAN", "CIN", "Bank Account", "Udyog Aadhaar", "Udyam"]],
        },
        fields=["validation_type", "status", "validation_datetime", "creation"],
        order_by="validation_datetime desc, creation desc",
    )

    latest_by_type = {}
    latest_success_datetime = None

    for row in logs:
        validation_type = "Udyog Aadhaar" if row.validation_type == "Udyam" else row.validation_type
        if validation_type not in latest_by_type:
            latest_by_type[validation_type] = row.status

        if row.status == "Success" and row.validation_datetime:
            if not latest_success_datetime or row.validation_datetime > latest_success_datetime:
                latest_success_datetime = row.validation_datetime

    return latest_by_type, latest_success_datetime


def _is_onboarding_manager():
    return bool({"Purchase Manager", "System Manager", "DeVoltrans Management"} & set(frappe.get_roles()))


def _reconcile_single_supplier_onboarding(doc, settings):
    latest_statuses, latest_success_datetime = _latest_validation_log_statuses(doc.name)

    checks = [
        ("GSTN", "gstn_validated", "gstn", bool(settings.enable_gstn_validation)),
        ("PAN", "pan_validated", "pan", bool(settings.enable_pan_validation)),
        ("CIN", "cin_validated", "cin", bool(settings.enable_cin_validation)),
        ("Bank Account", "bank_validated", "bank_account_no", bool(settings.enable_bank_validation)),
        (
            "Udyog Aadhaar",
            "udyam_validated",
            "udyog_aadhaar",
            bool(settings.enable_udyog_aadhaar_validation),
        ),
    ]

    updates = {}
    failed_sections = []
    pending_sections = []
    enabled_checks = 0

    for validation_type, flag_field, value_field, enabled in checks:
        if not enabled:
            continue

        enabled_checks += 1
        raw_value = doc.get(value_field)
        has_value = bool(raw_value.strip()) if isinstance(raw_value, str) else bool(raw_value)

        if not has_value:
            updates[flag_field] = 0
            pending_sections.append(validation_type)
            continue

        status = latest_statuses.get(validation_type)
        if status == "Success":
            updates[flag_field] = 1
        elif status == "Failed":
            updates[flag_field] = 0
            failed_sections.append(validation_type)
        else:
            updates[flag_field] = 0
            pending_sections.append(validation_type)

    target_onboarding_status = doc.onboarding_status
    target_validation_status = doc.validation_status
    target_validation_remarks = doc.validation_remarks
    target_validation_date = doc.validation_date

    if enabled_checks > 0:
        if failed_sections:
            target_validation_status = "Failed"
            target_onboarding_status = "Validation Failed"
            target_validation_remarks = _build_reconcile_failure_message(failed_sections)
        elif pending_sections:
            # Submitted records with partial logs should be shown as in progress.
            if doc.onboarding_status != "Pending Submission":
                target_validation_status = "In Progress"
                target_onboarding_status = "Data Submitted"
                target_validation_remarks = None
        else:
            target_validation_status = "Validated"
            target_onboarding_status = "Validation Successful"
            target_validation_remarks = None
            target_validation_date = latest_success_datetime or frappe.utils.now()

    has_changes = False
    changed_fields = []

    for fieldname, value in updates.items():
        if doc.get(fieldname) != value:
            doc.set(fieldname, value)
            changed_fields.append(fieldname)
            has_changes = True

    if doc.onboarding_status != target_onboarding_status:
        doc.onboarding_status = target_onboarding_status
        changed_fields.append("onboarding_status")
        has_changes = True
    if doc.validation_status != target_validation_status:
        doc.validation_status = target_validation_status
        changed_fields.append("validation_status")
        has_changes = True
    if (doc.validation_remarks or None) != (target_validation_remarks or None):
        doc.validation_remarks = target_validation_remarks
        changed_fields.append("validation_remarks")
        has_changes = True
    if target_validation_status == "Validated" and doc.validation_date != target_validation_date:
        doc.validation_date = target_validation_date
        changed_fields.append("validation_date")
        has_changes = True

    if has_changes:
        doc.save(ignore_permissions=True)

    return {
        "updated": has_changes,
        "onboarding_status": doc.onboarding_status,
        "validation_status": doc.validation_status,
        "changed_fields": changed_fields,
    }


def _reconcile_supplier_onboarding_validation_states():
    settings = frappe.get_single("Cashfree Settings")
    onboarding_names = frappe.get_all(
        "Supplier Onboarding",
        filters={
            "docstatus": ["!=", 2],
            "onboarding_status": ["not in", ["Approved", "Rejected"]],
        },
        pluck="name",
    )

    result = {
        "processed": 0,
        "updated": 0,
        "validated": 0,
        "failed": 0,
        "in_progress": 0,
    }

    for onboarding_name in onboarding_names:
        result["processed"] += 1
        doc = frappe.get_doc("Supplier Onboarding", onboarding_name)
        reconcile_result = _reconcile_single_supplier_onboarding(doc, settings)
        if reconcile_result["updated"]:
            result["updated"] += 1

            if reconcile_result["validation_status"] == "Validated":
                result["validated"] += 1
            elif reconcile_result["validation_status"] == "Failed":
                result["failed"] += 1
            elif reconcile_result["validation_status"] == "In Progress":
                result["in_progress"] += 1

    return result


@frappe.whitelist()
def reconcile_supplier_onboarding_validation_states():
    """One-time cleanup: reconcile onboarding validation flags and status from validation logs."""
    frappe.only_for("System Manager")
    result = _reconcile_supplier_onboarding_validation_states()
    frappe.db.commit()
    return {
        "success": True,
        "message": _(
            "Reconciliation complete. Processed {0}, updated {1} (validated: {2}, failed: {3}, in progress: {4})."
        ).format(
            result["processed"],
            result["updated"],
            result["validated"],
            result["failed"],
            result["in_progress"],
        ),
        "result": result,
    }


@frappe.whitelist()
def reconcile_supplier_onboarding_validation_state(supplier_onboarding):
    """Reconcile a single Supplier Onboarding record from validation logs."""
    if not _is_onboarding_manager():
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    if not supplier_onboarding:
        frappe.throw(_("Supplier Onboarding is required"))

    doc = frappe.get_doc("Supplier Onboarding", supplier_onboarding)
    if doc.docstatus == 2:
        frappe.throw(_("Cannot reconcile cancelled Supplier Onboarding records"))

    settings = frappe.get_single("Cashfree Settings")
    reconcile_result = _reconcile_single_supplier_onboarding(doc, settings)
    frappe.db.commit()

    return {
        "success": True,
        "updated": reconcile_result["updated"],
        "message": _("Reconciliation completed for {0}.").format(supplier_onboarding),
        "onboarding_status": reconcile_result["onboarding_status"],
        "validation_status": reconcile_result["validation_status"],
        "changed_fields": reconcile_result["changed_fields"],
    }


@frappe.whitelist()
def get_vendor_portal_data():
    """
    Get supplier portal data for current user
    """
    # Enhanced session validation
    if not frappe.session or frappe.session.user == "Guest":
        return {
            "error": "login_required", 
            "message": _("Please login to access the supplier portal"),
            "redirect_url": "/login?redirect-to=/vendor-portal"
        }
    
    user = frappe.session.user
    if not user or user == "Guest":
        return {
            "error": "login_required", 
            "message": _("Please login to access the supplier portal"),
            "redirect_url": "/login?redirect-to=/vendor-portal"
        }
    
    # Check if this user has Supplier role with enhanced validation
    user_roles = frappe.get_roles(user)
    if not ("Supplier" in user_roles):
        return {
            "error": "access_denied", 
            "message": _("This portal is only for registered suppliers. Please contact support if you believe this is an error."),
            "redirect_url": "/access-denied?message=supplier_portal"
        }
    
    # Get supplier associated with this email with additional validation
    try:
        supplier = frappe.db.get_value("Supplier", {"email_id": user}, "name")
        if not supplier:
            return {
                "error": "supplier_not_found",
                "message": _("No supplier account found for your email address. Please contact support."),
                "redirect_url": "/contact-support"
            }
        
        # Get onboarding records for this supplier with enhanced filtering
        supplier_doc = frappe.get_doc("Supplier", supplier)
        onboarding_list = frappe.get_list(
            "Supplier Onboarding",
            filters={
                "supplier": supplier, 
                "email": user,
                "docstatus": ["!=", 2]  # Exclude cancelled documents
            },
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

        for rec in onboarding_list:
            rec.validation_remarks = _sanitize_vendor_remarks(
                rec.onboarding_status, rec.validation_remarks
            )

        approved_exists = any(rec.onboarding_status == "Approved" for rec in onboarding_list)
        onboarding_only = bool(supplier_doc.disabled or not approved_exists)
        active_onboarding = None
        for rec in onboarding_list:
            if rec.onboarding_status not in ("Approved", "Rejected"):
                active_onboarding = rec
                break
        if not active_onboarding and onboarding_list:
            active_onboarding = onboarding_list[0]

        return {
            "supplier_found": True,
            "supplier_name": supplier,
            "supplier_enabled": not supplier_doc.disabled,
            "onboarding_only": onboarding_only,
            "active_onboarding": active_onboarding,
            "onboarding_list": onboarding_list,
            "has_pending": any(
                rec.onboarding_status == "Pending Submission" 
                for rec in onboarding_list
            ),
            "user_email": user,
            "session_valid": True
        }
        
    except Exception as e:
        frappe.log_error(
            message=f"Error getting supplier portal data for user {user}: {str(e)}",
            title="Supplier Portal Data Error"
        )
        return {
            "error": "system_error",
            "message": _("Unable to load portal data. Please try again or contact support."),
            "redirect_url": "/contact-support"
        }

@frappe.whitelist()
def get_onboarding_form_data(onboarding_id):
    """
    Get onboarding form data for editing
    """
    # Enhanced session validation
    if not frappe.session or frappe.session.user == "Guest":
        return {
            "error": "login_required", 
            "message": _("Please login to access your onboarding data"),
            "redirect_url": "/login?redirect-to=/vendor-portal"
        }
    
    user = frappe.session.user
    if not user or user == "Guest":
        return {
            "error": "login_required", 
            "message": _("Please login to access your onboarding data"),
            "redirect_url": "/login?redirect-to=/vendor-portal"
        }
    
    # Check if user has Supplier role
    user_roles = frappe.get_roles(user)
    if not ("Supplier" in user_roles):
        return {
            "error": "access_denied", 
            "message": _("You do not have permission to access this resource"),
            "redirect_url": "/access-denied?message=supplier_portal"
        }
    
    if not onboarding_id:
        return {"error": "invalid_request", "message": _("Onboarding ID is required")}
    
    try:
        doc = frappe.get_doc("Supplier Onboarding", onboarding_id)
        
        # Enhanced security check with additional validations
        if doc.email != user:
            return {
                "error": "access_denied", 
                "message": _("You can only access your own onboarding records"),
                "redirect_url": "/access-denied?message=supplier_portal"
            }
        
        # Check if document is cancelled
        if doc.docstatus == 2:
            return {
                "error": "cancelled",
                "message": _("This onboarding record has been cancelled"),
                "redirect_url": "/vendor-portal"
            }
        
        if doc.onboarding_status not in VENDOR_EDITABLE_ONBOARDING_STATUSES:
            return {
                "error": "locked", 
                "message": _(
                    "You can update details only when onboarding is in Pending Submission, Validation Failed, or Rejected status."
                ),
                "redirect_url": "/vendor-portal"
            }
        
        supplier = frappe.get_doc("Supplier", doc.supplier)

        return {
            "success": True,
            "doc": {
                "name": doc.name,
                "supplier": doc.supplier,
                "email": doc.email,
                "onboarding_status": doc.onboarding_status,
                "validation_status": doc.validation_status,
                "gstn": doc.gstn,
                "pan": doc.pan,
                "cin": doc.cin,
                "bank_account_no": doc.bank_account_no,
                "bank_ifsc_code": doc.bank_ifsc_code,
                "udyog_aadhaar": doc.udyog_aadhaar,
                "phone_number": doc.phone_number,
                "udyam_validated": doc.udyam_validated,
                "validation_remarks": _sanitize_vendor_remarks(
                    doc.onboarding_status, doc.validation_remarks
                ),
                "rejection_reason": doc.rejection_reason,
                "existing_required_files": _get_existing_required_files(doc.name),
            },
            "supplier_enabled": not supplier.disabled,
            "session_valid": True
        }
        
    except frappe.DoesNotExistError:
        return {
            "error": "not_found",
            "message": _("Onboarding record not found"),
            "redirect_url": "/vendor-portal"
        }
    except Exception as e:
        frappe.log_error(
            message=f"Error loading onboarding form data for {onboarding_id}: {str(e)}",
            title="Onboarding Form Data Error"
        )
        return {
            "error": "system_error", 
            "message": _("Unable to load onboarding record. Please try again or contact support."),
            "redirect_url": "/contact-support"
        }

@frappe.whitelist()
def submit_onboarding_data(onboarding_id, data):
    """
    Submit onboarding data from web form (without files).
    """
    try:
        import json
        if isinstance(data, str):
            data = json.loads(data)
        
        data = _normalize_supplier_payload(data)
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
        
        validation_errors = _validate_supplier_payload(data)
        if validation_errors:
            return {
                "success": False,
                "message": _("Validation failed: {0}").format("; ".join(validation_errors)),
                "errors": validation_errors,
            }

        _deduplicate_attachments(doc.name)

        missing_files = [field for field in REQUIRED_UPLOAD_FIELDS if not _has_attachment(doc.name, field)]
        if missing_files:
            return {
                "success": False,
                "message": _("Please upload all required documents before submitting."),
                "errors": missing_files,
            }

        # Update fields
        doc.gstn = data.get("gstn")
        doc.pan = data.get("pan")
        doc.cin = data.get("cin")
        doc.bank_account_no = data.get("bank_account_no")
        doc.bank_ifsc_code = data.get("bank_ifsc_code")
        doc.udyog_aadhaar = data.get("udyog_aadhaar")
        doc.phone_number = data.get("phone_number")
        _prepare_onboarding_for_resubmission(doc)
        
        doc.save(ignore_permissions=True)
        _deduplicate_attachments(doc.name)
        
        return {"success": True, "message": "Data submitted successfully"}
        
    except Exception as e:
        frappe.log_error(message=str(e), title="Supplier Data Submission Failed")
        return {"success": False, "message": _("Unable to submit data. Please try again later.")}

@frappe.whitelist()
def submit_onboarding_with_files(
    onboarding_id,
    gstn,
    pan,
    cin=None,
    bank_account_no=None,
    bank_ifsc_code=None,
    udyog_aadhaar=None,
    phone_number=None,
    gstn_certificate=None,
    pan_card=None,
    bank_cheque=None,
    udyog_aadhaar_certificate=None,
    cin_certificate=None,
    company_logo=None,
):
    """
    Submit onboarding data with file attachments
    """
    doc = None
    uploaded_files = []
    
    try:
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
        
        normalized_data = _normalize_supplier_payload(
            {
                "gstn": gstn,
                "pan": pan,
                "cin": cin,
                "bank_account_no": bank_account_no,
                "bank_ifsc_code": bank_ifsc_code,
                "udyog_aadhaar": udyog_aadhaar,
                "phone_number": phone_number,
            }
        )

        validation_errors = _validate_supplier_payload(normalized_data)
        
        if validation_errors:
            return {
                "success": False,
                "message": f"Validation failed: {'; '.join(validation_errors)}",
                "errors": validation_errors
            }
        
        # Update fields
        doc.gstn = normalized_data.get("gstn")
        doc.pan = normalized_data.get("pan")
        doc.cin = normalized_data.get("cin")
        doc.bank_account_no = normalized_data.get("bank_account_no")
        doc.bank_ifsc_code = normalized_data.get("bank_ifsc_code")
        doc.udyog_aadhaar = normalized_data.get("udyog_aadhaar")
        doc.phone_number = normalized_data.get("phone_number")
        _prepare_onboarding_for_resubmission(doc)
        
        # Save the document first (without committing yet)
        doc.save(ignore_permissions=True)
        _deduplicate_attachments(doc.name)
        
        # Handle file uploads with proper error handling
        file_mappings = {
            'gstn_certificate': gstn_certificate,
            'pan_card': pan_card,
            'bank_cheque': bank_cheque,
            'udyog_aadhaar_certificate': udyog_aadhaar_certificate,
            'cin_certificate': cin_certificate,
            'company_logo': company_logo,
        }
        
        for field_name, file_obj in file_mappings.items():
            if file_obj and hasattr(file_obj, 'filename'):
                try:
                    frappe.logger().info(f"Processing file upload: {field_name} - {file_obj.filename}")
                    
                    # Validate file size (max 5MB)
                    file_size = len(file_obj.read())
                    file_obj.seek(0)  # Reset file pointer
                    
                    if file_size > 5 * 1024 * 1024:  # 5MB limit
                        raise frappe.ValidationError(f"File {file_obj.filename} is too large. Maximum size is 5MB.")
                    
                    # Validate file type
                    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
                    filename = file_obj.filename.lower()
                    if not any(filename.endswith(ext) for ext in allowed_extensions):
                        raise frappe.ValidationError(f"File type not allowed for {file_obj.filename}. Allowed types: PDF, JPG, PNG, DOC, DOCX")
                    
                    # Use Frappe's save_file method for proper attachment
                    from frappe.utils.file_manager import save_file
                    
                    file_doc = save_file(
                        filename=file_obj.filename,
                        content=file_obj.read(),
                        dt=doc.doctype,
                        dn=doc.name,
                        folder="Home/Attachments",
                        is_private=1
                    )
                    
                    if file_doc:
                        frappe.logger().info(f"File document created: {file_doc.name}")
                        frappe.db.set_value(
                            "File",
                            file_doc.name,
                            "attached_to_field",
                            field_name,
                            update_modified=False,
                        )
                        
                        uploaded_files.append({
                            'file_name': file_obj.filename,
                            'file_url': file_doc.file_url,
                            'file_name_field': file_doc.name,
                            'field': field_name
                        })
                    else:
                        raise frappe.ValidationError(f"Failed to save file {file_obj.filename}")
                        
                except Exception as file_error:
                    frappe.logger().error(f"Failed to upload {field_name}: {str(file_error)}")
                    frappe.log_error(
                        message=f"Failed to upload {field_name} for onboarding {onboarding_id}: {str(file_error)}",
                        title="File Upload Error"
                    )
                    # Don't return error immediately, collect all file errors
                    uploaded_files.append({
                        'field': field_name,
                        'error': str(file_error),
                        'file_name': file_obj.filename if hasattr(file_obj, 'filename') else 'Unknown'
                    })
        
        # Check if any files failed to upload
        failed_uploads = [f for f in uploaded_files if 'error' in f]
        if failed_uploads:
            # Rollback: delete successfully uploaded files
            for uploaded_file in uploaded_files:
                if 'error' not in uploaded_file and 'file_name_field' in uploaded_file:
                    try:
                        frappe.delete_doc("File", uploaded_file['file_name_field'])
                    except Exception:
                        pass  # Ignore cleanup errors
            frappe.db.rollback()
            
            error_messages = [f"File {f['file_name']}: {f['error']}" for f in failed_uploads]
            return {
                "success": False,
                "message": f"File upload failed: {'; '.join(error_messages)}",
                "failed_files": failed_uploads
            }
        
        # Commit the document and files
        frappe.db.commit()
        frappe.logger().info(f"Onboarding document saved: {doc.name}")
        
        return {
            "success": True, 
            "message": "Data and documents submitted successfully",
            "uploaded_files": [f for f in uploaded_files if 'error' not in f],
            "doc_name": doc.name
        }
        
    except Exception as e:
        # Rollback: delete any uploaded files if document save failed
        for uploaded_file in uploaded_files:
            if 'file_name_field' in uploaded_file:
                try:
                    frappe.delete_doc("File", uploaded_file['file_name_field'])
                except Exception:
                    pass  # Ignore cleanup errors during rollback
        
        # Rollback document changes if it was modified
        if doc and doc.is_new() == False:
            try:
                frappe.db.rollback()
            except Exception:
                pass
        
        frappe.log_error(
            message=f"Failed to submit onboarding with files for {onboarding_id}: {str(e)}",
            title="Onboarding Submission Failed"
        )
        return {
            "success": False,
            "message": _("Unable to submit onboarding data. Please try again later."),
        }
