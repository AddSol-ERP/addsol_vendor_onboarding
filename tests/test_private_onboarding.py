"""Run with a Frappe bench Python; no site or external API calls required."""
from datetime import datetime
import hashlib
import inspect
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import Mock, patch

import frappe
from frappe.utils import add_days

spec = importlib.util.spec_from_file_location(
    "private_onboarding", Path(__file__).parents[1] / "addsol_vendor_onboarding/api/private_onboarding.py"
)
private = importlib.util.module_from_spec(spec)
spec.loader.exec_module(private)


class InvitationTests(unittest.TestCase):
    def setUp(self):
        clock = patch.object(private, "now_datetime", return_value=datetime(2026, 11, 2, 12, 0))
        clock.start()
        self.addCleanup(clock.stop)
        self.token = "a" * 43
        self.doc = SimpleNamespace(
            name="SUP-ONB-00001", doctype="Supplier Onboarding", docstatus=0,
            onboarding_status="Pending Submission", invitation_expires_at=add_days(datetime(2026, 11, 2, 12, 0), 1),
        )
        self.doc.update = lambda values: self.doc.__dict__.update(values)
        framework = Mock()
        framework.PermissionError = frappe.PermissionError
        framework.throw.side_effect = frappe.PermissionError("Invalid invitation")
        framework_patch = patch.object(private, "frappe", framework)
        framework_patch.start()
        self.addCleanup(framework_patch.stop)
        translations = patch.object(private, "_", side_effect=lambda message: message)
        translations.start()
        self.addCleanup(translations.stop)

    def authorize(self, rows=None, lock=False):
        with patch.object(private.frappe, "db") as db, patch.object(private.frappe, "get_doc", return_value=self.doc):
            db.sql.return_value = [(self.doc.name,)] if rows is None else rows
            result = private._authorized_doc(self.token, lock=lock)
            self.assertEqual(db.sql.call_args.args[1], (hashlib.sha256(self.token.encode()).hexdigest(),))
            if lock:
                self.assertIn("FOR UPDATE", db.sql.call_args.args[0])
            return result

    def test_valid_invitation_and_submission_lock(self):
        self.assertIs(self.authorize(lock=True), self.doc)

    def test_unknown_or_consumed_token(self):
        with self.assertRaises(frappe.PermissionError):
            self.authorize(rows=[])

    def test_expired_invitation(self):
        self.doc.invitation_expires_at = add_days(datetime(2026, 11, 2, 12, 0), -1)
        with self.assertRaises(frappe.PermissionError):
            self.authorize()

    def test_locked_workflow_states(self):
        for status in ("Data Submitted", "Validation Successful", "Approved"):
            self.doc.onboarding_status = status
            with self.subTest(status=status), self.assertRaises(frappe.PermissionError):
                self.authorize()

    def test_cancelled_record(self):
        self.doc.docstatus = 2
        with self.assertRaises(frappe.PermissionError):
            self.authorize()

    def test_malformed_token(self):
        for token in (None, "", "short", "x" * 129):
            with self.subTest(token=token), self.assertRaises(frappe.PermissionError):
                private._authorized_doc(token)

    def test_reissue_rotates_hash_and_uses_fragment(self):
        with patch.object(private.frappe, "db") as db, patch.object(private, "get_url", return_value="https://example.test"):
            first = private.issue_invitation(self.doc)
            second = private.issue_invitation(self.doc)
            self.assertNotEqual(first, second)
            raw_token = second.split("#token=")[1]
            stored = db.set_value.call_args.args[2]
            self.assertEqual(stored["invitation_token_hash"], hashlib.sha256(raw_token.encode()).hexdigest())
            self.assertNotIn(raw_token, str(stored))
            self.assertFalse(db.set_value.call_args.kwargs["update_modified"])

    def test_cannot_invite_approved_record(self):
        self.doc.onboarding_status = "Approved"
        with self.assertRaises(frappe.PermissionError):
            private.issue_invitation(self.doc)


class SubmissionTests(unittest.TestCase):
    def setUp(self):
        self.doc = Mock(name="onboarding")
        self.doc.name = "SUP-ONB-00001"
        self.doc.doctype = "Supplier Onboarding"
        self.doc.invitation_token_hash = "old-hash"
        self.payload = dict(gstn="22AAAAA0000A1Z5", pan="AAAAA0000A", bank_account_no="123456",
                            bank_ifsc_code="SBIN0001234", phone_number="9876543210")
        self.api = SimpleNamespace(
            ALL_UPLOAD_FIELDS=("gstn_certificate", "pan_card", "bank_cheque"),
            REQUIRED_UPLOAD_FIELDS=("gstn_certificate", "pan_card", "bank_cheque"),
            _has_attachment=Mock(return_value=True),
            _normalize_supplier_payload=lambda data: data,
            _validate_supplier_payload=Mock(return_value=[]),
            _prepare_onboarding_for_resubmission=Mock(),
        )
        framework = Mock()
        framework.parse_json.side_effect = lambda data: data
        framework.request.files = {}
        framework.throw.side_effect = frappe.ValidationError("Invalid submission")
        dependencies = {
            "addsol_vendor_onboarding.api": self.api,
            "addsol_vendor_onboarding.addsol_vendor_onboarding.doctype.supplier_onboarding.supplier_onboarding":
                SimpleNamespace(_ensure_mandatory_validations_enabled_for_submission=Mock()),
            "frappe.utils.file_manager": SimpleNamespace(save_file=Mock()),
        }
        for manager in (
            patch.object(private, "frappe", framework),
            patch.object(private, "_", side_effect=lambda message: message),
            patch.object(private, "_authorized_doc", return_value=self.doc),
            patch.dict(sys.modules, dependencies),
        ):
            manager.start()
            self.addCleanup(manager.stop)

    def test_success_consumes_token_before_saving(self):
        def verify_consumed(**kwargs):
            self.assertIsNone(self.doc.invitation_token_hash)
            self.assertIsNone(self.doc.invitation_expires_at)
        self.doc.save.side_effect = verify_consumed
        self.assertTrue(inspect.unwrap(private.submit)("token", self.payload)["success"])
        private._authorized_doc.assert_called_once_with("token", lock=True)
        self.doc.save.assert_called_once_with(ignore_permissions=True)

    def test_missing_document_preserves_invitation(self):
        self.api._has_attachment.return_value = False
        with self.assertRaises(frappe.ValidationError):
            inspect.unwrap(private.submit)("token", self.payload)
        self.doc.save.assert_not_called()
        self.assertEqual(self.doc.invitation_token_hash, "old-hash")

    def test_invalid_details_do_not_submit(self):
        self.api._validate_supplier_payload.return_value = ["Invalid PAN"]
        with self.assertRaises(frappe.ValidationError):
            inspect.unwrap(private.submit)("token", self.payload)
        self.doc.save.assert_not_called()

    def test_oversized_upload_does_not_consume_token(self):
        upload = Mock()
        upload.read.return_value = b"x" * (5 * 1024 * 1024 + 1)
        private.frappe.request.files = {"gstn_certificate": upload}
        with self.assertRaises(frappe.ValidationError):
            inspect.unwrap(private.submit)("token", self.payload)
        self.doc.save.assert_not_called()
        self.assertEqual(self.doc.invitation_token_hash, "old-hash")


if __name__ == "__main__":
    unittest.main()
