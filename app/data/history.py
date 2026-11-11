import json
import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from app.models.schemas import RunRecord, EvaluationDecision, VendorSubmission

HISTORY_FILE = "runs_history.json"
IST_TZ = timezone(timedelta(hours=5, minutes=30))

class RunHistoryManager:
    def __init__(self, filepath: str = HISTORY_FILE):
        self.filepath = filepath
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump([], f)

    def record_run(self, submission: VendorSubmission, decision: EvaluationDecision) -> RunRecord:
        now_utc = datetime.now(timezone.utc)
        now_ist = now_utc.astimezone(IST_TZ)
        record = RunRecord(
            run_id=f"RUN-{uuid.uuid4().hex[:8].upper()}",
            submission_id=submission.submission_id,
            timestamp=now_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
            timestamp_ist=now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
            company_name=submission.company.legal_name,
            country_code=submission.company.country_code,
            status=decision.status,
            risk_score=decision.risk_score,
            duration_ms=decision.total_duration_ms,
            summary=decision.summary_reasoning,
            decision=decision
        )

        history = self.get_all_runs()
        # Prepend newest first
        history.insert(0, record.model_dump())
        
        # Keep maximum 50 recent runs
        history = history[:50]

        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

        return record

    def get_all_runs(self) -> List[Dict[str, Any]]:
        self._ensure_file()
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def get_metrics(self) -> Dict[str, Any]:
        runs = self.get_all_runs()
        total = len(runs)
        if total == 0:
            return {
                "total_runs": 0,
                "approved_count": 0,
                "approved_rate": "0%",
                "pending_count": 0,
                "pending_rate": "0%",
                "rejected_count": 0,
                "rejected_rate": "0%",
                "avg_duration_ms": 0.0,
                "avg_risk_score": 0
            }

        approved = sum(1 for r in runs if r.get("status") == "APPROVED")
        pending = sum(1 for r in runs if r.get("status") == "PENDING_ACTION")
        rejected = sum(1 for r in runs if r.get("status") == "REJECTED")
        avg_dur = sum(r.get("duration_ms", 0) for r in runs) / total
        avg_risk = sum(r.get("risk_score", 0) for r in runs) / total

        return {
            "total_runs": total,
            "approved_count": approved,
            "approved_rate": f"{round((approved / total) * 100, 1)}%",
            "pending_count": pending,
            "pending_rate": f"{round((pending / total) * 100, 1)}%",
            "rejected_count": rejected,
            "rejected_rate": f"{round((rejected / total) * 100, 1)}%",
            "avg_duration_ms": round(avg_dur, 2),
            "avg_risk_score": round(avg_risk, 1)
        }

    def clear_history(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump([], f)
