# Purchase Manager User Manual

## Purpose

This manual explains how a Purchase Manager should run supplier onboarding in `Addsol Vendor Onboarding` from start to finish.

## Prerequisites

- Role access: `Purchase Manager` (or `System Manager`)
- Workspace access: `Vendor Onboarding`
- Provider credentials configured in provider settings

## Step 1: Configure Verification Provider

1. Go to **Vendor Onboarding > Settings > Vendor Verification Settings**.
2. Set **Verification Provider** (for example: `Cashfree`).
3. Save.

## Step 2: Configure Provider Credentials and Validation Rules

1. Open provider-specific settings:
   - For Cashfree: **Cashfree Settings**
   - For template/testing: **Dummy Provider Settings**
2. Fill API credentials.
3. Confirm mandatory checks are enabled:
   - GSTN
   - PAN
   - Bank Account
4. Save.
5. Use **Test Connection** button (if available).

## Step 3: Create Supplier and Onboarding Record

1. Open **Supplier** and create/select supplier master.
2. Open **Supplier Onboarding** and create a new onboarding record.
3. Fill key fields:
   - Supplier
   - Email (vendor login)
   - Contact details
4. Save.

What happens after save:
- Vendor login credentials are sent to supplier email (if configured).
- Supplier remains disabled until approval.

## Step 4: Ask Vendor to Submit Details in Portal

Vendor should submit:
- GSTN, PAN, CIN (if applicable), Bank details, Udyam (if applicable)
- Required attachments (GSTN certificate, PAN, bank proof)

## Step 5: Monitor Validation Progress

Use:
- **Supplier Onboarding List** to monitor status columns
- **Supplier Validation Log** for detailed API responses per check

Expected status flow:
1. `Pending Submission`
2. `Data Submitted`
3. `Validation Successful`, `Validation Failed`, or `Review Required`
4. `Approved` (after PM approval)

## Step 6: Handle Validation Failed Cases

1. Open the onboarding record.
2. Review generic failure remark.
3. Open **Supplier Validation Log** for exact failed checks.
4. Inform vendor what to correct.
5. Vendor resubmits data.
6. Validation retriggers automatically on submit.

## Step 7: Handle Review Required Cases (Name Mismatch)

A record reaches `Review Required` when every identifier passed provider validation but at least one registered name returned by the provider does not match the supplier name entered on the record (for example, the GSTN or PAN belongs to a different party). The record is intentionally kept in flux: not failed (there is nothing for the vendor to fix) and not verified (the decision is yours).

1. Open the record with `Review Required` status.
2. Review the **Registered Name Verification** section: it compares the entered supplier name against the registered name returned per identifier, with a `Name Matched` / `Name Mismatch` verdict.
3. Open **Supplier Validation Log** for the raw provider response; `Review` status rows carry the mismatch explanation.
4. Decide:
   - **Approve** if the difference is acceptable (trade name vs legal name, naming convention, branch naming, and similar).
   - **Reject** with a clear reason if the identifiers belong to a different party; the vendor can then correct and resubmit.
5. The vendor cannot edit the record while it is in `Review Required`.

Notes:
- The vendor only sees a generic "awaiting review" remark; mismatch details stay internal (record fields, validation logs, and the Purchase Manager notification email).
- The "Verification Passed - Awaiting Approval" number card counts both `Validation Successful` and `Review Required` records, so it is your full review queue.

## Step 8: Approve Supplier

1. Open record with `Validation Successful` or `Review Required` status.
2. Click **Approve Supplier**.
3. System actions:
   - Supplier is enabled
   - Validated GSTN/PAN copied to Supplier master
   - Approval email sent to vendor

## Step 9: Reject Supplier (When Required)

1. Open onboarding record.
2. Use reject action and provide reason.
3. Rejection email is sent to vendor.

## Step 10: Re-Verification for Existing Approved Supplier

Use re-verification when supplier details changed.

1. Open approved onboarding record.
2. Trigger **Re-initiate Reverification** with reason.
3. Record moves to `Pending Submission`.
4. Supplier is temporarily disabled until successful re-validation and approval.

## Operational Best Practices

- Keep one active onboarding record per supplier process.
- Check validation logs before contacting vendor.
- Do not disable mandatory validations unless there is business approval.
- Use Dummy Provider only for template/testing, not production.

## Troubleshooting

### Validation does not start

- Check selected provider in **Vendor Verification Settings**.
- Confirm provider credentials are saved.
- Confirm mandatory checks are enabled.

### Connection test fails

- Verify API URL and credentials.
- Check internet/firewall from server.
- Check API provider service status.

### Vendor did not receive credentials

- Confirm email is correct on onboarding record.
- Use manual credentials resend action (if enabled).
- Check Error Log and Email Queue.

## Quick Navigation

- Workspace: `/app/vendor-onboarding`
- Provider selector: `/app/vendor-verification-settings`
- Cashfree settings: `/app/cashfree-settings`
- Supplier onboarding list: `/app/supplier-onboarding`
- Validation logs list: `/app/supplier-validation-log`
