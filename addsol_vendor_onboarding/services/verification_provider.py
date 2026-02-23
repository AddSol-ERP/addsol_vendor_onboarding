# Copyright (c) 2026, Addition Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _

PROVIDERS = {
    "cashfree": {
        "label": "Cashfree",
        "settings_doctype": "Cashfree Settings",
        "validate_method": "addsol_vendor_onboarding.api.cashfree_api.validate_supplier_details",
        "test_connection_method": "addsol_vendor_onboarding.api.cashfree_api.test_connection",
    },
    "dummy_provider": {
        "label": "Dummy Provider",
        "settings_doctype": "Dummy Provider Settings",
        "validate_method": "addsol_vendor_onboarding.api.dummy_provider_api.validate_supplier_details",
        "test_connection_method": "addsol_vendor_onboarding.api.dummy_provider_api.test_connection",
    }
}

ENABLE_FIELD_MAP = {
    "gstn": "enable_gstn_validation",
    "pan": "enable_pan_validation",
    "cin": "enable_cin_validation",
    "bank": "enable_bank_validation",
    "udyam": "enable_udyog_aadhaar_validation",
}


def _normalize_provider_key(raw_provider):
    value = (raw_provider or "cashfree").strip().lower()
    if value in PROVIDERS:
        return value

    slug = value.replace("-", "_").replace(" ", "_")
    if slug in PROVIDERS:
        return slug

    for key, provider in PROVIDERS.items():
        label = (provider.get("label") or "").strip().lower()
        if value == label:
            return key

    frappe.throw(_("Unsupported verification provider: {0}").format(raw_provider or ""))


def get_active_provider_key():
    settings = frappe.get_single("Vendor Verification Settings")
    return _normalize_provider_key(getattr(settings, "verification_provider", None))


def get_provider_config(provider_key=None):
    provider_key = provider_key or get_active_provider_key()
    provider = PROVIDERS.get(provider_key)
    if not provider:
        frappe.throw(_("Unsupported verification provider: {0}").format(provider_key))
    return provider


def get_active_provider_config():
    return get_provider_config()


def get_provider_settings(provider_key=None):
    provider = get_provider_config(provider_key)
    return frappe.get_single(provider["settings_doctype"])


def get_disabled_mandatory_validations(provider_key=None, settings_doc=None):
    provider_key = provider_key or get_active_provider_key()
    settings_doc = settings_doc or get_provider_settings(provider_key)

    mandatory_fields = (
        ("enable_gstn_validation", "GSTN"),
        ("enable_pan_validation", "PAN"),
        ("enable_bank_validation", "Bank Account"),
    )
    return [label for fieldname, label in mandatory_fields if not getattr(settings_doc, fieldname, 0)]


def is_validation_enabled(check_name, provider_key=None, settings_doc=None):
    provider_key = provider_key or get_active_provider_key()
    settings_doc = settings_doc or get_provider_settings(provider_key)
    fieldname = ENABLE_FIELD_MAP.get((check_name or "").strip().lower())
    if not fieldname:
        return False
    return bool(getattr(settings_doc, fieldname, 0))


def enqueue_supplier_validation(supplier_onboarding, validation_requested_at=None):
    provider = get_active_provider_config()

    enqueue_kwargs = {
        "supplier_onboarding": supplier_onboarding,
    }
    if validation_requested_at:
        enqueue_kwargs["validation_requested_at"] = validation_requested_at

    frappe.enqueue(
        method=provider["validate_method"],
        queue="default",
        timeout=300,
        is_async=True,
        **enqueue_kwargs
    )


def get_verification_provider_display_name(provider_key=None):
    return get_provider_config(provider_key)["label"]
