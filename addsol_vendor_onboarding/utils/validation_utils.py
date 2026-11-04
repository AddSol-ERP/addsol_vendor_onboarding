# -*- coding: utf-8 -*-
# Copyright (c) 2025, Addition Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import difflib
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


# ---------------------------------------------------------------------------
# Registered-name verification (provider response vs entered supplier name)
# ---------------------------------------------------------------------------

# Minimum string similarity for a fuzzy name match after normalization.
NAME_MATCH_SIMILARITY_THRESHOLD = 0.85

# Tokens that carry no identity meaning and are dropped during normalization.
_NAME_DROP_TOKENS = {"THE"}

# Legal-form variants collapsed to one canonical token so that
# "PVT LTD" and "PRIVATE LIMITED" normalize identically.
_NAME_TOKEN_CANONICAL = {
    "PVT": "PRIVATE",
    "LTD": "LIMITED",
    "CO": "COMPANY",
    "CORP": "CORPORATION",
}

# Provider response keys that may carry the registered entity name, in
# preference order. Extracted defensively because providers evolve their
# schemas; GSTN prefers the legal name and falls back to the trade name.
_REGISTERED_NAME_KEYS = {
    "GSTN": (
        "legal_name_of_business",
        "trade_name_of_business",
        "name_of_business",
        "business_name",
    ),
    "PAN": (
        "registered_name",
        "name_on_card",
        "holder_name",
        "name",
    ),
    "CIN": (
        "company_name",
        "name_of_company",
    ),
    "Bank Account": (
        "account_holder_name",
        "name_on_account",
        "beneficiary_name",
        "customer_name",
        "name",
    ),
    "Udyog Aadhaar": (
        "enterprise_name",
        "entity_name",
        "firm_name",
        "organization_name",
        "name_of_enterprise",
        "name",
    ),
}

PUBLIC_VALIDATION_REVIEW_MESSAGE = _(
    "Validation completed. Some details require review by our purchase team before approval."
)

# Registered-name / name-match fields stored per check on Supplier Onboarding.
CHECK_NAME_FIELDS = (
    "gstn_registered_name",
    "gstn_name_match",
    "pan_registered_name",
    "pan_name_match",
    "cin_company_name",
    "cin_name_match",
    "bank_account_name",
    "bank_name_match",
    "udyam_entity_name",
    "udyam_name_match",
)


def reset_name_verification_fields(doc):
    """Clear registered names and name-match verdicts on a Supplier Onboarding doc."""
    for fieldname in CHECK_NAME_FIELDS:
        doc.set(fieldname, None)


def normalize_company_name(value):
    """Normalize a company/personal name for comparison.

    Uppercases, strips punctuation, drops the "M/S" honorific prefix and
    "THE", and canonicalizes common legal-form abbreviations so that
    formatting differences alone never count as a name mismatch.
    """
    if not value:
        return ""
    text = str(value).upper().strip()
    # "M/S", "M.S.", "MS", "M S" leading honorific is not part of the name.
    text = re.sub(r"^M\s*[\./]?\s*S\s+", " ", text)
    text = text.replace("&", " AND ")
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    tokens = []
    for token in text.split():
        if token in _NAME_DROP_TOKENS:
            continue
        tokens.append(_NAME_TOKEN_CANONICAL.get(token, token))
    return " ".join(tokens)


def names_match(entered_name, registered_name):
    """Return True when both names plausibly refer to the same entity.

    Match order: normalized exact match, token-subset fallback (the shorter
    name's tokens are all contained in the longer one, at least 2 tokens),
    then difflib sequence similarity >= NAME_MATCH_SIMILARITY_THRESHOLD.
    """
    entered = normalize_company_name(entered_name)
    registered = normalize_company_name(registered_name)
    if not entered or not registered:
        return False
    if entered == registered:
        return True

    entered_tokens = set(entered.split())
    registered_tokens = set(registered.split())
    if (
        len(entered_tokens) >= 2
        and len(registered_tokens) >= 2
        and (entered_tokens <= registered_tokens or registered_tokens <= entered_tokens)
    ):
        return True

    ratio = difflib.SequenceMatcher(None, entered, registered).ratio()
    return ratio >= NAME_MATCH_SIMILARITY_THRESHOLD


def extract_registered_names(validation_type, data):
    """Return candidate registered names from a provider response, preferred first."""
    if not isinstance(data, dict):
        return []
    names = []
    for key in _REGISTERED_NAME_KEYS.get(validation_type, ()):
        value = data.get(key)
        if isinstance(value, str):
            value = value.strip()
            if value and value not in names:
                names.append(value)
    return names


def find_matching_registered_name(entered_name, candidate_names):
    """Return the first candidate name matching the entered name, else None.

    For GSTN this makes the legal name OR the trade name sufficient.
    """
    for candidate in candidate_names:
        if names_match(entered_name, candidate):
            return candidate
    return None


def build_name_mismatch_message(validation_type, entered_name, registered_name):
    """Build the detailed mismatch text for validation logs and manager emails."""
    return _(
        "{0}: the registered name '{1}' does not match the supplier name '{2}' "
        "entered on this record."
    ).format(validation_type, registered_name, entered_name)
