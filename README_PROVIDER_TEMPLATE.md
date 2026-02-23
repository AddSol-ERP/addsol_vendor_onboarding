# Provider Integration Template

This guide explains how to add a new third-party verification provider in `addsol_vendor_onboarding`.

Use the existing `Dummy Provider` as a reference implementation.

## 1. Add Provider Registry Entry

Edit:
- `addsol_vendor_onboarding/services/verification_provider.py`

Add one item in `PROVIDERS`:
- key: internal provider key (example: `acme_verify`)
- `label`: UI display name (example: `Acme Verify`)
- `settings_doctype`: singleton DocType name for provider credentials/settings
- `validate_method`: dotted path for background validation method
- `test_connection_method`: dotted path for connection test method

Example:

```python
"acme_verify": {
    "label": "Acme Verify",
    "settings_doctype": "Acme Verify Settings",
    "validate_method": "addsol_vendor_onboarding.api.acme_verify_api.validate_supplier_details",
    "test_connection_method": "addsol_vendor_onboarding.api.acme_verify_api.test_connection",
}
```

## 2. Create Provider Settings DocType

Create a new singleton DocType folder similar to:
- `addsol_vendor_onboarding/addsol_vendor_onboarding/doctype/dummy_provider_settings/`

Required files:
- `__init__.py`
- `<provider>_settings.json`
- `<provider>_settings.py`
- `<provider>_settings.js`

Recommended fields (keep same names for compatibility):
- `enable_gstn_validation`
- `enable_pan_validation`
- `enable_cin_validation`
- `enable_bank_validation`
- `enable_udyog_aadhaar_validation`
- `retry_attempts`
- `timeout`
- provider credential fields (api key/secret/token/base URL)

Why same names: shared onboarding/reconcile logic reads these flags via `verification_provider.py`.

## 3. Add Provider API Module

Create:
- `addsol_vendor_onboarding/api/<provider>_api.py`

Implement:
- `validate_supplier_details(supplier_onboarding, validation_requested_at=None)`
- `test_connection()` (whitelisted)

`validate_supplier_details` should:
1. load `Supplier Onboarding`
2. read provider settings
3. validate enabled checks (GSTN/PAN/CIN/Bank/Udyam)
4. create `Supplier Validation Log` rows
5. set flags (`gstn_validated`, `pan_validated`, etc.)
6. call onboarding success/failure flow by setting statuses and remarks consistently

Tip: use `addsol_vendor_onboarding/api/cashfree_api.py` as behavior reference.

## 4. Expose Provider in Selector

Edit:
- `addsol_vendor_onboarding/addsol_vendor_onboarding/doctype/vendor_verification_settings/vendor_verification_settings.json`

Update `verification_provider.options` with your label, one per line.

Example:

```text
Cashfree
Dummy Provider
Acme Verify
```

## 5. Update Provider Settings Hint UI

Edit:
- `addsol_vendor_onboarding/addsol_vendor_onboarding/doctype/vendor_verification_settings/vendor_verification_settings.js`

Add a branch for your provider so users get a direct link to the provider settings page.

## 6. Add Dashboard/Workspace Links

Edit:
- `addsol_vendor_onboarding/addsol_vendor_onboarding/workspace/vendor_onboarding/vendor_onboarding.json`
- `addsol_vendor_onboarding/config/buying.py`

Add links for:
- `Vendor Verification Settings`
- your provider settings DocType

## 7. Migrate and Verify

Run:

```bash
bench --site <site-name> migrate
bench --site <site-name> clear-cache
```

Verify in UI:
1. Open `Vendor Verification Settings` and select your provider.
2. Open your provider settings and save credentials.
3. Trigger supplier validation and confirm logs/status transitions.

## 8. Production Readiness Checklist

- real API credentials stored in password/secure fields
- timeout/retry values tuned
- API failures handled with safe user-facing messages
- all enabled checks write validation logs
- onboarding status transitions are correct
- connection test gives clear diagnostics
- no hardcoded Cashfree references in new provider code

## Current Template Files

Use these as copy references:
- `addsol_vendor_onboarding/services/verification_provider.py`
- `addsol_vendor_onboarding/api/dummy_provider_api.py`
- `addsol_vendor_onboarding/addsol_vendor_onboarding/doctype/dummy_provider_settings/dummy_provider_settings.json`
- `addsol_vendor_onboarding/addsol_vendor_onboarding/doctype/dummy_provider_settings/dummy_provider_settings.js`
- `addsol_vendor_onboarding/addsol_vendor_onboarding/doctype/vendor_verification_settings/vendor_verification_settings.json`
