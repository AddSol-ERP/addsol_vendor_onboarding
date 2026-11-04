# Agent guidance for `addsol_vendor_onboarding`

## App context

- This is a Frappe / ERPNext v15 app (`addsol_vendor_onboarding`) for Indian supplier onboarding and verification.
- The Python package lives under `addsol_vendor_onboarding/`; DocType definitions and controllers are under `addsol_vendor_onboarding/addsol_vendor_onboarding/doctype/`.
- Start with [MEMORY.md](MEMORY.md) for the architecture map and known behavioral traps. Treat code and DocType JSON as authoritative when they differ from README or manuals.
- Keep changes focused on the requested behavior. Frappe DocType JSON, Python controllers, hooks, website pages, and browser scripts often form one feature and should be reviewed together.

## Work rules

- Preserve existing user changes. Check `git status --short` before editing and inspect the relevant diff afterward.
- Do not assume a README claim is implemented. Verify the current controller, hooks, roles, and actual form/page route.
- For state changes, trace both the DocType controller and the whitelisted/API or background-job entry point. Keep status fields, validation flags, timestamps, supplier enabled state, and notifications consistent.
- Public supplier routes must authorize against the logged-in user's email and the onboarding document's email. Do not trust a client-supplied onboarding name or supplier identity without a server-side check.
- Keep provider credentials in Frappe Password fields and never log secrets. Validation request/response logs can contain sensitive supplier data; preserve role restrictions and avoid exposing raw provider errors to suppliers.
- `patches.txt` registers patches in the post-model-sync phase. Keep migration patches safe and review their Patch Log behavior before relying on reruns.
- Provider additions must be wired through `services/verification_provider.py`, have settings and an API entry point, and be explicit about unsupported or placeholder behavior. The Dummy Provider is intentionally a non-production template.
- Update user-facing docs when behavior or setup changes materially. Existing README architecture/file-tree claims are stale in places.
- Follow `pyproject.toml` / pre-commit formatting conventions (Ruff; tabs for Ruff formatting, double quotes; ESLint/Prettier for JS as configured).
- Do not add or run tests unless the user asks for tests or verification. If asked, use the app's Frappe/bench environment and report exactly what ran.

## Useful starting points

- App hooks / Supplier and Purchase Order integration: `addsol_vendor_onboarding/hooks.py`
- Onboarding lifecycle and whitelisted operations: `addsol_vendor_onboarding/addsol_vendor_onboarding/doctype/supplier_onboarding/supplier_onboarding.py`
- Provider selection and enqueueing: `addsol_vendor_onboarding/services/verification_provider.py`
- Cashfree worker and provider calls: `addsol_vendor_onboarding/api/cashfree_api.py`
- Supplier API helpers and attachment reconciliation: `addsol_vendor_onboarding/api/__init__.py`
- Supplier portal pages: `addsol_vendor_onboarding/www/`
- Permission filtering and request guard: `addsol_vendor_onboarding/utils/permission_query_conditions.py`, `addsol_vendor_onboarding/utils/request_guards.py`
- Frappe schema and desk actions: matching files under `addsol_vendor_onboarding/addsol_vendor_onboarding/doctype/`
- Manual and provider docs served in Desk: `addsol_vendor_onboarding/public/docs/`
