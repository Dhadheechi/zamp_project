#!/usr/bin/env python3
import sys
import uvicorn
import argparse
from app.data.presets import PRESETS
from app.models.schemas import VendorSubmission
from app.pipeline.validator import VendorOnboardingPipeline

def run_server(port: int = 8000, host: str = "127.0.0.1"):
    print("=" * 65)
    print(" 🚀 Zamp AI Solutions Analyst — Vendor Onboarding Engine")
    print(f" 🌐 Web Dashboard: http://{host}:{port}")
    print(f" 📖 API Documentation: http://{host}:{port}/docs")
    print("=" * 65)
    uvicorn.run("app.main:app", host=host, port=port, reload=True)

def run_cli_test(preset_key: str = "happy_path"):
    if preset_key not in PRESETS:
        print(f"Error: Unknown preset '{preset_key}'. Available: {list(PRESETS.keys())}")
        sys.exit(1)

    preset = PRESETS[preset_key]
    print(f"\n[CLI EVALUATION] Running preset: {preset['title']}")
    print(f"Description: {preset['description']}\n")

    pipeline = VendorOnboardingPipeline()
    submission = VendorSubmission(**preset["data"])
    decision = pipeline.evaluate(submission)

    print("=" * 60)
    print(f"STATUS:     {decision.status}")
    print(f"RISK SCORE: {decision.risk_score} / 100")
    print(f"LATENCY:    {decision.total_duration_ms} ms")
    print(f"REASONING:  {decision.summary_reasoning}")
    print("=" * 60)
    print("\nSTAGE BREAKDOWN:")
    for stage in decision.stages:
        status_symbol = "✓" if stage.status == "PASSED" else ("⚠" if stage.status == "WARNING" else "✕")
        print(f"  {status_symbol} {stage.stage_name} ({stage.duration_ms} ms) -> {stage.status}")
        for check in stage.rule_checks:
            check_sym = "  [PASS]" if check.passed else f"  [{check.severity}]"
            print(f"     {check_sym} {check.rule_name}: {check.message}")

    if decision.vendor_communication:
        comm = decision.vendor_communication
        print("\n" + "-" * 60)
        print("ACTIONABLE VENDOR REMEDIATION NOTICE:")
        print(f"To:      {comm.recipient}")
        print(f"Subject: {comm.subject}\n")
        print(comm.body_summary)
        print("\nAction items needed:")
        for a in comm.action_items:
            print(f"  • {a}")
        print("-" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Zamp Vendor Onboarding Automated Verification Engine")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode instead of web server")
    parser.add_argument("--preset", default="happy_path", choices=list(PRESETS.keys()), help="Preset to run in CLI mode")
    parser.add_argument("--port", type=int, default=8000, help="Web server port (default: 8000)")
    parser.add_argument("--host", default="127.0.0.1", help="Web server host (default: 127.0.0.1)")

    args = parser.parse_args()

    if args.cli:
        run_cli_test(args.preset)
    else:
        run_server(port=args.port, host=args.host)

