# Copyright (c) 2025, Addition IT Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import time
import json
import requests
from frappe import _


def get_cashfree_settings():
    """Get Cashfree API settings."""
    settings = frappe.get_single("Cashfree Settings")
    if not settings.client_id or not settings.client_secret:
        frappe.throw(_("Please configure API Settings to validate supplier details"))
    return settings


def validate_supplier_details(supplier_onboarding):
    """
    Validate supplier details using Cashfree APIs.
    
    Args:
        supplier_onboarding: Name of Supplier Onboarding document
    """
    try:
        doc = frappe.get_doc("Supplier Onboarding", supplier_onboarding)
        settings = get_cashfree_settings()
        
        all_valid = True
        error_messages = []
        
        # Validate GSTN
        if settings.enable_gstn_validation and doc.gstn:
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
        
        # Validate PAN
        if settings.enable_pan_validation and doc.pan:
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
        
        # Validate Bank Account
        if settings.enable_bank_validation and doc.bank_account_no and doc.bank_ifsc_code:
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
        
        # Update supplier onboarding status
        if all_valid:
            doc.on_validation_success()
        else:
            doc.on_validation_failure("; ".join(error_messages))
        
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
    base_url = _get_verification_base_url(settings.api_url)
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
    base_url = _get_verification_base_url(settings.api_url)
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
    base_url = _get_verification_base_url(settings.api_url)
    return _make_api_call_with_retry(
        url=f"{base_url}/bank-account/sync",
        payload={"bank_account": account_number, "ifsc": ifsc_code},
        settings=settings,
        validation_type="Bank Account"
    )


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

    if validation_type in ("PAN", "GSTN"):
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
        frappe.db.commit()
        
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
        base_url = _get_verification_base_url(settings.api_url)
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
