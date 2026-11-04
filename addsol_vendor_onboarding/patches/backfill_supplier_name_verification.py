# Copyright (c) 2026, Addition Solutions and contributors
# For license information, please see license.txt
"""Backfill registered-name verification for historical validation runs.

Re-parses the response data already stored on Supplier Validation Log rows
(no provider API calls, no cost) to backfill the registered names and
name-match verdicts on Supplier Onboarding, flips mismatched Success logs
to Review, and reconciles non-finalized records so stale
"Validation Successful" ones surface as "Review Required".

Approved/Rejected records keep their status: only their verdicts are
backfilled. The patch is idempotent and safe to re-run.
"""
import json

import frappe

from addsol_vendor_onboarding.api import _reconcile_supplier_onboarding_validation_states
from addsol_vendor_onboarding.utils.validation_utils import (
    build_name_mismatch_message,
    extract_registered_names,
    find_matching_registered_name,
)

# validation_type -> (registered-name field, verdict field)
CHECK_FIELDS = {
    "GSTN": ("gstn_registered_name", "gstn_name_match"),
    "PAN": ("pan_registered_name", "pan_name_match"),
    "CIN": ("cin_company_name", "cin_name_match"),
    "Bank Account": ("bank_account_name", "bank_name_match"),
    "Udyog Aadhaar": ("udyam_entity_name", "udyam_name_match"),
}


def _parse_response(raw):
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _load_onboarding(cache, name):
    if name in cache:
        return cache[name]
    try:
        doc = frappe.get_doc("Supplier Onboarding", name)
    except frappe.DoesNotExistError:
        doc = False
    cache[name] = doc
    return doc


def execute():
    # Oldest first so the latest validation run decides the stored verdict.
    logs = frappe.get_all(
        "Supplier Validation Log",
        filters={
            "status": ["in", ["Success", "Review"]],
            "validation_type": ["in", list(CHECK_FIELDS)],
        },
        fields=["name", "supplier_onboarding", "validation_type", "status", "response_data"],
        order_by="validation_datetime asc, creation asc",
    )

    onboarding_cache = {}
    mismatch_onboardings = set()
    backfilled = 0
    flipped_logs = 0

    for log in logs:
        mapping = CHECK_FIELDS.get(log.validation_type)
        if not mapping:
            continue
        name_field, match_field = mapping

        onboarding = _load_onboarding(onboarding_cache, log.supplier_onboarding)
        if not onboarding:
            continue

        response = _parse_response(log.response_data)
        if response is None:
            continue

        candidates = extract_registered_names(log.validation_type, response)
        supplier_name = (onboarding.supplier_name or "").strip()
        if not candidates or not supplier_name:
            continue

        matched = find_matching_registered_name(supplier_name, candidates)
        registered_name = matched or candidates[0]
        verdict = "Matched" if matched else "Mismatch"

        updates = {}
        if (onboarding.get(name_field) or None) != registered_name:
            updates[name_field] = registered_name
        if (onboarding.get(match_field) or None) != verdict:
            updates[match_field] = verdict
        if updates:
            frappe.db.set_value(
                "Supplier Onboarding",
                log.supplier_onboarding,
                updates,
                update_modified=False,
            )
            onboarding.update(updates)
            backfilled += 1

        if verdict == "Mismatch":
            mismatch_onboardings.add(log.supplier_onboarding)
            if log.status != "Review":
                frappe.db.set_value(
                    "Supplier Validation Log",
                    log.name,
                    {
                        "status": "Review",
                        "error_message": build_name_mismatch_message(
                            log.validation_type, supplier_name, registered_name
                        ),
                    },
                    update_modified=False,
                )
                flipped_logs += 1

    # Recompute flags/status for non-final records; Approved/Rejected records
    # are excluded from reconciliation and keep their status (verdicts above).
    reconcile_result = None
    try:
        reconcile_result = _reconcile_supplier_onboarding_validation_states()
    except Exception:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="Supplier name verification backfill: reconcile failed",
        )

    frappe.db.commit()
    frappe.logger().info(
        "Supplier name verification backfill complete. "
        f"Logs processed={len(logs)}, onboarding rows backfilled={backfilled}, "
        f"logs flipped to Review={flipped_logs}, "
        f"records with mismatches={len(mismatch_onboardings)}, "
        f"reconcile={reconcile_result}"
    )
