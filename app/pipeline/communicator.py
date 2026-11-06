from typing import List, Optional
from app.models.schemas import VendorSubmission, StageResult, VendorCommunication

def generate_vendor_communication(
    submission: VendorSubmission,
    status: str,
    stages: List[StageResult]
) -> Optional[VendorCommunication]:
    """
    Synthesizes an actionable, professional communication directed to the vendor contact,
    explaining specifically what is missing, mismatched, or needed to unblock onboarding.
    """
    if status == "APPROVED":
        return None

    # Harvest all issues across all stages
    critical_issues: List[str] = []
    action_items: List[str] = []

    for stage in stages:
        for check in stage.rule_checks:
            if not check.passed:
                critical_issues.append(f"{check.rule_name}: {check.message}")
                
                # Derive targeted remediation action items
                if check.rule_id == "TAX_ID_SYNTAX":
                    action_items.append(
                        f"Provide a valid {submission.company.country_code} tax identifier. "
                        f"Current value '{submission.company.tax_id}' does not match official national formatting requirements."
                    )
                elif check.rule_id == "NAME_CONSISTENCY":
                    action_items.append(
                        f"Resolve bank account holder name discrepancy. Account is registered under '{submission.banking.account_holder_name}' "
                        f"while company is registered as '{submission.company.legal_name}'. "
                        "Please provide an updated corporate bank verification letter or update banking details to match the legal entity."
                    )
                elif check.rule_id == "SWIFT_CROSSBORDER":
                    action_items.append(
                        f"Provide a valid SWIFT/BIC code for cross-border settlement to {submission.banking.bank_name}. "
                        "International wire transfers cannot clear without an ISO 9362 SWIFT/BIC."
                    )
                elif check.rule_id == "ROUTING_SYNTAX":
                    action_items.append(
                        f"Correct the banking routing/sort code. Current routing number '{submission.banking.routing_or_sort_code}' "
                        "failed the routing transit checksum validation."
                    )
                elif check.rule_id == "DOC_COMPLIANCE":
                    action_items.append(
                        "Upload the missing required verification documents (W-9/W-8BEN tax form, voided check/bank confirmation letter, or Certificate of Incorporation)."
                    )
                elif check.rule_id == "SANCTIONS_SDN" or check.rule_id == "COUNTRY_SANCTIONS":
                    action_items.append(
                        "Submit supplemental beneficial ownership disclosures (Form 25-AML) for compliance and legal review."
                    )

    # Deduplicate action items preserving order
    deduped_actions: List[str] = []
    for item in action_items:
        if item not in deduped_actions:
            deduped_actions.append(item)

    if not deduped_actions:
        deduped_actions.append("Please reach out to the accounts payable team to clarify your submission documentation.")

    contact_name = submission.company.contact_name or "Vendor Accounts Team"
    company_name = submission.company.legal_name

    if status == "PENDING_ACTION":
        subject = f"Action Required: Information needed to complete onboarding for {company_name} (Ref: {submission.submission_id})"
        greeting = f"Dear {contact_name},"
        body_summary = (
            f"Thank you for submitting your vendor onboarding registration for {company_name}. "
            "Our automated compliance verification system reviewed your submission and identified a few items "
            "that require your attention before we can approve your account for payment processing."
        )
        deadline_note = (
            "Please respond directly to this email or re-submit the updated documents via the vendor portal within 5 business days "
            "to prevent delays in invoice settlements."
        )

    else:  # REJECTED
        subject = f"Notice: Onboarding status update for {company_name} (Ref: {submission.submission_id})"
        greeting = f"Dear {contact_name},"
        body_summary = (
            f"We have completed the compliance review for {company_name}'s vendor profile. "
            "Unfortunately, your submission could not be approved at this time due to high-risk compliance "
            "or entity divergence policies."
        )
        deadline_note = (
            "If you believe this determination was made in error or have documented legal proof of entity resolution, "
            "please contact our risk compliance team at compliance-ops@example.com."
        )

    return VendorCommunication(
        subject=subject,
        recipient=submission.company.contact_email,
        greeting=greeting,
        body_summary=body_summary,
        action_items=deduped_actions,
        deadline_note=deadline_note
    )
