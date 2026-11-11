# Zamp AI Solutions Analyst — Case Study: PS-2 Vendor Onboarding

An automated, explainable vendor verification and onboarding engine with stage-by-stage real-time execution, audit trails, and automated vendor remediation notices.

> 🌐 **Live Interactive Website (Cloudflare Pages)**: **[https://zamp-vendor-onboarding.pages.dev/](https://zamp-vendor-onboarding.pages.dev/)**  
> Access the complete, zero-install interactive demo live in your browser.

---

## 🎯 Executive Overview

Before a business can disburse funds to a new vendor, compliance and accounts payable teams must verify that the vendor is **complete, consistent, and credible**. In manual workflows, this requires tedious cross-referencing between tax registrations, corporate entity filings, and bank statements—frequently creating payment fraud vulnerabilities (such as CEO fraud / invoice diversion) and operational backlogs.

This solution automates the end-to-end evaluation of vendor submissions against a 4-stage verification pipeline, providing:
1. **Live Stage Execution View**: Real-time inspection of each verification check (syntax, cross-field entity matching, sanctions).
2. **Deterministic Risk Scoring & Decisions**: `APPROVED`, `PENDING_ACTION`, or `REJECTED`.
3. **Automated Remediation Loop**: Clear, professional communication drafted to the vendor detailing the exact discrepancies and remediation checklist.
4. **Operations & Audit Dashboard**: Complete persistence and KPI metrics tracking across all runs.

---

## 🏗️ 4-Stage Verification Pipeline Architecture

```
[ Vendor Submission (Form / JSON) ]
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│ Stage 1: Syntax & Structural Completeness             │
│ • Country-specific Tax ID regex (US EIN, DE VAT, etc.) │
│ • US ABA Routing Number Federal Reserve Checksum       │
│ • IBAN MOD-97 checksum & Cross-border SWIFT syntax     │
└────────────────────────┬───────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────┐
│ Stage 2: Cross-Field Consistency & Entity Resolution   │
│ • Legal Entity Name vs. Bank Beneficiary Alignment     │
│ • Corporate legal suffix normalizer (Inc, LLC, GmbH)   │
│ • Corporate domain validation vs. free webmail flags   │
└────────────────────────┬───────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────┐
│ Stage 3: Risk & Sanctions Screening                   │
│ • FATF Comprehensive Sanctions Blacklist (OFAC/FATF)   │
│ • Watchlist / SDN Entity & Principal Screening         │
│ • Commercial Account Type Mandate vs. Personal Payout  │
│ • Mandatory verification document checklist            │
└────────────────────────┬───────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────┐
│ Stage 4: Decision Engine & Vendor Action Dispatch      │
│ • Risk Score calculation (0–100)                       │
│ • Final Status: APPROVED | PENDING_ACTION | REJECTED   │
│ • Actionable remediation email generated for vendor    │
└────────────────────────────────────────────────────────┘
```

---

## 🧪 Scenarios & Edge Cases

The system comes pre-loaded with **5 realistic test scenarios** accessible via 1-click buttons:

| Preset | Description | Pipeline Outcome | Key Audit Trigger |
| :--- | :--- | :--- | :--- |
| **🟢 Happy Path** | Legitimate US Enterprise SaaS (`CloudScale Technologies Inc.`). Valid US EIN `84-1928374`, valid NY Fedwire ABA routing, matching Chase corporate account. | **APPROVED**<br>*(Risk: 5/100)* | All regulatory and banking fields validated with 100% entity alignment. |
| **🔴 Edge Case 1: Name Mismatch (Fraud Risk)** | Corporate logistics firm (`Apex Industrial Logistics LLC`), but payout beneficiary is an individual personal checking account (`Elena Rostova`). | **REJECTED**<br>*(Risk: 100/100)* | **Critical Divergence**: Third-party payment diversion / invoice fraud flag. Commercial mandate violated. |
| **🟠 Edge Case 2: Tax / Country Collision** | German manufacturer (`Klausen Precision Engineering GmbH`) accidentally submits UK VAT syntax (`GB928371940`) instead of German `DE` USt-IdNr. | **PENDING_ACTION**<br>*(Risk: 30/100)* | **Tax ID Syntax Mismatch**: Automatically generates remediation notice requesting German VAT. |
| **🟡 Edge Case 3: Missing Cross-Border SWIFT** | Japanese supplier (`Tokyo Automation Works K.K.`) requesting international wire disbursements but omitted mandatory SWIFT/BIC code. | **PENDING_ACTION**<br>*(Risk: 25/100)* | **Cross-Border Banking**: International wires require ISO 9362 SWIFT code. Generates targeted instructions. |
| **🟣 Edge Case 4: Shell Entity / Sanctions Hit** | Offshore maritime entity (`Sovereign Maritime Trading FZE`) whose principal matches OFAC/SDN global watchlist target. | **REJECTED**<br>*(Risk: 100/100)* | **Direct Watchlist Hit**: SDN match + Sanctioned jurisdiction freeze. Escalated to Senior Compliance Officer. |

---

## 🚀 Quickstart & Setup

### 🌐 Live Cloudflare Deployment (Zero Setup)
Experience the full interactive application directly in your browser:  
👉 **[https://zamp-vendor-onboarding.pages.dev/](https://zamp-vendor-onboarding.pages.dev/)**

---

### Local Installation & Run

#### Prerequisites
- Python 3.10+
- `uv` package manager

#### 1. Launch with `uv`
```bash
# Run web server directly
uv run python run.py
```
Open your browser to:
👉 **http://127.0.0.1:8000**  
(Interactive API Documentation available at `http://127.0.0.1:8000/docs`)

#### 2. Headless CLI Mode
You can also run any preset directly in your terminal:
```bash
uv run python run.py --cli --preset happy_path
uv run python run.py --cli --preset name_mismatch
uv run python run.py --cli --preset tax_country_mismatch
uv run python run.py --cli --preset missing_crossborder_swift
uv run python run.py --cli --preset sanctions_watchlist_hit
```

#### 3. Run Automated Tests
```bash
uv run python -m unittest tests/test_pipeline.py
```

