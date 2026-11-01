"""Account-free onboarding. The invitation is a narrowly scoped bearer credential."""
import hashlib
import secrets
from pathlib import PurePath

import frappe
from frappe import _
from frappe.utils import add_days, get_datetime, get_url, now_datetime

EDITABLE_STATUSES = ("Pending Submission", "Validation Failed", "Rejected")
DETAIL_FIELDS = ("gstn", "pan", "cin", "bank_account_no", "bank_ifsc_code", "udyog_aadhaar", "phone_number")


def issue_invitation(doc):
    if doc.onboarding_status not in EDITABLE_STATUSES:
        frappe.throw(_("A private link can only be issued for an editable onboarding record."))
    token = secrets.token_urlsafe(32)
    values = {
        "invitation_token_hash": hashlib.sha256(token.encode()).hexdigest(),
        "invitation_expires_at": add_days(now_datetime(), 7),
    }
    # Invitation metadata must not invalidate an asynchronous validation job.
    frappe.db.set_value(doc.doctype, doc.name, values, update_modified=False)
    doc.update(values)
    # Fragments stay out of HTTP access logs and referrer headers.
    return f"{get_url()}/private-vendor-onboarding#token={token}"


def _authorized_doc(token, lock=False):
    if not isinstance(token, str) or not 32 <= len(token) <= 128:
        frappe.throw(_("This invitation is invalid or expired. Please request a new link."), frappe.PermissionError)
    digest = hashlib.sha256(token.encode()).hexdigest()
    rows = frappe.db.sql(
        "SELECT name FROM `tabSupplier Onboarding` WHERE invitation_token_hash=%s" +
        (" FOR UPDATE" if lock else ""), (digest,),
    )
    doc = frappe.get_doc("Supplier Onboarding", rows[0][0]) if rows else None
    if (not doc or doc.docstatus == 2 or doc.onboarding_status not in EDITABLE_STATUSES
            or not doc.invitation_expires_at or get_datetime(doc.invitation_expires_at) <= now_datetime()):
        frappe.throw(_("This invitation is invalid or expired. Please request a new link."), frappe.PermissionError)
    return doc


@frappe.whitelist(allow_guest=True)
def get_form(token):
    from addsol_vendor_onboarding.api import _get_existing_required_files

    doc = _authorized_doc(token)
    # Never serialize the whole document or expose attachment URLs to guests.
    return {"success": True, "doc": {
        **{field: doc.get(field) for field in DETAIL_FIELDS},
        "name": doc.name,
        "rejection_reason": doc.rejection_reason if doc.onboarding_status == "Rejected" else None,
        "existing_required_files": _get_existing_required_files(doc.name),
    }}


@frappe.whitelist(allow_guest=True, methods=["POST"])
def submit(token, data):
    from frappe.utils.file_manager import save_file
    from addsol_vendor_onboarding.api import (
        ALL_UPLOAD_FIELDS, REQUIRED_UPLOAD_FIELDS, _has_attachment,
        _normalize_supplier_payload, _validate_supplier_payload, _prepare_onboarding_for_resubmission,
    )
    from addsol_vendor_onboarding.addsol_vendor_onboarding.doctype.supplier_onboarding.supplier_onboarding import (
        _ensure_mandatory_validations_enabled_for_submission,
    )

    doc = _authorized_doc(token, lock=True)
    payload = _normalize_supplier_payload(frappe.parse_json(data))
    errors = _validate_supplier_payload(payload)
    for field in ("gstn", "pan", "bank_account_no", "bank_ifsc_code", "phone_number"):
        if not payload.get(field):
            errors.append(_("Please provide {0}").format(field.replace("_", " ")))
    if errors:
        frappe.throw("; ".join(errors))
    _ensure_mandatory_validations_enabled_for_submission()
    files = frappe.request.files
    for field in REQUIRED_UPLOAD_FIELDS:
        if not files.get(field) and not _has_attachment(doc.name, field):
            frappe.throw(_("Please upload {0}.").format(field.replace("_", " ")))

    # Validate every upload before writing any files or triggering verification.
    uploads = []
    for field in ALL_UPLOAD_FIELDS:
        upload = files.get(field)
        if upload is None:
            continue
        content = upload.read(5 * 1024 * 1024 + 1)
        if not content or len(content) > 5 * 1024 * 1024:
            frappe.throw(_("Each document must be nonempty and no larger than 5MB."))
        filename = PurePath(upload.filename.replace("\\", "/")).name
        if PurePath(filename).suffix.lower() not in {".pdf", ".jpg", ".jpeg", ".png"}:
            frappe.throw(_("Allowed file types: PDF, JPG, PNG."))
        uploads.append((field, filename, content))
    for field, filename, content in uploads:
        file_doc = save_file(filename, content, doc.doctype, doc.name, is_private=1)
        frappe.db.set_value("File", file_doc.name, "attached_to_field", field, update_modified=False)
    for field in DETAIL_FIELDS:
        doc.set(field, payload.get(field))
    _prepare_onboarding_for_resubmission(doc)
    # Consume under the same row lock before on_update starts the worker.
    doc.invitation_token_hash = None
    doc.invitation_expires_at = None
    doc.save(ignore_permissions=True)
    return {"success": True}
