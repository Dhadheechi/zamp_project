import os
import io
import csv
import json
from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.models.schemas import VendorSubmission, EvaluationDecision, CompanyProfile, BankingInfo, ComplianceDocs
from app.pipeline.validator import VendorOnboardingPipeline
from app.data.presets import PRESETS, get_preset_list
from app.data.history import RunHistoryManager

app = FastAPI(
    title="Zamp AI Solutions Analyst - Vendor Onboarding Engine",
    description="Automated, explainable vendor onboarding verification pipeline with stage-by-stage execution and actionable vendor communication.",
    version="1.0.0"
)

templates = Jinja2Templates(directory="app/templates")
pipeline = VendorOnboardingPipeline()
history_manager = RunHistoryManager()

def parse_csv_row_to_submission(row: dict, index: int) -> VendorSubmission:
    return VendorSubmission(
        submission_id=f"CSV-{index+1:03d}-{row.get('country_code', 'XX').strip().upper()}",
        company=CompanyProfile(
            legal_name=row.get("legal_name", "").strip(),
            dba_name=row.get("dba_name", "").strip() or None,
            country_code=row.get("country_code", "US").strip().upper(),
            business_address=row.get("business_address", "Address from CSV import"),
            business_type=row.get("business_type", "Corporation"),
            tax_id=row.get("tax_id", "").strip(),
            tax_id_type=row.get("tax_id_type", "EIN").strip(),
            contact_name=row.get("contact_name", "Vendor Accounts").strip(),
            contact_email=row.get("contact_email", "billing@vendor.com").strip(),
            contact_phone=row.get("contact_phone", None),
            website=row.get("website", None)
        ),
        banking=BankingInfo(
            bank_name=row.get("bank_name", "").strip(),
            bank_country=row.get("bank_country", row.get("country_code", "US")).strip().upper(),
            account_holder_name=row.get("account_holder_name", "").strip(),
            account_number_or_iban=row.get("account_number_or_iban", "").strip(),
            routing_or_sort_code=row.get("routing_or_sort_code", "").strip() or None,
            swift_bic=row.get("swift_bic", "").strip() or None,
            currency=row.get("currency", "USD").strip(),
            account_type=row.get("account_type", "Corporate Checking").strip()
        ),
        compliance=ComplianceDocs(
            tax_document_attached=str(row.get("tax_doc", "true")).strip().lower() in ("true", "1", "yes"),
            bank_statement_attached=str(row.get("bank_doc", "true")).strip().lower() in ("true", "1", "yes"),
            certificate_of_incorporation=str(row.get("incorp_doc", "true")).strip().lower() in ("true", "1", "yes"),
            pep_sanctions_declared_clear=str(row.get("pep_clear", "true")).strip().lower() in ("true", "1", "yes")
        )
    )

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "presets": get_preset_list(),
            "metrics": history_manager.get_metrics(),
            "recent_runs": history_manager.get_all_runs()[:10]
        }
    )

@app.get("/api/presets")
async def list_presets():
    return JSONResponse(content=get_preset_list())

@app.get("/api/presets/{preset_id}")
async def get_preset(preset_id: str):
    if preset_id not in PRESETS:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")
    return JSONResponse(content=PRESETS[preset_id])

@app.post("/api/evaluate")
async def evaluate_submission(submission: VendorSubmission):
    try:
        decision = pipeline.evaluate(submission)
        record = history_manager.record_run(submission, decision)
        return JSONResponse(content={
            "run_id": record.run_id,
            "decision": decision.model_dump(),
            "metrics": history_manager.get_metrics()
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/evaluate/csv")
async def evaluate_csv(file: UploadFile = File(...)):
    try:
        content = await file.read()
        text = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        
        batch_results = []
        for idx, row in enumerate(reader):
            if not row.get("legal_name"):
                continue
            sub = parse_csv_row_to_submission(row, idx)
            dec = pipeline.evaluate(sub)
            rec = history_manager.record_run(sub, dec)
            batch_results.append({
                "run_id": rec.run_id,
                "company_name": sub.company.legal_name,
                "country": sub.company.country_code,
                "status": dec.status,
                "risk_score": dec.risk_score,
                "summary": dec.summary_reasoning
            })

        return JSONResponse(content={
            "total_processed": len(batch_results),
            "batch_results": batch_results,
            "metrics": history_manager.get_metrics()
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process CSV: {str(e)}")

@app.get("/api/history")
async def get_history():
    return JSONResponse(content=history_manager.get_all_runs())

@app.get("/api/metrics")
async def get_metrics():
    return JSONResponse(content=history_manager.get_metrics())

@app.post("/api/history/clear")
async def clear_history():
    history_manager.clear_history()
    return JSONResponse(content={"status": "cleared", "metrics": history_manager.get_metrics()})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
