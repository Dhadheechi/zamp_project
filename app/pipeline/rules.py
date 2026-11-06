import re
import unicodedata
from typing import Tuple, List, Dict, Any

# Sanctioned jurisdictions (FATF blacklist & comprehensive sanctions)
SANCTIONED_COUNTRIES = {"IR", "KP", "SY", "CU", "RU"}
HIGH_RISK_GREYLIST = {"MM", "YE", "VE", "SS"}

# Sample mock SDN / Watchlist of blocked entities & designated individuals
SANCTIONED_ENTITIES_WATCHLIST = [
    "SOVEREIGN MARITIME TRADING",
    "GLOBAL OFFSHORE LOGISTICS LTD",
    "RED STAR COMMODITIES",
    "PETROCHEMICAL TRANSNATIONAL FZE",
    "VIKTOR CHERNOV",
    "SERGEY VORONIN"
]

# Free email provider list to detect low-trust enterprise contacts
FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "protonmail.com", "mail.com", "zoho.com"
}

# Corporate legal suffix normalizer
CORP_SUFFIXES = [
    r"\bllc\b", r"\binc\b", r"\bincorporated\b", r"\bcorp\b", r"\bcorporation\b",
    r"\bltd\b", r"\blimited\b", r"\bgmbh\b", r"\bco\b", r"\bcompany\b",
    r"\bplc\b", r"\bpty\b", r"\bk\.?k\.?\b", r"\bs\.?a\.?\b", r"\bs\.?r\.?l\.?\b",
    r"\bfze\b", r"\bag\b"
]

def normalize_text(text: str) -> str:
    """Normalize text by lowercasing, removing accents, and stripping punctuation."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def strip_corporate_suffixes(name: str) -> str:
    """Remove common corporate entity suffixes for clean root entity comparison."""
    clean = normalize_text(name)
    for suffix in CORP_SUFFIXES:
        clean = re.sub(suffix, "", clean).strip()
    return re.sub(r"\s+", " ", clean).strip()

def calculate_name_similarity(name1: str, name2: str) -> float:
    """
    Calculate similarity between two business names considering root names,
    corporate suffix variance, and containment.
    """
    if not name1 or not name2:
        return 0.0
    
    n1 = normalize_text(name1)
    n2 = normalize_text(name2)
    
    if n1 == n2:
        return 1.0
    
    # Strip suffixes
    root1 = strip_corporate_suffixes(name1)
    root2 = strip_corporate_suffixes(name2)
    
    if root1 and root2 and root1 == root2:
        return 0.95
    
    # Substring check
    if root1 and root2:
        if root1 in root2 or root2 in root1:
            ratio = min(len(root1), len(root2)) / max(len(root1), len(root2))
            return max(0.80, ratio)
            
    # Jaccard word-level similarity
    words1 = set(root1.split())
    words2 = set(root2.split())
    if words1 and words2:
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union)
        
    return 0.0

def validate_us_aba_routing(routing: str) -> Tuple[bool, str]:
    """
    Validates US 9-digit ABA Routing Transit Number using Federal Reserve checksum:
    (3*(d1+d4+d7) + 7*(d2+d5+d8) + 1*(d3+d6+d9)) % 10 == 0
    """
    clean = re.sub(r"[^\d]", "", routing or "")
    if len(clean) != 9:
        return False, f"Routing number must be exactly 9 digits (got {len(clean)})"
    
    digits = [int(c) for c in clean]
    checksum = (
        3 * (digits[0] + digits[3] + digits[6]) +
        7 * (digits[1] + digits[4] + digits[7]) +
        1 * (digits[2] + digits[5] + digits[8])
    ) % 10
    
    if checksum != 0:
        return False, f"Invalid ABA routing number checksum ({clean})"
    return True, "Valid ABA routing number"

def validate_iban(iban: str) -> Tuple[bool, str]:
    """Basic IBAN structural and MOD-97 check."""
    clean = re.sub(r"[\s-]", "", iban or "").upper()
    if len(clean) < 14 or len(clean) > 34:
        return False, f"IBAN length must be between 14 and 34 characters (got {len(clean)})"
    
    if not re.match(r"^[A-Z]{2}\d{2}[A-Z0-9]+$", clean):
        return False, "IBAN format invalid (must start with 2-letter country code and 2 check digits)"
    
    # Rearrange for Mod 97 calculation
    rearranged = clean[4:] + clean[:4]
    numeric = ""
    for char in rearranged:
        if char.isalpha():
            numeric += str(ord(char) - 55)
        else:
            numeric += char
            
    try:
        if int(numeric) % 97 == 1:
            return True, "Valid IBAN"
        else:
            return False, "Invalid IBAN check digits (Mod-97 failure)"
    except Exception:
        return False, "Malformed IBAN"

def validate_swift_bic(swift: str) -> Tuple[bool, str]:
    """Validates ISO 9362 SWIFT/BIC (8 or 11 characters)."""
    clean = re.sub(r"\s", "", swift or "").upper()
    if not clean:
        return False, "SWIFT/BIC is missing"
    
    # Format: 4 letters (bank code) + 2 letters (country code) + 2 chars (location code) + optional 3 chars (branch code)
    if not re.match(r"^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$", clean):
        return False, f"Invalid SWIFT/BIC syntax: '{clean}'. Expected 8 or 11 alphanumeric characters (e.g., CHASUS33)."
    return True, "Valid SWIFT/BIC syntax"

def validate_tax_id_by_country(country: str, tax_id: str, tax_id_type: str) -> Tuple[bool, str, str]:
    """
    Validates tax registration number against country-specific syntax rules.
    Returns: (is_valid, expected_syntax_description, detected_issue)
    """
    clean = re.sub(r"\s", "", tax_id or "").upper()
    country = (country or "").upper().strip()
    
    if not clean:
        return False, "Tax ID must not be empty", "Missing Tax ID"
    
    if country == "US":
        # US EIN: 9 digits, commonly formatted as XX-XXXXXXX
        has_hyphen_match = bool(re.match(r"^\d{2}-\d{7}$", tax_id.strip()))
        raw_digits = re.sub(r"[^\d]", "", clean)
        if len(raw_digits) != 9:
            return False, "US Employer Identification Number (EIN) must be 9 digits (format: XX-XXXXXXX)", f"Invalid US EIN length: {len(raw_digits)} digits"
        # Check if submitter mistakenly provided an international VAT
        if clean.startswith("GB") or clean.startswith("DE") or clean.startswith("FR"):
            return False, "US EIN format XX-XXXXXXX", f"European VAT prefix detected on US submission ({clean})"
        return True, "Valid US EIN format", ""

    elif country == "GB":
        # UK VAT: GB followed by 9 or 12 digits, or standard company registration (8 alphanumeric)
        if clean.startswith("GB"):
            vat_num = clean[2:]
            if len(vat_num) in (9, 12) and vat_num.isdigit():
                return True, "Valid UK VAT format", ""
            return False, "UK VAT format must be GB followed by 9 or 12 digits (e.g., GB123456789)", f"Invalid UK VAT: {clean}"
        elif len(clean) == 8 and (clean.isdigit() or re.match(r"^[A-Z]{2}\d{6}$", clean)):
            return True, "Valid UK Company Registration Number", ""
        return False, "UK tax identifier should be UK VAT (GB123456789) or 8-character CRN", f"Unrecognized UK format: {clean}"

    elif country == "DE":
        # Germany: USt-IdNr starts with DE + 9 digits
        if clean.startswith("DE"):
            de_num = clean[2:]
            if len(de_num) == 9 and de_num.isdigit():
                return True, "Valid German USt-IdNr", ""
            return False, "German VAT (USt-IdNr) must be DE followed by exactly 9 digits (e.g. DE123456789)", f"Invalid German VAT length: {clean}"
        # If user submitted a foreign format like GB or US
        if clean.startswith("GB"):
            return False, "German VAT (USt-IdNr) format DE followed by 9 digits", f"UK VAT format '{clean}' entered for German entity"
        return False, "German VAT must begin with country prefix 'DE' followed by 9 digits", f"Missing DE prefix: {clean}"

    elif country == "JP":
        # Japan: Corporate Number (Hojin Bango) is 13 digits
        digits = re.sub(r"[^\d]", "", clean)
        if len(digits) == 13:
            return True, "Valid Japanese Corporate Number (13 digits)", ""
        return False, "Japanese Corporate Number must be exactly 13 digits", f"Japanese Tax/Corporate ID has {len(digits)} digits (expected 13)"

    elif country == "FR":
        # France: SIREN (9 digits), SIRET (14 digits), or FR + 11 chars VAT
        digits = re.sub(r"[^\d]", "", clean)
        if clean.startswith("FR") and len(clean) == 13:
            return True, "Valid French TVA format", ""
        if len(digits) in (9, 14):
            return True, "Valid French SIREN/SIRET", ""
        return False, "French tax ID should be 9-digit SIREN, 14-digit SIRET, or FR + 11-digit TVA", f"Invalid French tax ID: {clean}"

    elif country == "AU":
        # Australia: ABN (11 digits)
        digits = re.sub(r"[^\d]", "", clean)
        if len(digits) == 11:
            return True, "Valid Australian Business Number (ABN)", ""
        return False, "Australian Business Number (ABN) must be 11 digits", f"Invalid ABN: {len(digits)} digits"

    else:
        # Generic country check: alphanumeric between 6 and 20 chars
        if 5 <= len(clean) <= 25 and re.match(r"^[A-Z0-9-]+$", clean):
            return True, "Valid generic tax ID syntax", ""
        return False, "Tax ID must be between 5 and 25 alphanumeric characters", f"Malformed tax ID: {clean}"

