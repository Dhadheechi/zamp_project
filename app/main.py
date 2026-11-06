import os
import json
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.models.schemas import VendorSubmission, EvaluationDecision
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
