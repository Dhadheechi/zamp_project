from typing import Dict, Any, List

PRESETS: Dict[str, Dict[str, Any]] = {
    "happy_path": {
        "id": "happy_path",
        "title": "🟢 Happy Path: Domestic US Enterprise",
        "badge": "Expected: APPROVED",
        "badge_color": "green",
        "description": "Standard legitimate US software vendor. All tax formats, 9-digit ABA routing, corporate bank name, and documents match 100%.",
        "data": {
            "submission_id": "SUB-2026-HAPPY",
            "company": {
                "legal_name": "CloudScale Technologies Inc.",
                "dba_name": "CloudScale",
                "country_code": "US",
                "business_address": "500 Howard Street, Suite 400, San Francisco, CA 94105",
                "business_type": "Corporation",
                "tax_id": "84-1928374",
                "tax_id_type": "EIN",
                "contact_name": "Sarah Jenkins",
                "contact_email": "billing@cloudscale.io",
                "contact_phone": "+1-415-555-0199",
                "website": "https://cloudscale.io"
            },
            "banking": {
                "bank_name": "JPMorgan Chase Bank, N.A.",
                "bank_country": "US",
                "account_holder_name": "CloudScale Technologies Inc.",
                "account_number_or_iban": "48920194820",
                "routing_or_sort_code": "021000021",  # Valid NY Fedwire routing
                "swift_bic": "CHASUS33",
                "currency": "USD",
                "account_type": "Corporate Checking"
            },
            "compliance": {
                "tax_document_attached": True,
                "bank_statement_attached": True,
                "certificate_of_incorporation": True,
                "pep_sanctions_declared_clear": True
            }
        }
    },
    "name_mismatch": {
        "id": "name_mismatch",
        "title": "🔴 Edge Case 1: Beneficiary Name Mismatch (Fraud Flag)",
        "badge": "Expected: REJECTED",
        "badge_color": "red",
        "description": "Company registration is for a corporate logistics firm, but the bank payout is directed to a personal checking account under an individual's name. Signals payment diversion fraud.",
        "data": {
            "submission_id": "SUB-2026-FRAUD-1",
            "company": {
                "legal_name": "Apex Industrial Logistics LLC",
                "dba_name": "Apex Freight",
                "country_code": "US",
                "business_address": "1244 Commerce Blvd, Chicago, IL 60607",
                "business_type": "LLC",
                "tax_id": "36-9812450",
                "tax_id_type": "EIN",
                "contact_name": "Elena Rostova",
                "contact_email": "erostova@apexlogistics-portal.com",
                "contact_phone": "+1-312-555-0144",
                "website": "https://apexlogistics-portal.com"
            },
            "banking": {
                "bank_name": "Wells Fargo Bank, N.A.",
                "bank_country": "US",
                "account_holder_name": "Elena Rostova (Personal Checking)",
                "account_number_or_iban": "1092837491",
                "routing_or_sort_code": "121000248",  # Valid ABA routing transit number
                "swift_bic": "WFBIUS6S",
                "currency": "USD",
                "account_type": "Personal Checking"
            },
            "compliance": {
                "tax_document_attached": True,
                "bank_statement_attached": False,
                "certificate_of_incorporation": True,
                "pep_sanctions_declared_clear": True
            }
        }
    },
    "tax_country_mismatch": {
        "id": "tax_country_mismatch",
        "title": "🟠 Edge Case 2: Country vs. Tax ID Syntax Collision",
        "badge": "Expected: PENDING",
        "badge_color": "orange",
        "description": "German manufacturing vendor Klausen GmbH submits a UK VAT number format ('GB928371940') instead of a German USt-IdNr ('DE999999999'). Triggers automatic remediation notice.",
        "data": {
            "submission_id": "SUB-2026-TAX-MISMATCH",
            "company": {
                "legal_name": "Klausen Precision Engineering GmbH",
                "dba_name": "Klausen Tools",
                "country_code": "DE",
                "business_address": "Industriestrasse 14, 70565 Stuttgart, Germany",
                "business_type": "GmbH",
                "tax_id": "GB928371940",  # UK VAT entered by mistake
                "tax_id_type": "VAT",
                "contact_name": "Hans Klausen",
                "contact_email": "accounting@klausen-precision.de",
                "contact_phone": "+49 711 555 0122",
                "website": "https://klausen-precision.de"
            },
            "banking": {
                "bank_name": "Deutsche Bank AG",
                "bank_country": "DE",
                "account_holder_name": "Klausen Precision Engineering GmbH",
                "account_number_or_iban": "DE89370400440532013000",
                "routing_or_sort_code": "37040044",
                "swift_bic": "DEUTDEDBFRA",
                "currency": "EUR",
                "account_type": "Corporate Checking"
            },
            "compliance": {
                "tax_document_attached": True,
                "bank_statement_attached": True,
                "certificate_of_incorporation": True,
                "pep_sanctions_declared_clear": True
            }
        }
    },
    "missing_crossborder_swift": {
        "id": "missing_crossborder_swift",
        "title": "🟡 Edge Case 3: Missing Cross-Border Wire SWIFT/BIC",
        "badge": "Expected: PENDING",
        "badge_color": "yellow",
        "description": "Japanese supplier Tokyo Robotics K.K. requesting international wire disbursements, but omitted the mandatory SWIFT/BIC code. Generates targeted email instructions.",
        "data": {
            "submission_id": "SUB-2026-JP-SWIFT",
            "company": {
                "legal_name": "Tokyo Automation Works K.K.",
                "dba_name": "Tokyo Robotics",
                "country_code": "JP",
                "business_address": "2-3-1 Marunouchi, Chiyoda-ku, Tokyo 100-0005, Japan",
                "business_type": "Kabushiki Kaisha",
                "tax_id": "1010001099881",  # 13-digit valid Japanese Corporate Number
                "tax_id_type": "Corporate Number",
                "contact_name": "Kenji Sato",
                "contact_email": "finance@tokyo-robotics.co.jp",
                "contact_phone": "+81 3 5555 0188",
                "website": "https://tokyo-robotics.co.jp"
            },
            "banking": {
                "bank_name": "MUFG Bank, Ltd.",
                "bank_country": "JP",
                "account_holder_name": "Tokyo Automation Works K.K.",
                "account_number_or_iban": "0091827",
                "routing_or_sort_code": "0005-001",
                "swift_bic": "",  # Missing! Cross-border wire requirement
                "currency": "JPY",
                "account_type": "Corporate Checking"
            },
            "compliance": {
                "tax_document_attached": True,
                "bank_statement_attached": True,
                "certificate_of_incorporation": True,
                "pep_sanctions_declared_clear": True
            }
        }
    },
    "sanctions_watchlist_hit": {
        "id": "sanctions_watchlist_hit",
        "title": "🟣 Edge Case 4: Shell Entity / Sanctions Watchlist Hit",
        "badge": "Expected: REJECTED",
        "badge_color": "purple",
        "description": "Offshore entity registered in a high-risk jurisdiction whose principal matches an active OFAC/SDN global watchlist target. Immediate compliance freeze.",
        "data": {
            "submission_id": "SUB-2026-SDN-BLOCK",
            "company": {
                "legal_name": "Sovereign Maritime Trading FZE",
                "dba_name": "Sovereign Maritime",
                "country_code": "SY",  # Sanctioned country
                "business_address": "PO Box 4910, Offshore Free Zone, Port Authority",
                "business_type": "FZE",
                "tax_id": "9928172635",
                "tax_id_type": "VAT",
                "contact_name": "Viktor Chernov",  # Match on Watchlist
                "contact_email": "vchernov@mail.com",  # Free webmail
                "contact_phone": "+963 11 555 9900",
                "website": ""
            },
            "banking": {
                "bank_name": "Levant Commerce Bank",
                "bank_country": "SY",
                "account_holder_name": "Sovereign Maritime Trading",
                "account_number_or_iban": "SY910000001928374615",
                "routing_or_sort_code": "881029",
                "swift_bic": "LVNTSYDA",
                "currency": "EUR",
                "account_type": "Corporate Checking"
            },
            "compliance": {
                "tax_document_attached": False,
                "bank_statement_attached": False,
                "certificate_of_incorporation": False,
                "pep_sanctions_declared_clear": False
            }
        }
    }
}

def get_preset_list() -> List[Dict[str, Any]]:
    return [
        {
            "id": p["id"],
            "title": p["title"],
            "badge": p["badge"],
            "badge_color": p["badge_color"],
            "description": p["description"]
        }
        for p in PRESETS.values()
    ]
