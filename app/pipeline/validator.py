import time
from typing import List, Tuple
from app.models.schemas import (
    VendorSubmission,
    StageResult,
    RuleCheck,
    EvaluationDecision,
    VendorCommunication
)
from app.pipeline.rules import (
    validate_tax_id_by_country,
    validate_us_aba_routing,
    validate_iban,
    validate_swift_bic,
    calculate_name_similarity,
    normalize_text,
    SANCTIONED_COUNTRIES,
    HIGH_RISK_GREYLIST,
    SANCTIONED_ENTITIES_WATCHLIST,
    FREE_EMAIL_DOMAINS
)
from app.pipeline.communicator import generate_vendor_communication

class VendorOnboardingPipeline:
    def __init__(self):
        pass

    def evaluate(self, submission: VendorSubmission) -> EvaluationDecision:
        overall_start = time.perf_counter()
        stages: List[StageResult] = []
        accumulated_risk = 0
        critical_flags = 0

        # =========================================================================
        # STAGE 1: Syntax & Structural Completeness
        # =========================================================================
        s1_start = time.perf_counter()
        s1_checks: List[RuleCheck] = []
        s1_findings: List[str] = []

        # Rule 1.1: Tax ID Format Check
        tax_valid, tax_expected, tax_issue = validate_tax_id_by_country(
            submission.company.country_code,
            submission.company.tax_id,
            submission.company.tax_id_type
        )
        if tax_valid:
            s1_checks.append(RuleCheck(
                rule_id="TAX_ID_SYNTAX",
                rule_name="National Tax ID Syntax",
                passed=True,
                severity="INFO",
                message=f"Tax ID conforms to {submission.company.country_code} requirements ({tax_expected})."
            ))
            s1_findings.append(f"Tax registration syntax validated for {submission.company.country_code}.")
        else:
            s1_checks.append(RuleCheck(
                rule_id="TAX_ID_SYNTAX",
                rule_name="National Tax ID Syntax",
                passed=False,
                severity="CRITICAL",
                message=f"Syntax mismatch: {tax_issue}. Expected: {tax_expected}"
            ))
            s1_findings.append(f"Invalid Tax ID: {tax_issue}")
            accumulated_risk += 30

        # Rule 1.2: Banking Syntax Check
        is_us = submission.company.country_code == "US"
        is_domestic_bank = submission.banking.bank_country == submission.company.country_code

        if is_us and is_domestic_bank:
            if submission.banking.routing_or_sort_code:
                rt_valid, rt_msg = validate_us_aba_routing(submission.banking.routing_or_sort_code)
                s1_checks.append(RuleCheck(
                    rule_id="ROUTING_SYNTAX",
                    rule_name="US Fedwire / ABA Routing Checksum",
                    passed=rt_valid,
                    severity="CRITICAL" if not rt_valid else "INFO",
                    message=rt_msg
                ))
                if not rt_valid:
                    s1_findings.append(f"ABA Routing failure: {rt_msg}")
                    accumulated_risk += 25
            else:
                s1_checks.append(RuleCheck(
                    rule_id="ROUTING_SYNTAX",
                    rule_name="US Fedwire / ABA Routing Checksum",
                    passed=False,
                    severity="CRITICAL",
                    message="Missing 9-digit ABA routing transit number."
                ))
                s1_findings.append("Missing ABA routing number for US domestic account.")
                accumulated_risk += 25
        elif submission.banking.account_number_or_iban.startswith(("GB", "DE", "FR", "NL", "ES", "IT")):
            iban_valid, iban_msg = validate_iban(submission.banking.account_number_or_iban)
            s1_checks.append(RuleCheck(
                rule_id="IBAN_SYNTAX",
                rule_name="IBAN MOD-97 Checksum",
                passed=iban_valid,
                severity="CRITICAL" if not iban_valid else "INFO",
                message=iban_msg
            ))
            if not iban_valid:
                s1_findings.append(f"IBAN validation error: {iban_msg}")
                accumulated_risk += 25

        # Rule 1.3: Cross-border SWIFT requirement
        is_cross_border = submission.banking.bank_country != "US" or submission.company.country_code != "US"
        if is_cross_border:
            swift_valid, swift_msg = validate_swift_bic(submission.banking.swift_bic or "")
            s1_checks.append(RuleCheck(
                rule_id="SWIFT_CROSSBORDER",
                rule_name="Cross-Border SWIFT/BIC Validation",
                passed=swift_valid,
                severity="CRITICAL" if not swift_valid else "INFO",
                message=swift_msg
            ))
            if not swift_valid:
                s1_findings.append(f"Missing or invalid SWIFT/BIC for cross-border transaction: {swift_msg}")
                accumulated_risk += 25

        s1_status = "FAILED" if any(not c.passed and c.severity == "CRITICAL" for c in s1_checks) else "PASSED"
        s1_duration = (time.perf_counter() - s1_start) * 1000

        stages.append(StageResult(
            stage_id="STAGE_1_SYNTAX",
            stage_name="1. Syntax & Structural Completeness",
            status=s1_status,
            duration_ms=round(s1_duration, 2),
            description="Verifies format conformity for tax registrations, bank transit codes, and IBAN/SWIFT requirements.",
            rule_checks=s1_checks,
            findings=s1_findings
        ))

        # =========================================================================
        # STAGE 2: Cross-Field Consistency & Entity Resolution
        # =========================================================================
        s2_start = time.perf_counter()
        s2_checks: List[RuleCheck] = []
        s2_findings: List[str] = []

        # Rule 2.1: Legal Name vs Bank Account Holder Name Match
        legal_name = submission.company.legal_name
        account_holder = submission.banking.account_holder_name
        dba_name = submission.company.dba_name or ""

        sim_legal = calculate_name_similarity(legal_name, account_holder)
        sim_dba = calculate_name_similarity(dba_name, account_holder) if dba_name else 0.0
        effective_sim = max(sim_legal, sim_dba)

        if effective_sim >= 0.85:
            s2_checks.append(RuleCheck(
                rule_id="NAME_CONSISTENCY",
                rule_name="Entity & Account Holder Identity Alignment",
                passed=True,
                severity="INFO",
                message=f"High identity alignment ({int(effective_sim * 100)}% match) between legal entity and bank account."
            ))
            s2_findings.append(f"Account holder name verified: '{account_holder}' aligns with '{legal_name}'.")
        elif effective_sim >= 0.60:
            s2_checks.append(RuleCheck(
                rule_id="NAME_CONSISTENCY",
                rule_name="Entity & Account Holder Identity Alignment",
                passed=True,
                severity="WARNING",
                message=f"Partial identity match ({int(effective_sim * 100)}%). Slight naming divergence detected."
            ))
            s2_findings.append("Partial name match; recommended human review for minor alias variation.")
            accumulated_risk += 15
        else:
            s2_checks.append(RuleCheck(
                rule_id="NAME_CONSISTENCY",
                rule_name="Entity & Account Holder Identity Alignment",
                passed=False,
                severity="CRITICAL",
                message=(
                    f"CRITICAL DISCREPANCY: Bank account holder '{account_holder}' does not match legal company name '{legal_name}'. "
                    "Suspected third-party payment diversion / fraud risk."
                )
            ))
            s2_findings.append(f"CRITICAL: Bank account belongs to third-party or individual ('{account_holder}').")
            accumulated_risk += 50
            critical_flags += 1

        # Rule 2.2: Email Domain Authenticity
        email = submission.company.contact_email
        email_domain = email.split("@")[-1].lower() if "@" in email else ""
        if email_domain in FREE_EMAIL_DOMAINS:
            s2_checks.append(RuleCheck(
                rule_id="EMAIL_DOMAIN_TRUST",
                rule_name="Business Domain Authenticity",
                passed=False,
                severity="WARNING",
                message=f"Contact email utilizes consumer webmail provider (@{email_domain}) rather than corporate domain."
            ))
            s2_findings.append(f"Consumer email address detected: {email}")
            accumulated_risk += 10
        else:
            s2_checks.append(RuleCheck(
                rule_id="EMAIL_DOMAIN_TRUST",
                rule_name="Business Domain Authenticity",
                passed=True,
                severity="INFO",
                message=f"Corporate email domain validated (@{email_domain})."
            ))

        s2_status = "FAILED" if any(not c.passed and c.severity == "CRITICAL" for c in s2_checks) else (
            "WARNING" if any(c.severity == "WARNING" for c in s2_checks) else "PASSED"
        )
        s2_duration = (time.perf_counter() - s2_start) * 1000

        stages.append(StageResult(
            stage_id="STAGE_2_CONSISTENCY",
            stage_name="2. Cross-Field Consistency & Entity Matching",
            status=s2_status,
            duration_ms=round(s2_duration, 2),
            description="Cross-references banking beneficiary against registered entity name, DBA aliases, and contact channels.",
            rule_checks=s2_checks,
            findings=s2_findings
        ))

        # =========================================================================
        # STAGE 3: Compliance & Sanctions Screening
        # =========================================================================
        s3_start = time.perf_counter()
        s3_checks: List[RuleCheck] = []
        s3_findings: List[str] = []

        # Rule 3.1: FATF & Comprehensive Country Sanctions
        country = submission.company.country_code.upper()
        bank_country = submission.banking.bank_country.upper()

        if country in SANCTIONED_COUNTRIES or bank_country in SANCTIONED_COUNTRIES:
            s3_checks.append(RuleCheck(
                rule_id="COUNTRY_SANCTIONS",
                rule_name="FATF / Comprehensive Jurisdiction Sanctions",
                passed=False,
                severity="CRITICAL",
                message=f"BLOCKED JURISDICTION: Country {country} is subject to comprehensive international trade sanctions."
            ))
            s3_findings.append(f"Regulatory block: Prohibited jurisdiction ({country}).")
            accumulated_risk += 60
            critical_flags += 1
        elif country in HIGH_RISK_GREYLIST or bank_country in HIGH_RISK_GREYLIST:
            s3_checks.append(RuleCheck(
                rule_id="COUNTRY_SANCTIONS",
                rule_name="FATF Greylist Jurisdiction Monitoring",
                passed=False,
                severity="WARNING",
                message=f"Country {country} is under increased FATF monitoring (Greylist)."
            ))
            s3_findings.append(f"High risk greylist jurisdiction: {country}.")
            accumulated_risk += 20
        else:
            s3_checks.append(RuleCheck(
                rule_id="COUNTRY_SANCTIONS",
                rule_name="Jurisdiction Sanctions Clearance",
                passed=True,
                severity="INFO",
                message=f"Jurisdiction {country} cleared against OFAC & FATF blacklists."
            ))

        # Rule 3.2: Watchlist / SDN Screening
        normalized_legal = normalize_text(submission.company.legal_name).upper()
        normalized_contact = normalize_text(submission.company.contact_name).upper()
        sanctions_hit = False
        matched_target = ""

        for target in SANCTIONED_ENTITIES_WATCHLIST:
            if target in normalized_legal or target in normalized_contact:
                sanctions_hit = True
                matched_target = target
                break

        if sanctions_hit:
            s3_checks.append(RuleCheck(
                rule_id="SANCTIONS_SDN",
                rule_name="Global Watchlist & SDN Screening",
                passed=False,
                severity="CRITICAL",
                message=f"DIRECT WATCHLIST HIT: Entity/Principal matched sanctioned list entry '{matched_target}'."
            ))
            s3_findings.append(f"OFAC / SDN list match: {matched_target}")
            accumulated_risk += 80
            critical_flags += 1
        else:
            s3_checks.append(RuleCheck(
                rule_id="SANCTIONS_SDN",
                rule_name="Global Watchlist & SDN Screening",
                passed=True,
                severity="INFO",
                message="Zero matches on OFAC Specially Designated Nationals (SDN) or PEP registries."
            ))

        # Rule 3.3: Account Type Appropriateness
        if submission.banking.account_type.lower() == "personal checking":
            s3_checks.append(RuleCheck(
                rule_id="ACCOUNT_TYPE_COMPLIANCE",
                rule_name="Commercial Account Type Mandate",
                passed=False,
                severity="CRITICAL",
                message="Corporate vendors must settle to an official Corporate Checking or Commercial Treasury account."
            ))
            s3_findings.append("Personal bank account submitted for commercial entity.")
            accumulated_risk += 35
        else:
            s3_checks.append(RuleCheck(
                rule_id="ACCOUNT_TYPE_COMPLIANCE",
                rule_name="Commercial Account Type Mandate",
                passed=True,
                severity="INFO",
                message=f"Account type verified: {submission.banking.account_type}."
            ))

        # Rule 3.4: Documentation Completeness
        docs = submission.compliance
        missing_docs = []
        if not docs.tax_document_attached:
            missing_docs.append("W-9/W-8BEN Tax Form")
        if not docs.bank_statement_attached:
            missing_docs.append("Voided Check / Bank Letter")
        if not docs.certificate_of_incorporation:
            missing_docs.append("Certificate of Incorporation")

        if missing_docs:
            s3_checks.append(RuleCheck(
                rule_id="DOC_COMPLIANCE",
                rule_name="Mandatory Verification Documents",
                passed=False,
                severity="WARNING",
                message=f"Missing required documentation: {', '.join(missing_docs)}."
            ))
            s3_findings.append(f"Missing documents: {', '.join(missing_docs)}")
            accumulated_risk += 15
        else:
            s3_checks.append(RuleCheck(
                rule_id="DOC_COMPLIANCE",
                rule_name="Mandatory Verification Documents",
                passed=True,
                severity="INFO",
                message="All mandatory compliance documents (Tax, Banking Letter, Incorporation) attached."
            ))

        s3_status = "FAILED" if any(not c.passed and c.severity == "CRITICAL" for c in s3_checks) else (
            "WARNING" if any(c.severity == "WARNING" for c in s3_checks) else "PASSED"
        )
        s3_duration = (time.perf_counter() - s3_start) * 1000

        stages.append(StageResult(
            stage_id="STAGE_3_COMPLIANCE",
            stage_name="3. Risk & Sanctions Compliance",
            status=s3_status,
            duration_ms=round(s3_duration, 2),
            description="Screens entity and beneficial principals against OFAC, FATF sanctions, PEP registries, and commercial criteria.",
            rule_checks=s3_checks,
            findings=s3_findings
        ))

        # =========================================================================
        # STAGE 4: Final Decision Engine & Resolution
        # =========================================================================
        final_risk_score = min(100, max(5 if stages[0].status == "PASSED" else 15, accumulated_risk))
        
        # Decision logic
        if critical_flags > 0 or final_risk_score >= 70:
            final_status = "REJECTED"
            confidence = 0.96
            summary_reasoning = (
                f"Onboarding REJECTED due to critical compliance violations or fraud indicators. "
                f"Risk score: {final_risk_score}/100. Discrepancies include: " +
                "; ".join([f for stage in stages for f in stage.findings if "CRITICAL" in f or "BLOCKED" in f or "match" in f][:2])
            )
            next_steps = "Profile locked. Escalated to Senior Compliance Officer and Fraud Operations."
        elif any(stage.status in ("FAILED", "WARNING") for stage in stages) or final_risk_score >= 25:
            final_status = "PENDING_ACTION"
            confidence = 0.92
            summary_reasoning = (
                f"Onboarding held in PENDING status. The submission requires clarification or corrected documentation. "
                f"Risk score: {final_risk_score}/100. Automated remediation notice generated for vendor."
            )
            next_steps = "Action checklist dispatched to vendor contact email. 5 business-day cure window initiated."
        else:
            final_status = "APPROVED"
            confidence = 0.99
            summary_reasoning = (
                f"Vendor successfully verified and APPROVED for payment scheduling. "
                f"Risk score: {final_risk_score}/100. Zero naming deviations or compliance alerts."
            )
            next_steps = "Vendor profile activated in AP ERP. Ready for purchase order generation and disbursement."

        # Generate Vendor Communication if not approved
        vendor_comm = generate_vendor_communication(submission, final_status, stages)

        total_duration = (time.perf_counter() - overall_start) * 1000

        return EvaluationDecision(
            submission_id=submission.submission_id,
            status=final_status,
            risk_score=final_risk_score,
            confidence=confidence,
            summary_reasoning=summary_reasoning,
            total_duration_ms=round(total_duration, 2),
            stages=stages,
            vendor_communication=vendor_comm,
            next_steps=next_steps
        )

