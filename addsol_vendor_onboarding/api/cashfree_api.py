# Copyright (c) 2025, Addition IT Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import time
import json
import re
import requests
from frappe import _
from frappe.utils import get_datetime
from frappe.utils import cint


def get_cashfree_settings():
    """Get Cashfree API settings."""
    settings = frappe.get_single("Cashfree Settings")
    if not settings.client_id or not settings.client_secret:
        frappe.throw(_("Please configure API Settings to validate supplier details"))
    return settings


def _get_verification_base_url_for_settings(settings):
    """Resolve verification base URL honoring sandbox toggle."""
    if cint(getattr(settings, "is_sandbox", 0)):
        return "https://sandbox.cashfree.com/verification"
    return _get_verification_base_url(getattr(settings, "api_url", None) or "https://api.cashfree.com")


def _is_stale_validation_request(doc, validation_requested_at=None):
    if not validation_requested_at:
        return False

    try:
        requested_at = get_datetime(validation_requested_at)
    except Exception:
        return False

    try:
        doc_modified = get_datetime(doc.modified) if doc.modified else None
    except Exception:
        doc_modified = None

    return bool(doc_modified and doc_modified > requested_at)


def validate_supplier_details(supplier_onboarding, validation_requested_at=None):
    """
    Validate supplier details using Cashfree APIs.
    
    Args:
        supplier_onboarding: Name of Supplier Onboarding document
    """
    try:
        doc = frappe.get_doc("Supplier Onboarding", supplier_onboarding)
        settings = get_cashfree_settings()
        base_url = _get_verification_base_url_for_settings(settings)
        frappe.logger().info(
            f"Validation base URL for {supplier_onboarding}: {base_url} (is_sandbox={cint(getattr(settings, 'is_sandbox', 0))})"
        )

        # Ignore stale jobs from an older submission to avoid overwriting
        # latest validation state with outdated results.
        if _is_stale_validation_request(doc, validation_requested_at):
            frappe.logger().info(
                f"Skipping stale validation job for {supplier_onboarding}. "
                f"requested_at={validation_requested_at}, modified={doc.modified}"
            )
            return

        if doc.onboarding_status != "Data Submitted":
            frappe.logger().info(
                f"Skipping validation for {supplier_onboarding}: onboarding_status={doc.onboarding_status}"
            )
            return
        
        all_valid = True
        error_messages = []
        
        # Validate GSTN
        if settings.enable_gstn_validation:
            if doc.gstn:
                gstn_payload = {"gstin": doc.gstn}
                gstn_result = validate_gstn(doc.gstn, settings)
                doc.gstn_validated = 1 if gstn_result["success"] else 0
                if not gstn_result["success"]:
                    all_valid = False
                    error_messages.append(f"GSTN: {gstn_result['message']}")

                # Create validation log
                create_validation_log(
                    supplier_onboarding,
                    "GSTN",
                    doc.gstn,
                    gstn_result,
                    gstn_payload,
                )
            else:
                doc.gstn_validated = 0
                all_valid = False
                missing_message = "Missing GSTN"
                error_messages.append(f"GSTN: {missing_message}")
                create_validation_log(
                    supplier_onboarding,
                    "GSTN",
                    doc.gstn,
                    {"success": False, "message": missing_message, "data": None},
                    {"gstin": doc.gstn},
                )
        else:
            doc.gstn_validated = 0
        
        # Validate PAN
        if settings.enable_pan_validation:
            if doc.pan:
                pan_payload = {"pan": doc.pan}
                pan_result = validate_pan(doc.pan, settings)
                doc.pan_validated = 1 if pan_result["success"] else 0
                if not pan_result["success"]:
                    all_valid = False
                    error_messages.append(f"PAN: {pan_result['message']}")

                create_validation_log(
                    supplier_onboarding,
                    "PAN",
                    doc.pan,
                    pan_result,
                    pan_payload,
                )
            else:
                doc.pan_validated = 0
                all_valid = False
                missing_message = "Missing PAN"
                error_messages.append(f"PAN: {missing_message}")
                create_validation_log(
                    supplier_onboarding,
                    "PAN",
                    doc.pan,
                    {"success": False, "message": missing_message, "data": None},
                    {"pan": doc.pan},
                )
        else:
            doc.pan_validated = 0

        # Validate CIN/LLPIN (optional)
        if settings.enable_cin_validation:
            if doc.cin:
                cin_result = validate_cin(doc.cin, settings, supplier_onboarding=supplier_onboarding)
                cin_payload = cin_result.pop("request_payload", {"cin": doc.cin})
                doc.cin_validated = 1 if cin_result["success"] else 0
                if not cin_result["success"]:
                    all_valid = False
                    error_messages.append(f"CIN: {cin_result['message']}")

                create_validation_log(
                    supplier_onboarding,
                    "CIN",
                    doc.cin,
                    cin_result,
                    cin_payload,
                )
            else:
                doc.cin_validated = 0
        else:
            doc.cin_validated = 0
        
        # Validate Bank Account
        if settings.enable_bank_validation:
            if doc.bank_account_no and doc.bank_ifsc_code:
                bank_payload = {
                    "bank_account": doc.bank_account_no,
                    "ifsc": doc.bank_ifsc_code,
                }
                bank_result = validate_bank_account(
                    doc.bank_account_no,
                    doc.bank_ifsc_code,
                    settings
                )
                doc.bank_validated = 1 if bank_result["success"] else 0
                if not bank_result["success"]:
                    all_valid = False
                    error_messages.append(f"Bank: {bank_result['message']}")

                create_validation_log(
                    supplier_onboarding,
                    "Bank Account",
                    f"{doc.bank_account_no} - {doc.bank_ifsc_code}",
                    bank_result,
                    bank_payload,
                )
            else:
                doc.bank_validated = 0
                all_valid = False
                missing_message = "Missing bank account number or IFSC code"
                error_messages.append(f"Bank: {missing_message}")
                create_validation_log(
                    supplier_onboarding,
                    "Bank Account",
                    f"{doc.bank_account_no or ''} - {doc.bank_ifsc_code or ''}",
                    {"success": False, "message": missing_message, "data": None},
                    {
                        "bank_account": doc.bank_account_no,
                        "ifsc": doc.bank_ifsc_code,
                    },
                )
        else:
            doc.bank_validated = 0

        # Validate Udyog Aadhaar / Udyam Registration (if configured and supplied)
        if settings.enable_udyog_aadhaar_validation and doc.udyog_aadhaar:
            udyog_result = validate_udyog_aadhaar(
                doc.udyog_aadhaar,
                settings,
                supplier_onboarding=supplier_onboarding,
            )
            doc.udyam_validated = 1 if udyog_result["success"] else 0
            udyog_payload = udyog_result.pop("request_payload", {"udyam": doc.udyog_aadhaar})
            if not udyog_result["success"]:
                all_valid = False
                error_messages.append(f"Udyog Aadhaar: {udyog_result['message']}")

            create_validation_log(
                supplier_onboarding,
                "Udyog Aadhaar",
                doc.udyog_aadhaar,
                udyog_result,
                udyog_payload,
            )
        else:
            doc.udyam_validated = 0
        
        # Update supplier onboarding status
        if all_valid:
            doc.on_validation_success()
        else:
            doc.on_validation_failure("; ".join(error_messages))

        frappe.logger().info(
            "Validation decision for {0}: all_valid={1}, "
            "flags=(gstn={2}, pan={3}, cin={4}, bank={5}, udyam={6}), "
            "errors={7}".format(
                supplier_onboarding,
                all_valid,
                doc.gstn_validated,
                doc.pan_validated,
                getattr(doc, "cin_validated", 0),
                doc.bank_validated,
                getattr(doc, "udyam_validated", 0),
                "; ".join(error_messages) if error_messages else "",
            )
        )
        
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(
            message=str(e),
            title=f"Validation Failed for {supplier_onboarding}"
        )
        doc = frappe.get_doc("Supplier Onboarding", supplier_onboarding)

        # Do not downgrade to failed if validation was already persisted as successful.
        if (
            doc.onboarding_status == "Validation Successful"
            and doc.validation_status == "Validated"
        ):
            return

        doc.on_validation_failure(str(e))
        frappe.db.commit()


def validate_gstn(gstn, settings):
    """
    Validate GSTN using Cashfree API.
    
    Args:
        gstn: GSTN number
        settings: Cashfree Settings document
    
    Returns:
        dict: Validation result
    """
    base_url = _get_verification_base_url_for_settings(settings)
    return _make_api_call_with_retry(
        url=f"{base_url}/gstin",
        payload={"gstin": gstn},
        settings=settings,
        validation_type="GSTN"
    )


def validate_pan(pan, settings):
    """
    Validate PAN using Cashfree API.
    
    Args:
        pan: PAN number
        settings: Cashfree Settings document
    
    Returns:
        dict: Validation result
    """
    base_url = _get_verification_base_url_for_settings(settings)
    return _make_api_call_with_retry(
        url=f"{base_url}/pan",
        payload={"pan": pan},
        settings=settings,
        validation_type="PAN"
    )


def validate_bank_account(account_number, ifsc_code, settings):
    """
    Validate Bank Account using Cashfree API.
    
    Args:
        account_number: Bank account number
        ifsc_code: Bank IFSC code
        settings: Cashfree Settings document
    
    Returns:
        dict: Validation result
    """
    base_url = _get_verification_base_url_for_settings(settings)
    return _make_api_call_with_retry(
        url=f"{base_url}/bank-account/sync",
        payload={"bank_account": account_number, "ifsc": ifsc_code},
        settings=settings,
        validation_type="Bank Account"
    )


def validate_cin(cin, settings, supplier_onboarding=None):
    """
    Validate CIN/LLPIN using Cashfree API.
    """
    base_url = _get_verification_base_url_for_settings(settings)
    payload = {
        "verification_id": _build_udyam_verification_id(supplier_onboarding),
        "cin": cin,
    }
    result = _make_api_call_with_retry(
        url=f"{base_url}/cin",
        payload=payload,
        settings=settings,
        validation_type="CIN",
    )
    result["request_payload"] = payload
    return result


def _normalize_udyam_for_api(udyog_aadhaar):
    value = (udyog_aadhaar or "").strip().upper()
    alnum = re.sub(r"[^A-Z0-9]", "", value)
    if re.fullmatch(r"UDYAM[A-Z]{2}\d{2}\d{7}", alnum):
        return f"{alnum[:5]}-{alnum[5:7]}-{alnum[7:9]}-{alnum[9:]}"
    return value


def _build_udyam_verification_id(supplier_onboarding=None):
    if supplier_onboarding:
        return f"SUPONB-{supplier_onboarding}"
    return f"SUPONB-{frappe.generate_hash(length=12)}"


def validate_udyog_aadhaar(udyog_aadhaar, settings, supplier_onboarding=None):
    """
    Validate Udyog/Udyam using Cashfree /verification/udyam API.
    """
    normalized_alnum = re.sub(r"[^A-Z0-9]", "", (udyog_aadhaar or "").strip().upper())
    if not re.fullmatch(r"UDYAM[A-Z]{2}\d{2}\d{7}", normalized_alnum):
        return {
            "success": False,
            "message": "Please provide Udyam Registration Number in format UDYAM-XX-00-0000000",
            "data": {"normalized_value": normalized_alnum},
            "request_payload": None,
        }

    base_url = _get_verification_base_url_for_settings(settings)
    payload = {
        "verification_id": _build_udyam_verification_id(supplier_onboarding),
        "udyam": _normalize_udyam_for_api(udyog_aadhaar),
    }
    result = _make_api_call_with_retry(
        url=f"{base_url}/udyam",
        payload=payload,
        settings=settings,
        validation_type="Udyam",
    )
    result["request_payload"] = payload
    return result


def _get_verification_base_url(api_url):
    """Normalize API URL so it always ends with /verification exactly once."""
    normalized = (api_url or "").strip().rstrip("/")
    if normalized.endswith("/verification"):
        return normalized
    return f"{normalized}/verification"


def _make_api_call_with_retry(url, payload, settings, validation_type, max_retries=None):
    """
    Make API call with retry mechanism and exponential backoff.
    
    Args:
        url: API endpoint URL
        payload: Request payload
        settings: Cashfree Settings document
        validation_type: Type of validation for logging
        max_retries: Maximum number of retries (default from settings)
    
    Returns:
        dict: Validation result
    """
    if max_retries is None:
        max_retries = settings.retry_attempts or 3
    
    headers = {
        "x-client-id": settings.client_id,
        "x-client-secret": settings.get_password("client_secret"),
        "Content-Type": "application/json"
    }
    
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            # Log retry attempt if not the first attempt
            if attempt > 0:
                frappe.logger().info(f"{validation_type} validation retry attempt {attempt + 1}/{max_retries + 1}")
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=settings.timeout or 30
            )
            
            # Check if request was successful
            if response.status_code == 200:
                data = response.json()
                is_success, message = _interpret_verification_response(validation_type, data)
                return {
                    "success": is_success,
                    "message": message,
                    "data": data,
                }
            elif response.status_code in [429, 500, 502, 503, 504]:
                # Retryable errors - implement exponential backoff
                last_error = f"API Error: {response.status_code} - {response.text}"
                if attempt < max_retries:
                    wait_time = (2 ** attempt) * 1  # Exponential backoff starting at 1 second
                    frappe.logger().warning(f"{validation_type} validation failed with {response.status_code}, retrying in {wait_time} seconds")
                    time.sleep(wait_time)
                    continue
            else:
                # Non-retryable error
                response_snippet = (response.text or "")[:500]
                if response.status_code == 403:
                    frappe.logger().warning(
                        f"{validation_type} verification forbidden. URL={url}. Response={response_snippet}"
                    )
                return {
                    "success": False,
                    "message": f"API Error: {response.status_code} - {response_snippet}",
                    "data": response.text
                }
                
        except requests.exceptions.Timeout:
            last_error = "Request timeout"
            if attempt < max_retries:
                wait_time = (2 ** attempt) * 1
                frappe.logger().warning(f"{validation_type} validation timeout, retrying in {wait_time} seconds")
                time.sleep(wait_time)
                continue
        except requests.exceptions.ConnectionError:
            last_error = "Connection error"
            if attempt < max_retries:
                wait_time = (2 ** attempt) * 1
                frappe.logger().warning(f"{validation_type} validation connection error, retrying in {wait_time} seconds")
                time.sleep(wait_time)
                continue
        except Exception as e:
            last_error = str(e)
            if attempt < max_retries:
                wait_time = (2 ** attempt) * 1
                frappe.logger().warning(f"{validation_type} validation error: {str(e)}, retrying in {wait_time} seconds")
                time.sleep(wait_time)
                continue
    
    # All retries exhausted
    return {
        "success": False,
        "message": f"{validation_type} validation failed after {max_retries + 1} attempts: {last_error}",
        "data": None
    }


def _interpret_verification_response(validation_type, data):
    message = data.get("message") if isinstance(data, dict) else None

    if validation_type in ("PAN", "GSTN", "CIN"):
        if data.get("valid") is True:
            return True, message or f"{validation_type} verified successfully"
        if isinstance(data.get("status"), str) and data.get("status").upper() in ("SUCCESS", "VALID"):
            return True, message or f"{validation_type} verified successfully"
        return False, message or f"{validation_type} validation failed"

    if validation_type == "Bank Account":
        if isinstance(data.get("account_status"), str) and data.get("account_status").upper() == "VALID":
            return True, message or "Bank account verified successfully"
        if data.get("valid") is True:
            return True, message or "Bank account verified successfully"
        return False, message or "Bank account validation failed"

    if validation_type == "Udyam":
        if data.get("valid") is True:
            return True, message or "Udyam verified successfully"
        if data.get("verified") is True:
            return True, message or "Udyam verified successfully"
        if str(data.get("sub_code", "")).strip() == "200":
            return True, message or "Udyam verified successfully"
        if isinstance(data.get("verification_status"), str) and data.get("verification_status").upper() in (
            "SUCCESS",
            "VERIFIED",
            "VALID",
        ):
            return True, message or "Udyam verified successfully"
        if isinstance(data.get("status"), str) and data.get("status").upper() in (
            "SUCCESS",
            "VERIFIED",
            "VALID",
        ):
            return True, message or "Udyam verified successfully"
        return False, message or "Udyam validation failed"

    if isinstance(data.get("status"), str) and data.get("status").upper() == "SUCCESS":
        return True, message or f"{validation_type} validated successfully"

    return False, message or f"{validation_type} validation failed"


def create_validation_log(supplier_onboarding, validation_type,
                         validation_field, result, request_data=None):
    """
    Create a validation log entry.
    
    Args:
        supplier_onboarding: Supplier Onboarding document name
        validation_type: Type of validation (GSTN/PAN/Bank)
        validation_field: Field value being validated
        result: Validation result dictionary
    """
    try:
        log = frappe.get_doc({
            "doctype": "Supplier Validation Log",
            "supplier_onboarding": supplier_onboarding,
            "validation_type": validation_type,
            "validation_field": validation_field,
            "status": "Success" if result["success"] else "Failed",
            "validation_datetime": frappe.utils.now(),
            "request_data": json.dumps(request_data, indent=2) if request_data else None,
            "response_data": json.dumps(result.get("data"), indent=2),
            "error_message": result.get("message") if not result["success"] else None
        })
        log.insert(ignore_permissions=True)
        
    except Exception as e:
        frappe.log_error(
            message=str(e),
            title="Failed to create validation log"
        )

@frappe.whitelist()
def test_connection():
    """
    Test Cashfree API connection.
    
    Returns:
        dict: Connection test result
    """
    try:
        settings = get_cashfree_settings()
        
        # Test with a dummy PAN validation (you can use a test PAN)
        # For testing purposes, we'll just check if we can reach the API
        base_url = _get_verification_base_url_for_settings(settings)
        url = "{0}/pan".format(base_url)
        
        headers = {
            "x-client-id": settings.client_id,
            "x-client-secret": settings.get_password("client_secret"),
            "Content-Type": "application/json"
        }
        
        # Test payload - this will fail validation but confirms API connectivity
        payload = {
            "pan": "AAAAA0000A"  # Dummy PAN for connection test
        }
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=settings.timeout or 30
        )
        
        # Even if validation fails, if we get a 200 or 400 response, connection is OK
        if response.status_code in [200, 400, 401, 403]:
            # Check if it's an authentication error
            if response.status_code == 401 or response.status_code == 403:
                return {
                    "success": False,
                    "message": "Authentication failed. Please check your Client ID and Client Secret."
                }
            
            return {
                "success": True,
                "message": "Connection successful! Cashfree API is reachable.",
                "status_code": response.status_code
            }
        else:
            return {
                "success": False,
                "message": "Connection failed with status code: {0}".format(response.status_code),
                "status_code": response.status_code
            }
            
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "message": "Connection timeout. Please check your network or increase timeout setting."
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "Cannot reach Cashfree API. Please check your network connection and API URL."
        }
    except Exception as e:
        frappe.log_error(
            message=str(e),
            title="Cashfree Connection Test Failed"
        )
        return {
            "success": False,
            "message": "Error: {0}".format(str(e))
        }
