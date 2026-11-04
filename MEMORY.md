# App memory: Addsol Vendor Onboarding

This file is a compact, code-verified map for future work. Re-check implementation when changing behavior; details here can become stale.

## Purpose and stack

- Frappe / ERPNext v15 app for supplier onboarding, Indian business credential validation, supplier self-service web pages, purchase approval, and purchase-order gating.
- Python >=3.10; lint/format configuration is in `pyproject.toml` (Ruff), with ESLint/Prettier/pre-commit configuration at the repository root.
- Main app package: `addsol_vendor_onboarding/`. Frappe module/DocTypes/workspace: `addsol_vendor_onboarding/addsol_vendor_onboarding/`.
- The root README is broader and in places stale (its example file tree and claims should not be taken as proof of current behavior).

## Main domain model

- `Supplier Onboarding` is the central record, named `SUP-ONB-#####`. It links to ERPNext `Supplier`, stores GSTN, PAN, CIN/LLPIN, bank, Udyam, phone/email, document attachments, validation flags, status, approval metadata, and rejection/re-verification reasons.
- `Supplier Validation Log` stores per-check type, status, request/response data, and error message. Read access is explicitly granted to Purchase Manager and System Manager in its DocType JSON; treat logged data as sensitive.
- Single DocTypes: `Vendor Verification Settings` selects a provider; `Cashfree Settings` and `Dummy Provider Settings` hold provider configuration. Secrets use Password fields.
- Workspace and number cards are in `addsol_vendor_onboarding/addsol_vendor_onboarding/workspace/` and `number_card/`.

## Lifecycle and execution flow

1. `hooks.py` makes new ERPNext Suppliers disabled and requires email; it also validates email on updates for suppliers with onboarding records. A Supplier `validate` guard (`prevent_unapproved_supplier_enable`) blocks enabling a supplier (disabled → enabled) unless an `Approved` onboarding row, an active management override, or the System Manager role is present; disabling is always allowed. Purchase Order validation permits the `Vendor Management` role to create emergency POs before onboarding approval, accepts suppliers with an active management override, and otherwise requires an onboarding row in `Approved` status.
2. A Supplier Onboarding record is created with `Pending Submission`; the controller attempts to create/send supplier login credentials in `after_insert`.
3. Supplier-facing routes live in `www/vendor-portal.py` and `www/vendor-onboarding-form.py`; supplier data submission is also exposed through methods in `api/__init__.py` and the DocType controller. Verify which route the UI calls before changing submission behavior.
4. The normal submission path sets `Data Submitted`; the DocType `on_update` detects the state transition and starts asynchronous validation via `services/verification_provider.py`.
5. The selected provider's configured method is enqueued on the `default` queue. Cashfree processing is in `api/cashfree_api.py`, logs checks, updates field flags, and calls the DocType success/failure lifecycle methods.
6. On validation success, a Purchase Manager (if configured) reviews and approves or rejects. Approval copies validated GSTN/PAN to Supplier, applies a company logo if attached, enables the Supplier, and sets onboarding to `Approved`. Re-verification disables the Supplier and resets validation state.

### Onboarding status values

`Pending Submission` → `Data Submitted` → `Validation Successful` → `Approved`; failed checks go to `Validation Failed`, with resubmission possible. When every check is API-valid but a provider-returned registered name does not match `supplier_name`, the record goes to `Review Required` (validation status `Needs Review`) for Purchase Manager approve/reject; the vendor cannot edit there. Manager rejection uses `Rejected`. Validation status values are `Not Validated`, `In Progress`, `Needs Review`, `Validated`, and `Failed`.

### Registered-name verification and Review Required

- Matching helpers live in `utils/validation_utils.py` (`normalize_company_name`, `names_match`, `extract_registered_names`, `find_matching_registered_name`): normalize (uppercase, strip punctuation/honorifics, PVT→PRIVATE, LTD→LIMITED...), then normalized-exact → token-subset (≥2 tokens) → difflib similarity ≥ 0.85. GSTN matches when the legal OR trade name matches.
- `api/cashfree_api.py::_apply_check_result` sets each `*_validated` tick only when the provider call succeeded AND any returned registered name matches `supplier_name`; a response with no name ticks on API validity with no verdict. Mismatched checks write log status `Review` with the mismatch text in `error_message`.
- Outcome routing in the Cashfree worker: any API failure → `on_validation_failure`; else any name mismatch → `on_validation_review` (sets `Review Required`/`Needs Review`, generic vendor-safe `validation_remarks`, PM-only email via `send_validation_review_email`); else `on_validation_success`.
- Reconcile (`api/__init__.py::_reconcile_single_supplier_onboarding`) applies log status priority Failed > Review > pending > Success and freezes `onboarding_status`/`validation_status`/remarks on `Approved`/`Rejected` records (flags may still refresh). The comparison UI is the `name_verification_html` field rendered by `supplier_onboarding.js::render_name_verification`; the raw `*_registered_name`/`*_name_match` fields are hidden data storage.

### Provider behavior

- Provider registry is `PROVIDERS` in `services/verification_provider.py`. Current keys: `cashfree` and `dummy_provider`.
- `Vendor Verification Settings.verification_provider` is the selector. Provider settings doctype and worker/test method are resolved centrally there.
- GSTN, PAN, and bank validations are mandatory for submission through the provider settings gate; CIN and Udyam are optional/configurable.
- Dummy Provider is deliberately a placeholder that marks a record failed and returns unsuccessful test connection. Do not describe it as a working mock or production integration.
- Cashfree worker receives `validation_requested_at` and checks for stale requests / changed status before applying asynchronous results. Preserve this protection when modifying job flow.

## Security and permission boundaries

- `hooks.py`: `permission_query_conditions` and `has_permission` hooks apply to Supplier Onboarding. System Manager and Purchase Manager have broad access; Supplier users are filtered by their User email matching the onboarding email; other roles receive no records.
- Several whitelisted manager actions in the controller enforce Purchase Manager or System Manager role checks.
- `force_enable_supplier` (Supplier Onboarding controller) is the management override entry point: it requires the `Vendor Management` role and a non-empty reason, records `supplier_enable_override` / `override_enabled_by` / `override_enabled_on` / `override_reason` on the onboarding record, and adds an HTML-escaped comment on the Supplier. It changes no validation state. A Supplier without an onboarding record gets one auto-created (email required, `credentials_email_sent` pre-set so no portal email goes out).
- `www/vendor-portal.py` requires an authenticated Supplier role and lists onboarding rows scoped to the user's email and linked Supplier.
- `www/vendor-onboarding-form.py` checks the logged-in user email against the record email and limits editable states.
- `utils/request_guards.py` blocks Supplier role users from `/update-profile`; `public/js/vendor_portal_guard.js` hides the profile action as a UI companion, not a security control.
- Supplier-facing validation remarks are sanitized/generic. Detailed provider diagnostics stay in logs. Do not widen public error output casually.
- Supplier data and validation logs may contain PII and financial identifiers. Avoid adding sensitive values to logs or non-manager APIs.

## Known implementation traps

- Two submission implementations exist: `www/vendor-onboarding-form.py::submit_onboarding_data` and `addsol_vendor_onboarding/addsol_vendor_onboarding/doctype/supplier_onboarding/supplier_onboarding.py::submit_supplier_data` (with related helpers in `api/__init__.py`). Their validation, normalization, attachment requirements, and error behavior are not identical. Trace the active browser call before modifying one; avoid assuming the paths are interchangeable.
- `api/__init__.py` contains significant supplier payload validation, normalization, required-attachment checks, remark sanitization, attachment deduplication, and validation-state reconciliation helpers, despite the unhelpful module name.
- Controller lifecycle methods save records with `ignore_permissions=True` in trusted server-side flows. Any new API entry point must authorize first rather than relying on these internal saves.
- Approval is stricter than onboarding record creation: it requires status `Validation Successful` or `Review Required`; PO validation checks for `Approved` onboarding. Keep the two states distinct.
- Supplier is disabled until approval, including during re-verification. Check Supplier state side effects whenever changing status transitions.
- `approve_supplier()` persists `Approved` on the onboarding record **before** enabling the Supplier; the Supplier enable guard needs the Approved row to exist first. Keep that ordering or approval will throw.
- Management override semantics: the override flag (`supplier_enable_override`) means "supplier may stay enabled without approval". `check_supplier_status` skips re-disabling while it is set; it is cleared in `reject_supplier()` and `initiate_reverification()` (both flows then disable the supplier again). The flag may remain set on an `Approved` record as history — `is_supplier_enable_override_active` treats Approved as not active.
- `patches.txt` registers five `[post_model_sync]` patches: attachment deduplication, validation-state reconciliation, workspace force sync, removal of private duplicate workspaces, and `backfill_supplier_name_verification` (re-parses stored log `response_data` to backfill registered names/verdicts, flips mismatched Success logs to `Review`, reconciles non-final records; no API calls, idempotent, never flips `Approved`/`Rejected` status). Confirm Patch Log state before assuming whether a patch will run again; routines should remain safe if manually rerun.
- Docs under `public/docs/` are served as assets and linked from the Workspace; website manuals also have `www/*.py` / `.html` pairs.
- The Desk documentation reader is the standard Page `vendor-onboarding-help` under `addsol_vendor_onboarding/addsol_vendor_onboarding/page/`; it renders the Purchase Manager and Supplier manuals from `public/docs/`. Workspace links to those manuals deep-link to the reader with a document route in the URL hash. The README and Provider Template remain raw Markdown downloads in the separate Downloads section.
- No test modules were found in this app's tracked file inventory during this review. Bench/Frappe context is required for meaningful integration verification; do not infer a clean site state from static inspection.

## Key files by concern

| Concern | Files |
|---|---|
| Frappe hooks and ERPNext integration | `addsol_vendor_onboarding/hooks.py` |
| Onboarding lifecycle, permissions for actions, API methods | `addsol_vendor_onboarding/addsol_vendor_onboarding/doctype/supplier_onboarding/supplier_onboarding.py` |
| Provider dispatch/config | `addsol_vendor_onboarding/services/verification_provider.py` |
| Cashfree and Dummy provider adapters | `addsol_vendor_onboarding/api/cashfree_api.py`, `addsol_vendor_onboarding/api/dummy_provider_api.py` |
| Supplier portal API utilities | `addsol_vendor_onboarding/api/__init__.py`, `addsol_vendor_onboarding/api/supplier_portal.py` |
| Supplier site pages | `addsol_vendor_onboarding/www/vendor-portal.py`, `vendor-onboarding-form.py`, corresponding HTML files |
| In-Desk documentation reader | `addsol_vendor_onboarding/addsol_vendor_onboarding/page/vendor_onboarding_help/`, source Markdown in `addsol_vendor_onboarding/public/docs/` |
| Input validation and email | `addsol_vendor_onboarding/utils/validation_utils.py`, `utils/email_utils.py` |
| Permissions / portal profile guard | `addsol_vendor_onboarding/utils/permission_query_conditions.py`, `utils/request_guards.py`, `public/js/vendor_portal_guard.js` |
| Schema / browser UI | matching DocType JSON, `.py`, `.js` under `addsol_vendor_onboarding/addsol_vendor_onboarding/doctype/` |
| Patches | `addsol_vendor_onboarding/patches.txt`, `addsol_vendor_onboarding/patches/` |
| User/provider documentation | `addsol_vendor_onboarding/public/docs/`, `README.md`, `README_PROVIDER_TEMPLATE.md` |

## Migration and operational notes

- When changing DocType fields or permissions, update the exported DocType JSON and the controller/UI as applicable; then migrate in a bench site when explicitly asked to verify.
- Provider setup changes span the selector options, settings DocType, provider registry, adapter methods, and docs.
- Workspace updates may be force-synced by a post-model-sync patch, so preserve JSON definitions and keep that patch compatible with the current Workspace schema. The validation reconciliation patch is especially sensitive because it derives state from historical logs.
- This repository review was static. No site migration, API call, external Cashfree request, or test run was performed.
