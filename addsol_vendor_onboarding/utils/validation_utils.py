# -*- coding: utf-8 -*-
# Copyright (c) 2025, Addition Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import re
import frappe
from frappe import _

def _normalize_alnum(value):
    if not value:
        return ""
    return re.sub(r"[^A-Za-z0-9]", "", str(value)).upper()


def validate_gstn_format(gstn):
    """
    Validate GSTN format.
    
    Args:
        gstn: GSTN number
    
    Returns:
        tuple: (is_valid, error_message)
    """
    gstn = _normalize_alnum(gstn)
    if not gstn:
        return False, "GSTN is required"
    
    # GSTN format: 2 digits (state code) + 10 char PAN + 1 digit (entity number) 
    # + 1 char Z + 1 check digit
    pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    
    if not re.match(pattern, gstn):
        return False, "Invalid GSTN format"
    
    return True, None


def validate_pan_format(pan):
    """
    Validate PAN format.
    
    Args:
        pan: PAN number
    
    Returns:
        tuple: (is_valid, error_message)
    """
    pan = _normalize_alnum(pan)
    if not pan:
        return False, "PAN is required"
    
    # PAN format: 5 char + 4 digits + 1 char
    pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    
    if not re.match(pattern, pan):
        return False, "Invalid PAN format"
    
    return True, None


def validate_cin_format(cin):
    """
    Validate CIN/LLPIN format.

    CIN format: L12345AB1234PLC123456
    LLPIN format: AAA-1234 / AAA1234
    """
    cin = _normalize_alnum(cin)
    if not cin:
        return False, "CIN is required"

    cin_pattern = r"^[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}$"
    llpin_pattern = r"^[A-Z]{3}\d{4}$"

    if re.match(cin_pattern, cin) or re.match(llpin_pattern, cin):
        return True, None

    return False, "Invalid CIN/LLPIN format"


def validate_ifsc_format(ifsc):
    """
    Validate IFSC code format.
    
    Args:
        ifsc: IFSC code
    
    Returns:
        tuple: (is_valid, error_message)
    """
    ifsc = _normalize_alnum(ifsc)
    if not ifsc:
        return False, "IFSC code is required"
    
    # IFSC format: 4 char bank code + 0 + 6 char branch code
    pattern = r'^[A-Z]{4}0[A-Z0-9]{6}$'
    
    if not re.match(pattern, ifsc):
        return False, "Invalid IFSC code format"
    
    return True, None


def validate_phone_format(phone):
    """
    Validate phone number format.
    
    Args:
        phone: Phone number
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not phone:
        return False, "Phone number is required"
    
    # Remove all non-numeric characters
    phone_digits = re.sub(r'\D', '', phone)
    
    # Indian mobile number should be 10 digits
    if len(phone_digits) != 10:
        return False, "Phone number must be 10 digits"
    
    if not phone_digits.startswith(('6', '7', '8', '9')):
        return False, "Invalid mobile number"
    
    return True, None


@frappe.whitelist()
def validate_supplier_data_format(data):
    """
    Validate supplier data format before submission.
    
    Args:
        data: Dictionary containing supplier data
    
    Returns:
        dict: Validation result with errors if any
    """
    import json
    if isinstance(data, str):
        data = json.loads(data)
    
    errors = {}
    
    # Validate GSTN
    if data.get('gstn'):
        is_valid, error = validate_gstn_format(data['gstn'])
        if not is_valid:
            errors['gstn'] = error
    
    # Validate PAN
    if data.get('pan'):
        is_valid, error = validate_pan_format(data['pan'])
        if not is_valid:
            errors['pan'] = error

    # Validate CIN (optional)
    if data.get('cin'):
        is_valid, error = validate_cin_format(data['cin'])
        if not is_valid:
            errors['cin'] = error
    
    # Validate IFSC
    if data.get('bank_ifsc_code'):
        is_valid, error = validate_ifsc_format(data['bank_ifsc_code'])
        if not is_valid:
            errors['bank_ifsc_code'] = error
    
    # Validate Phone
    if data.get('phone_number'):
        is_valid, error = validate_phone_format(data['phone_number'])
        if not is_valid:
            errors['phone_number'] = error
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }
