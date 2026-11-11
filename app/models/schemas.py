from __future__ import annotations
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class CompanyProfile(BaseModel):
    legal_name: str = Field(..., description="Official registered business entity name")
    dba_name: Optional[str] = Field(None, description="Doing Business As / Trade name if applicable")
    country_code: str = Field(..., description="2-letter ISO country code (e.g., US, GB, DE, JP)")
    business_address: str = Field(..., description="Physical business address")
    business_type: str = Field("Corporation", description="Corporation, LLC, Partnership, Sole Proprietorship, etc.")
    tax_id: str = Field(..., description="Tax registration number (EIN, VAT, ABN, etc.)")
    tax_id_type: str = Field("EIN", description="Type of tax identification (EIN, VAT, SIREN, etc.)")
    contact_name: str = Field(..., description="Primary contact full name")
    contact_email: str = Field(..., description="Primary contact email address")
    contact_phone: Optional[str] = Field(None, description="Contact phone number")
    website: Optional[str] = Field(None, description="Company website URL")

class BankingInfo(BaseModel):
    bank_name: str = Field(..., description="Name of financial institution")
    bank_country: str = Field(..., description="Country where bank branch is domiciled")
    account_holder_name: str = Field(..., description="Name appearing on bank account statement")
    account_number_or_iban: str = Field(..., description="Account number or IBAN")
    routing_or_sort_code: Optional[str] = Field(None, description="Routing transit number (US), Sort code (UK), or BLZ (DE)")
    swift_bic: Optional[str] = Field(None, description="SWIFT/BIC code for cross-border wires")
    currency: str = Field("USD", description="Settlement currency (USD, EUR, GBP, JPY, etc.)")
    account_type: str = Field("Corporate Checking", description="Corporate Checking, Business Savings, Personal Checking, etc.")

class ComplianceDocs(BaseModel):
    tax_document_attached: bool = Field(True, description="W-9, W-8BEN, or local Certificate of Tax Registration attached")
    bank_statement_attached: bool = Field(True, description="Voided check or formal bank verification letter attached")
    certificate_of_incorporation: bool = Field(True, description="Official company registration certificate attached")
    pep_sanctions_declared_clear: bool = Field(True, description="Vendor self-certification of sanctions/PEP clearance")

class VendorSubmission(BaseModel):
    submission_id: str = Field(..., description="Unique submission identifier (e.g. SUB-2026-001)")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    company: CompanyProfile
    banking: BankingInfo
    compliance: ComplianceDocs

class RuleCheck(BaseModel):
    rule_id: str
    rule_name: str
    passed: bool
    severity: Literal["CRITICAL", "WARNING", "INFO"]
    message: str

class StageResult(BaseModel):
    stage_id: str
    stage_name: str
    status: Literal["PASSED", "WARNING", "FAILED"]
    duration_ms: float
    description: str
    rule_checks: List[RuleCheck]
    findings: List[str]

class VendorCommunication(BaseModel):
    subject: str
    recipient: str
    greeting: str
    body_summary: str
    action_items: List[str]
    deadline_note: str

class EvaluationDecision(BaseModel):
    submission_id: str
    evaluated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: Literal["APPROVED", "PENDING_ACTION", "REJECTED"]
    risk_score: int = Field(..., ge=0, le=100, description="Risk Score from 0 (clean) to 100 (high risk)")
    confidence: float = Field(..., ge=0.0, le=1.0)
    summary_reasoning: str
    total_duration_ms: float
    stages: List[StageResult]
    vendor_communication: Optional[VendorCommunication] = None
    next_steps: str

class RunRecord(BaseModel):
    run_id: str
    submission_id: str
    timestamp: str
    timestamp_ist: Optional[str] = None
    company_name: str
    country_code: str
    status: str
    risk_score: int
    duration_ms: float
    summary: str
    decision: EvaluationDecision
