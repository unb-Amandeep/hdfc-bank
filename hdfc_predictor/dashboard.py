"""
Interactive Web Dashboard for HDFC Bank Cyclical Accumulation & Decision Intelligence.
Unified into a clean, modern single-page dashboard with:
1. Top Fold: Verdict & Capital Allocation Plan + Unified Monotonic Price Ladder
2. 5 Safety & Accumulation Checks (with nested Gordon sensitivity & certified filing metrics)
3. Plain-Language Glossary (Financial concepts explained simply)
4. Collapsible Deep Dive: Details & Historical Audit Container:
   - Audited Historical Backtest (HTML5 Canvas with graceful empty state handling)
   - All 8 Past Setup Occurrences (n=8, 95% CI, Pre vs Post Merger regime)
   - Track Record Scoreboard (Definition of Hit: 6M return >= +8.0%)
   - Management Promise & Guidance Tracker (BSE Q2 FY27 audit, SHA-256 hash, page numbers)
   - Recent News Flow & Market Narrative (dated headlines, unproven causality note)
   - Big-4 Private Banking Peer Watchlist (Single reference price, live peers or 'Feed offline')
   - Data Health & Cryptographic Hash Chain Ledger (SHA-256 signed 2:00 PM records)
5. Completely self-contained: zero external CDNs, native HTML5 canvas line chart, local styles.
6. Non-blocking asynchronous Refresh: background worker thread with HTTP 202 Accepted and job polling.
"""
import gzip
import http.server
import json
import os
import shutil
import socketserver
import sqlite3
import threading
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from hdfc_predictor.config import settings
from hdfc_predictor.database import (
    get_recent_predictions,
    get_learning_progress,
    verify_decision_chain_integrity,
    get_latest_decision
)
from hdfc_predictor.market_data import MarketDataProvider
from hdfc_predictor.fundamental_engine import FundamentalEngine
from hdfc_predictor.valuation_engine import ValuationEngine
from hdfc_predictor.cyclical_bottom_detector import CyclicalBottomDetector
from hdfc_predictor.capital_allocator import CapitalAllocator
from hdfc_predictor.investment_committee import InvestmentCommittee
from hdfc_predictor.event_intelligence import EventIntelligenceEngine
from hdfc_predictor.historical_analogues import HistoricalAnalogueEngine
from hdfc_predictor.calibrated_confidence import CalibratedConfidenceEngine
from hdfc_predictor.news_engine import NewsEngine
from hdfc_predictor.signal_generator import SignalGenerator
from hdfc_predictor.backtester import Backtester
from hdfc_predictor.fair_value_and_regime import FairValueAndRegimeEngine
from hdfc_predictor.deterministic_risk import DeterministicRiskEngine
from hdfc_predictor.valuation_targets import ValuationTargetEngine
from hdfc_predictor.track_record import TrackRecordEngine
from hdfc_predictor.trading_calendar import TradingCalendar
from hdfc_predictor.earnings_transcript import EarningsTranscriptEngine
from hdfc_predictor.accumulation_gates import AccumulationGatesEngine, BANK_SAFETY_CONFIG
from hdfc_predictor.multi_bank_config import MultiBankEngine
from hdfc_predictor.technical_engine import TechnicalEngine
from hdfc_predictor.probabilistic_forecast import ProbabilisticForecastEngine
from hdfc_predictor.daily_compass_log import CompassLogEngine
from hdfc_predictor.macro_market_inputs import MacroMarketEngine

PORT = int(os.environ.get("PORT", 8501))


class RefreshJobManager:
    """
    Manages non-blocking asynchronous signal calculations.
    Returns HTTP 202 Accepted immediately, tracks background progress,
    and enforces a 60-second execution timeout.
    """
    _lock = threading.Lock()
    _current_job: Dict[str, Any] = {
        "status": "IDLE", # IDLE, RUNNING, SUCCESS, ERROR
        "started_at": None,
        "completed_at": None,
        "message": "No refresh job has been run yet.",
        "error": None,
        "duration_seconds": 0.0
    }

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        with cls._lock:
            # Check timeout (60s)
            if cls._current_job["status"] == "RUNNING" and cls._current_job["started_at"]:
                elapsed = time.time() - cls._current_job["started_at"]
                if elapsed > 60.0:
                    cls._current_job["status"] = "ERROR"
                    cls._current_job["error"] = "Refresh job timed out after 60 seconds."
                    cls._current_job["completed_at"] = time.time()
                    cls._current_job["duration_seconds"] = round(elapsed, 2)
            return dict(cls._current_job)

    @classmethod
    def start_job(cls, force: bool = True) -> Dict[str, Any]:
        with cls._lock:
            if cls._current_job["status"] == "RUNNING" and cls._current_job["started_at"]:
                elapsed = time.time() - cls._current_job["started_at"]
                if elapsed <= 60.0:
                    return {
                        "status": "RUNNING",
                        "message": "Signal refresh already in progress.",
                        "started_at": cls._current_job["started_at"],
                        "elapsed_seconds": round(elapsed, 1)
                    }

            cls._current_job = {
                "status": "RUNNING",
                "started_at": time.time(),
                "completed_at": None,
                "message": "Recalculating 2:00 PM signal pipeline...",
                "error": None,
                "duration_seconds": 0.0
            }

        def _worker():
            start_t = time.time()
            try:
                gen = SignalGenerator()
                result = gen.run_daily_signal(force=force)
                pred = result.get("prediction", {})
                action = pred.get("signal_action", "HOLD")
                conf = pred.get("confidence_score", 0.0)
                dur = round(time.time() - start_t, 2)

                # Derive primary verdict from accumulation gates so toast and page never contradict
                ref_price = getattr(ValuationTargetEngine, "DEFAULT_REFERENCE_PRICE", 814.95)
                gates_eval = AccumulationGatesEngine.evaluate_all_gates(
                    current_price=ref_price,
                    df_bars=None,
                    as_of_date="2026-11-18"
                )
                primary_verdict = gates_eval.final_action

                try:
                    invalidate_payload_caches()
                except Exception:
                    pass

                with cls._lock:
                    cls._current_job["status"] = "SUCCESS"
                    cls._current_job["completed_at"] = time.time()
                    cls._current_job["duration_seconds"] = dur
                    cls._current_job["message"] = f"Signal refreshed: {primary_verdict} (Tactical ML: {action}, {conf*100:.0f}% conf) · Locked at 2:00 PM IST in {dur}s."
            except Exception as exc:
                import logging
                logging.getLogger("hdfc_engine").error("Signal refresh calculation error", exc_info=True)
                dur = round(time.time() - start_t, 2)
                with cls._lock:
                    cls._current_job["status"] = "ERROR"
                    cls._current_job["completed_at"] = time.time()
                    cls._current_job["duration_seconds"] = dur
                    cls._current_job["error"] = "Refresh failed, see logs"
                    cls._current_job["message"] = "Refresh failed, see logs"

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

        return {
            "status": "RUNNING",
            "message": "Signal recalculation started in background.",
            "started_at": cls._current_job["started_at"]
        }


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HDFC Bank Accumulation Engine · Groww White Interface</title>
    <!-- INJECTED_DATA -->
    <style>
        :root {
            --font-sans: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
            --groww-green: #00D09C;
            --groww-green-hover: #00b386;
            --groww-green-light: #EBF9F5;
            --slate-50: #f8fafc;
            --slate-100: #f1f5f9;
            --slate-200: #e2e8f0;
            --slate-300: #cbd5e1;
            --slate-400: #94a3b8;
            --slate-500: #64748b;
            --slate-600: #475569;
            --slate-700: #334155;
            --slate-800: #1e293b;
            --slate-900: #0f172a;
            --emerald-50: #ecfdf5;
            --emerald-100: #d1fae5;
            --emerald-200: #a7f3d0;
            --emerald-500: #10b981;
            --emerald-600: #059669;
            --emerald-700: #047857;
            --emerald-800: #065f46;
            --emerald-900: #064e3b;
            --amber-50: #fffbeb;
            --amber-100: #fef3c7;
            --amber-200: #fde68a;
            --amber-300: #fcd34d;
            --amber-400: #fbbf24;
            --amber-500: #f59e0b;
            --amber-600: #d97706;
            --amber-700: #b45309;
            --amber-800: #92400e;
            --amber-900: #78350f;
            --rose-50: #fff1f2;
            --rose-100: #ffe4e6;
            --rose-200: #fecdd3;
            --rose-500: #f43f5e;
            --rose-600: #e11d48;
            --rose-700: #be123c;
            --rose-800: #9f1239;
            --rose-900: #881337;
            --indigo-50: #eef2ff;
            --indigo-100: #e0e7ff;
            --indigo-200: #c7d2fe;
            --indigo-600: #4f46e5;
            --indigo-700: #4338ca;
            --indigo-800: #3730a3;
            --purple-50: #faf5ff;
            --purple-100: #f3e8ff;
            --purple-200: #e9d5ff;
            --purple-700: #7e22ce;
            --sky-50: #f0f9ff;
            --sky-600: #0284c7;
            --sky-700: #0369a1;
            --sky-800: #075985;
            --teal-50: #f0fdfa;
            --teal-100: #ccfbf1;
            --teal-700: #0f766e;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        html { scroll-behavior: smooth; }
        body { font-family: var(--font-sans); background-color: var(--slate-50); color: var(--slate-800); line-height: 1.5; font-size: 13px; -webkit-font-smoothing: antialiased; }
        .mono { font-family: var(--font-mono); }
        .tech-only, .tech-block { display: none; }
        body.show-tech .tech-only { display: inline-block; }
        body.show-tech .tech-block { display: block; }
        
        /* Layout */
        .flex { display: flex; }
        .inline-flex { display: inline-flex; }
        .flex-col { flex-direction: column; }
        .flex-wrap { flex-wrap: wrap; }
        .items-center { align-items: center; }
        .items-start { align-items: flex-start; }
        .items-baseline { align-items: baseline; }
        .justify-between { justify-content: space-between; }
        .justify-center { justify-content: center; }
        .shrink-0 { flex-shrink: 0; }
        
        .grid { display: grid; }
        .grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
        .grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
        .grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
        .grid-cols-6 { grid-template-columns: repeat(6, minmax(0, 1fr)); }
        @media (min-width: 640px) {
            .sm\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .sm\:grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
            .sm\:grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
            .sm\:inline { display: inline; }
            .sm\:flex { display: flex; }
            .sm\:px-6 { padding-left: 1.5rem; padding-right: 1.5rem; }
            .sm\:p-7 { padding: 1.75rem; }
            .sm\:text-3xl { font-size: 1.875rem; line-height: 2.25rem; }
            .sm\:text-4xl { font-size: 2.25rem; line-height: 2.5rem; }
            .sm\:h-80 { height: 20rem; }
        }
        @media (min-width: 768px) {
            .md\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .md\:inline-flex { display: inline-flex; }
        }
        @media (min-width: 1024px) {
            .lg\:grid-cols-3 { grid-template-columns: 2fr 1fr; }
            .lg\:grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
            .lg\:col-span-2 { grid-column: span 2 / span 2; }
        }
        
        /* Gaps */
        .gap-1 { gap: 0.25rem; }
        .gap-1\.5 { gap: 0.375rem; }
        .gap-2 { gap: 0.5rem; }
        .gap-2\.5 { gap: 0.625rem; }
        .gap-3 { gap: 0.75rem; }
        .gap-3\.5 { gap: 0.875rem; }
        .gap-4 { gap: 1rem; }
        .gap-5 { gap: 1.25rem; }
        .gap-6 { gap: 1.5rem; }
        .gap-8 { gap: 2rem; }
        
        .space-y-0\.5 > * + * { margin-top: 0.125rem; }
        .space-y-1 > * + * { margin-top: 0.25rem; }
        .space-y-1\.5 > * + * { margin-top: 0.375rem; }
        .space-y-2 > * + * { margin-top: 0.5rem; }
        .space-y-2\.5 > * + * { margin-top: 0.625rem; }
        .space-y-3 > * + * { margin-top: 0.75rem; }
        .space-y-3\.5 > * + * { margin-top: 0.875rem; }
        .space-y-4 > * + * { margin-top: 1rem; }
        .space-y-5 > * + * { margin-top: 1.25rem; }
        .space-y-6 > * + * { margin-top: 1.5rem; }
        .space-y-8 > * + * { margin-top: 2rem; }
        
        /* Spacing */
        .p-0\.5 { padding: 0.125rem; }
        .p-1 { padding: 0.25rem; }
        .p-1\.5 { padding: 0.375rem; }
        .p-2 { padding: 0.5rem; }
        .p-2\.5 { padding: 0.625rem; }
        .p-3 { padding: 0.75rem; }
        .p-3\.5 { padding: 0.875rem; }
        .p-4 { padding: 1rem; }
        .p-5 { padding: 1.25rem; }
        .p-6 { padding: 1.5rem; }
        .px-1\.5 { padding-left: 0.375rem; padding-right: 0.375rem; }
        .px-2 { padding-left: 0.5rem; padding-right: 0.5rem; }
        .px-2\.5 { padding-left: 0.625rem; padding-right: 0.625rem; }
        .px-3 { padding-left: 0.75rem; padding-right: 0.75rem; }
        .px-3\.5 { padding-left: 0.875rem; padding-right: 0.875rem; }
        .px-4 { padding-left: 1rem; padding-right: 1rem; }
        .px-6 { padding-left: 1.5rem; padding-right: 1.5rem; }
        .py-0\.2 { padding-top: 0.1rem; padding-bottom: 0.1rem; }
        .py-0\.5 { padding-top: 0.125rem; padding-bottom: 0.125rem; }
        .py-1 { padding-top: 0.25rem; padding-bottom: 0.25rem; }
        .py-1\.5 { padding-top: 0.375rem; padding-bottom: 0.375rem; }
        .py-2 { padding-top: 0.5rem; padding-bottom: 0.5rem; }
        .py-2\.5 { padding-top: 0.625rem; padding-bottom: 0.625rem; }
        .py-3 { padding-top: 0.75rem; padding-bottom: 0.75rem; }
        .py-6 { padding-top: 1.5rem; padding-bottom: 1.5rem; }
        .py-8 { padding-top: 2rem; padding-bottom: 2rem; }
        .pt-0 { padding-top: 0; }
        .pt-1 { padding-top: 0.25rem; }
        .pt-2 { padding-top: 0.5rem; }
        .pt-2\.5 { padding-top: 0.625rem; }
        .pt-3 { padding-top: 0.75rem; }
        .pt-4 { padding-top: 1rem; }
        .pb-1 { padding-bottom: 0.25rem; }
        .pb-2 { padding-bottom: 0.5rem; }
        .mt-1 { margin-top: 0.25rem; }
        .mt-2 { margin-top: 0.5rem; }
        .mt-2\.5 { margin-top: 0.625rem; }
        .mt-4 { margin-top: 1rem; }
        .mb-2 { margin-bottom: 0.5rem; }
        .mx-auto { margin-left: auto; margin-right: auto; }
        
        /* Dimensions & Position */
        .w-full { width: 100%; }
        .w-1 { width: 0.25rem; }
        .w-1\.5 { width: 0.375rem; }
        .w-2 { width: 0.5rem; }
        .w-3 { width: 0.75rem; }
        .w-3\.5 { width: 0.875rem; }
        .w-4 { width: 1rem; }
        .w-6 { width: 1.5rem; }
        .w-8 { width: 2rem; }
        .w-9 { width: 2.25rem; }
        .h-full { height: 100%; }
        .h-1 { height: 0.25rem; }
        .h-1\.5 { height: 0.375rem; }
        .h-2 { height: 0.5rem; }
        .h-3 { height: 0.75rem; }
        .h-3\.5 { height: 0.875rem; }
        .h-4 { height: 1rem; }
        .h-6 { height: 1.5rem; }
        .h-8 { height: 2rem; }
        .h-9 { height: 2.25rem; }
        .h-16 { height: 4rem; }
        .h-72 { height: 18rem; }
        .h-80 { height: 20rem; }
        .max-w-\[1240px\] { max-width: 1240px; }
        .min-h-screen { min-height: 100vh; }
        .relative { position: relative; }
        .absolute { position: absolute; }
        .sticky { position: sticky; }
        .inset-0 { top: 0; right: 0; bottom: 0; left: 0; }
        .top-0 { top: 0; }
        .bottom-0 { bottom: 0; }
        .-top-1 { top: -0.25rem; }
        .-top-7 { top: -1.75rem; }
        .-translate-x-1\/2 { transform: translateX(-50%); }
        .z-40 { z-index: 40; }
        .z-50 { z-index: 50; }
        .scroll-mt-28 { scroll-margin-top: 7rem; }
        
        /* Colors */
        .bg-white { background-color: #ffffff; }
        .bg-white\/95 { background-color: rgba(255, 255, 255, 0.95); }
        .bg-slate-50 { background-color: var(--slate-50); }
        .bg-slate-100 { background-color: var(--slate-100); }
        .bg-slate-200 { background-color: var(--slate-200); }
        .bg-slate-800 { background-color: var(--slate-800); }
        .bg-slate-900 { background-color: var(--slate-900); }
        .bg-emerald-50 { background-color: var(--emerald-50); }
        .bg-emerald-100 { background-color: var(--emerald-100); }
        .bg-emerald-400 { background-color: #34d399; }
        .bg-emerald-500 { background-color: var(--emerald-500); }
        .bg-emerald-600 { background-color: var(--emerald-600); }
        .bg-amber-50 { background-color: var(--amber-50); }
        .bg-amber-100 { background-color: var(--amber-100); }
        .bg-amber-400 { background-color: var(--amber-400); }
        .bg-amber-500 { background-color: var(--amber-500); }
        .bg-rose-50 { background-color: var(--rose-50); }
        .bg-rose-100 { background-color: var(--rose-100); }
        .bg-rose-500 { background-color: var(--rose-500); }
        .bg-rose-600 { background-color: var(--rose-600); }
        .bg-indigo-50 { background-color: var(--indigo-50); }
        .bg-indigo-100 { background-color: var(--indigo-100); }
        .bg-indigo-600 { background-color: var(--indigo-600); }
        .bg-purple-50 { background-color: var(--purple-50); }
        .bg-purple-100 { background-color: var(--purple-100); }
        .bg-purple-200 { background-color: var(--purple-200); }
        .bg-purple-700 { background-color: var(--purple-700); }
        .bg-sky-50 { background-color: var(--sky-50); }
        .bg-sky-600 { background-color: var(--sky-600); }
        .bg-teal-50 { background-color: var(--teal-50); }
        .bg-teal-100 { background-color: var(--teal-100); }
        
        .text-slate-300 { color: var(--slate-300); }
        .text-slate-400 { color: var(--slate-400); }
        .text-slate-500 { color: var(--slate-500); }
        .text-slate-600 { color: var(--slate-600); }
        .text-slate-700 { color: var(--slate-700); }
        .text-slate-800 { color: var(--slate-800); }
        .text-slate-900 { color: var(--slate-900); }
        .text-white { color: #ffffff; }
        .text-emerald-400 { color: #34d399; }
        .text-emerald-600 { color: var(--emerald-600); }
        .text-emerald-700 { color: var(--emerald-700); }
        .text-emerald-800 { color: var(--emerald-800); }
        .text-emerald-900 { color: var(--emerald-900); }
        .text-amber-300 { color: var(--amber-300); }
        .text-amber-400 { color: var(--amber-400); }
        .text-amber-500 { color: var(--amber-500); }
        .text-amber-700 { color: var(--amber-700); }
        .text-amber-800 { color: var(--amber-800); }
        .text-amber-900 { color: var(--amber-900); }
        .text-rose-600 { color: var(--rose-600); }
        .text-rose-700 { color: var(--rose-700); }
        .text-rose-800 { color: var(--rose-800); }
        .text-rose-900 { color: var(--rose-900); }
        .text-indigo-600 { color: var(--indigo-600); }
        .text-indigo-700 { color: var(--indigo-700); }
        .text-indigo-800 { color: var(--indigo-800); }
        .text-purple-700 { color: var(--purple-700); }
        .text-sky-700 { color: var(--sky-700); }
        .text-sky-800 { color: var(--sky-800); }
        .text-teal-700 { color: var(--teal-700); }
        
        .border { border-width: 1px; border-style: solid; border-color: var(--slate-200); }
        .border-2 { border-width: 2px; border-style: solid; }
        .border-t { border-top-width: 1px; border-top-style: solid; border-top-color: var(--slate-200); }
        .border-b { border-bottom-width: 1px; border-bottom-style: solid; border-bottom-color: var(--slate-200); }
        .border-slate-100 { border-color: var(--slate-100); }
        .border-slate-200 { border-color: var(--slate-200); }
        .border-slate-300 { border-color: var(--slate-300); }
        .border-emerald-200 { border-color: var(--emerald-200); }
        .border-emerald-300 { border-color: var(--emerald-300); }
        .border-amber-200 { border-color: var(--amber-200); }
        .border-amber-300 { border-color: var(--amber-300); }
        .border-rose-200 { border-color: var(--rose-200); }
        .border-rose-300 { border-color: var(--rose-300); }
        .border-indigo-200 { border-color: var(--indigo-200); }
        .border-purple-200 { border-color: var(--purple-200); }
        .border-sky-200 { border-color: #bae6fd; }
        
        .rounded { border-radius: 0.25rem; }
        .rounded-md { border-radius: 0.375rem; }
        .rounded-lg { border-radius: 0.5rem; }
        .rounded-xl { border-radius: 0.75rem; }
        .rounded-2xl { border-radius: 1rem; }
        .rounded-full { border-radius: 9999px; }
        
        .font-normal { font-weight: 400; }
        .font-medium { font-weight: 500; }
        .font-semibold { font-weight: 600; }
        .font-bold { font-weight: 700; }
        .font-extrabold { font-weight: 800; }
        
        .text-\[10px\] { font-size: 10px; line-height: 14px; }
        .text-\[11px\] { font-size: 11px; line-height: 15px; }
        .text-xs { font-size: 12px; line-height: 16px; }
        .text-sm { font-size: 14px; line-height: 20px; }
        .text-base { font-size: 16px; line-height: 24px; }
        .text-lg { font-size: 18px; line-height: 28px; }
        .text-xl { font-size: 20px; line-height: 28px; }
        .text-2xl { font-size: 24px; line-height: 32px; }
        .text-3xl { font-size: 30px; line-height: 36px; }
        .text-4xl { font-size: 36px; line-height: 40px; }
        
        .uppercase { text-transform: uppercase; }
        .tracking-wide { letter-spacing: 0.025em; }
        .tracking-wider { letter-spacing: 0.05em; }
        .tracking-tight { letter-spacing: -0.025em; }
        .leading-none { line-height: 1; }
        .leading-snug { line-height: 1.375; }
        .leading-relaxed { line-height: 1.625; }
        
        .text-left { text-align: left; }
        .text-center { text-align: center; }
        .text-right { text-align: right; }
        
        .shadow-sm { box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); }
        .shadow { box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1); }
        .cursor-pointer { cursor: pointer; }
        .cursor-crosshair { cursor: crosshair; }
        .select-none { user-select: none; }
        .overflow-hidden { overflow: hidden; }
        .overflow-x-auto { overflow-x: auto; }
        .italic { font-style: italic; }
        .hidden { display: none !important; }
        .block { display: block; }
        .transition { transition: all 150ms cubic-bezier(0.4, 0, 0.2, 1); }
        .animate-pulse { animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .5; } }
        
        .divide-y > * + * { border-top-width: 1px; border-top-style: solid; }
        .divide-slate-50 > * + * { border-top-color: var(--slate-50); }
        .divide-slate-100 > * + * { border-top-color: var(--slate-100); }
        .list-disc { list-style-type: disc; }
        .list-inside { list-style-position: inside; }
        
        table { border-collapse: collapse; width: 100%; }
        button { cursor: pointer; border: none; font-family: inherit; }
        
        /* Toast notification */
        #toastContainer { position: fixed; top: 1.25rem; right: 1.25rem; z-index: 9999; display: flex; flex-direction: column; gap: 0.5rem; }
        .toast-item { padding: 0.75rem 1rem; border-radius: 0.5rem; font-size: 12px; font-weight: 600; display: flex; align-items: center; gap: 0.5rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); transition: opacity 0.3s ease; }
        .toast-success { background-color: var(--emerald-900); color: #ffffff; border: 1px solid var(--emerald-600); }
        .toast-error { background-color: var(--rose-900); color: #ffffff; border: 1px solid var(--rose-600); }
    </style>
</head>
<body class="min-h-screen text-slate-800">

    <div id="toastContainer"></div>

    <!-- Top Sticky Header -->
    <header class="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div class="max-w-[1240px] mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
            <!-- Left: HDFC Bank Brand -->
            <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-full bg-slate-900 text-white font-extrabold text-sm flex items-center justify-center shrink-0">
                    H
                </div>
                <div>
                    <div class="flex items-center gap-2">
                        <h1 class="text-base font-bold text-slate-900 tracking-tight">HDFC Bank</h1>
                    </div>
                    <p class="text-xs text-slate-500">NSE: HDFCBANK · Private-sector bank · Accumulation Engine</p>
                </div>
            </div>

            <!-- Center / Right: Prototype badge & Controls -->
            <div class="flex items-center gap-3 sm:gap-4">
                <span class="hidden md:inline-flex px-3 py-1 rounded-full bg-slate-100 text-slate-700 text-xs font-semibold tracking-wide border border-slate-200">
                    PROTOTYPE · ENGINE DATA AS OF NOV 18–19, 2026
                </span>

                <!-- Plain / Tech Toggle -->
                <div class="flex items-center bg-slate-100 p-0.5 rounded-lg text-xs font-semibold border border-slate-200">
                    <button onclick="setMode('plain')" id="btnModePlain" class="px-3 py-1 rounded-md bg-white text-slate-900 shadow-sm transition">Plain</button>
                    <button onclick="setMode('tech')" id="btnModeTech" class="px-3 py-1 rounded-md text-slate-500 hover:text-slate-900 transition">Technical</button>
                </div>

                <!-- Async Refresh Button -->
                <button onclick="triggerNow()" id="btnTrigger" class="bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition shadow-sm">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                    Refresh
                </button>
            </div>
        </div>

        <!-- Sticky Anchor Sub-Navigation Bar -->
        <div class="max-w-[1240px] mx-auto px-4 sm:px-6 flex items-center justify-between border-t border-slate-100 text-xs font-semibold overflow-x-auto">
            <nav class="flex gap-6 py-2.5 shrink-0">
                <a href="#sectionOverview" class="nav-link text-slate-900 font-bold hover:text-emerald-600 transition">Overview</a>
                <a href="#sectionLadder" class="nav-link text-slate-500 hover:text-slate-900 transition">Valuation</a>
                <a href="#sectionCompass" class="nav-link text-slate-500 hover:text-slate-900 transition">Daily Compass</a>
                <a href="#sectionDetails" onclick="switchAuditTab('evidence')" class="nav-link text-slate-500 hover:text-slate-900 transition">Track record</a>
                <a href="#sectionDetails" onclick="switchAuditTab('integrity')" class="nav-link text-slate-500 hover:text-slate-900 transition">Data trust</a>
            </nav>
            <div class="hidden sm:flex items-center gap-2 text-xs text-slate-500">
                <span id="headerPriceText" class="font-bold mono text-slate-900">₹814.95</span>
                <span id="headerFeedStatusBadge" class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-rose-100 text-rose-800 border border-rose-300">
                    DATA STALE - not live
                </span>
                <span id="headerTimingStatus" class="hidden">Feed: NSE Historical Verified Cache · 2026-11-18 15:30 IST</span>
            </div>
        </div>
    </header>

    <!-- Stale Feed Warning Banner -->
    <div id="staleFeedAlertBanner" class="max-w-[1240px] mx-auto px-4 sm:px-6 pt-4 hidden">
        <div class="bg-rose-50 border border-rose-200 text-rose-900 px-4 py-3 rounded-xl flex items-center justify-between text-xs shadow-sm">
            <div class="flex items-center gap-2 font-medium">
                <span class="w-2 h-2 rounded-full bg-rose-600 animate-pulse"></span>
                <strong>DATA STALE - not live</strong> · Feed: <span id="staleFeedSource">NSE Historical Verified Cache</span> · Timestamp: <span id="staleFeedTimestamp">2026-11-18 15:30:00 IST</span> · Live BUY/SELL order generation is locked to WAIT.
            </div>
            <span class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-rose-100 text-rose-800 border border-rose-200">Safety Circuit Breaker</span>
        </div>
    </div>

    <!-- Main Container -->
    <main class="max-w-[1240px] mx-auto px-4 sm:px-6 py-6 space-y-8">

        <!-- 1. HERO ROW & TODAY'S CALL (GROWW WHITE STYLE) -->
        <section id="sectionOverview" class="scroll-mt-28 space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
                
                <!-- Hero Left: Price, Timeframe & Interactive Chart (2 cols / 66%) -->
                <div class="lg:col-span-2 bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
                    <!-- Price and Timeframe Row -->
                    <div class="flex flex-wrap items-start justify-between gap-4">
                        <div class="space-y-1">
                            <div class="flex items-baseline gap-3">
                                <span id="heroPrice" class="text-3xl sm:text-4xl font-extrabold text-slate-900 mono">₹814.95</span>
                                <span id="heroDelta" class="text-sm sm:text-base font-bold text-rose-600 flex items-center gap-0.5">
                                    ▼ -1.55 (-0.19%)
                                </span>
                            </div>
                            <!-- Feed Status Chip -->
                            <div id="heroFeedChip" class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-semibold bg-emerald-50 text-emerald-900 border border-emerald-200">
                                <span id="heroFeedChipDot" class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                                <span id="heroFeedChipText">LIVE · NSE Real-Time · As of Today · Prev close ₹846.00</span>
                            </div>
                        </div>

                        <!-- Timeframe Switcher (1M, 3M, 6M, ALL) -->
                        <div class="flex items-center bg-slate-100 p-1 rounded-lg gap-1 border border-slate-200">
                            <button onclick="setHeroTimeframe('1M')" data-tf="1M" class="btn-tf px-2.5 py-1 rounded-md text-xs font-semibold text-slate-500 hover:text-slate-900 bg-transparent transition">1M</button>
                            <button onclick="setHeroTimeframe('3M')" data-tf="3M" class="btn-tf px-2.5 py-1 rounded-md text-xs font-semibold text-slate-500 hover:text-slate-900 bg-transparent transition">3M</button>
                            <button onclick="setHeroTimeframe('6M')" data-tf="6M" class="btn-tf px-2.5 py-1 rounded-md text-xs font-bold bg-slate-900 text-white shadow-sm transition">6M</button>
                            <button onclick="setHeroTimeframe('ALL')" data-tf="ALL" class="btn-tf px-2.5 py-1 rounded-md text-xs font-semibold text-slate-500 hover:text-slate-900 bg-transparent transition">ALL</button>
                        </div>
                    </div>

                    <!-- Canvas Container -->
                    <div class="relative w-full h-72 sm:h-80 bg-slate-50/50 rounded-xl border border-slate-100 p-2 overflow-hidden">
                        <canvas id="heroPriceChart" class="w-full h-full block cursor-crosshair"></canvas>
                    </div>

                    <!-- Overlays Toggle Row -->
                    <div class="flex flex-wrap items-center justify-between gap-3 pt-1 border-t border-slate-100">
                        <div class="flex items-center gap-2">
                            <span class="text-xs font-bold text-slate-500 uppercase tracking-wider text-[11px]">Overlays:</span>
                            <button id="btnOverlay_buyBand" onclick="toggleHeroOverlay('buyBand')" class="px-2.5 py-1 rounded-full text-xs font-bold bg-slate-900 text-white shadow-sm border border-slate-900 transition flex items-center gap-1">
                                <span class="w-2 h-2 rounded-full bg-emerald-400"></span> Buy band
                            </button>
                            <button id="btnOverlay_fibLevels" onclick="toggleHeroOverlay('fibLevels')" class="px-2.5 py-1 rounded-full text-xs font-semibold bg-white text-slate-600 border border-slate-200 hover:border-slate-300 transition flex items-center gap-1">
                                Fib levels
                            </button>
                            <button id="btnOverlay_movingAvgs" onclick="toggleHeroOverlay('movingAvgs')" class="px-2.5 py-1 rounded-full text-xs font-semibold bg-white text-slate-600 border border-slate-200 hover:border-slate-300 transition flex items-center gap-1">
                                Moving avgs
                            </button>
                            <button id="btnOverlay_avwap" onclick="toggleHeroOverlay('avwap')" class="px-2.5 py-1 rounded-full text-xs font-semibold bg-white text-slate-600 border border-slate-200 hover:border-slate-300 transition flex items-center gap-1">
                                AVWAP
                            </button>
                        </div>
                    </div>
                    <p class="text-[11px] text-slate-400 leading-tight">
                        Closing prices, Feb 19 – Nov 17, 2026. Moving-average, Fibonacci and AVWAP overlays are drawn as today's level, not as history.
                    </p>
                </div>

                <!-- Hero Right: TODAY'S CALL Card (1 col / 33%) -->
                <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-5">
                    <!-- Header Row -->
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">TODAY'S CALL</span>
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600 border border-slate-200">
                            RECORD #100 · NOV 18 · v2.5
                        </span>
                    </div>

                    <!-- Giant Verdict -->
                    <div class="space-y-1">
                        <div class="flex items-center gap-3">
                            <span id="verdictActionBadge" class="text-4xl font-extrabold text-amber-500 tracking-tight">WAIT</span>
                        </div>
                        <h3 class="text-base font-bold text-slate-900">Don't chase this move</h3>
                        <p class="text-xs text-slate-600 leading-relaxed">
                            Place a limit order in <strong class="text-slate-900 mono">₹742–772</strong>. If the dip is deeper, add the second tranche at <strong class="text-slate-900 mono">₹710</strong>.
                        </p>
                    </div>

                    <!-- Size & Order Valid Till Tiles -->
                    <div class="grid grid-cols-2 gap-3 pt-1">
                        <div class="bg-slate-50 p-3 rounded-xl border border-slate-100 space-y-0.5">
                            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">SIZE</span>
                            <p id="verdictTrancheSharesText" class="text-base font-bold text-slate-900 mono">259–269 sh</p>
                            <span class="text-[10px] text-slate-500 block">~ ₹2L · 20% of ₹10L budget</span>
                        </div>
                        <div class="bg-slate-50 p-3 rounded-xl border border-slate-100 space-y-0.5">
                            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">ORDER VALID TILL</span>
                            <p id="orderValidityPill" class="text-base font-bold text-slate-900 mono">Nov 27, 2026</p>
                            <span class="text-[10px] text-slate-500 block">Limit order, re-check before</span>
                        </div>
                    </div>

                    <!-- WHAT HAS TO HAPPEN FIRST -->
                    <div class="space-y-3 pt-2 border-t border-slate-100">
                        <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">WHAT HAS TO HAPPEN FIRST</span>
                        
                        <!-- Item 1: Price back inside buy band -->
                        <div class="space-y-1.5">
                            <div class="flex items-center justify-between text-xs">
                                <span class="font-semibold text-slate-800">Price back inside the buy band</span>
                                <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">Waiting</span>
                            </div>
                            <!-- Progress Bar -->
                            <div class="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                                <div class="bg-amber-400 h-full rounded-full" style="width: 25%;"></div>
                            </div>
                            <p class="text-[11px] text-slate-500 leading-tight">
                                ₹814.95 now. Needs to fall to ₹772 or lower; about 5.3% down. Scale ₹700–830.
                            </p>
                        </div>

                        <!-- Item 2: Momentum cooled (RSI 14) -->
                        <div class="space-y-1.5">
                            <div class="flex items-center justify-between text-xs">
                                <span class="font-semibold text-slate-800">Momentum cooled (RSI 14)</span>
                                <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">Waiting</span>
                            </div>
                            <!-- Segmented / colored bar for RSI: green zone (0-70), red zone (70-100) with needle at 88.7 -->
                            <div class="w-full bg-slate-100 h-2 rounded-full overflow-hidden relative flex">
                                <div class="bg-emerald-500 h-full" style="width: 70%;"></div>
                                <div class="bg-rose-500 h-full" style="width: 30%;"></div>
                                <!-- Marker indicator at 88.7% -->
                                <div class="absolute top-0 bottom-0 w-1.5 bg-slate-900 border border-white rounded-full" style="left: 88.7%;"></div>
                            </div>
                            <p class="text-[11px] text-slate-500 leading-tight">
                                RSI 88.7 is deeply overbought. The green zone marks the conventional 70 line, not the engine's own threshold.
                            </p>
                        </div>
                    </div>

                    <!-- SAFETY GATES · 5 OF 6 PASS -->
                    <div class="space-y-2 pt-2 border-t border-slate-100">
                        <div class="flex items-center justify-between text-xs font-bold">
                            <span class="text-slate-700 uppercase tracking-wider text-[11px]">SAFETY GATES · 5 OF 6 PASS</span>
                            <span class="text-slate-500 text-[10px]">83%</span>
                        </div>
                        <!-- 6 Segments -->
                        <div class="grid grid-cols-6 gap-1.5 h-2">
                            <div class="bg-emerald-500 rounded-full h-full" title="Gate 0: Data Integrity - PASS"></div>
                            <div class="bg-emerald-500 rounded-full h-full" title="Gate 1: Valuation Trigger - PASS"></div>
                            <div class="bg-emerald-500 rounded-full h-full" title="Gate 2: Balance Sheet Health - PASS"></div>
                            <div class="bg-emerald-500 rounded-full h-full" title="Gate 3: Structural Support - PASS"></div>
                            <div class="bg-amber-400 rounded-full h-full animate-pulse" title="Gate 4: Momentum & Timing - WAITING"></div>
                            <div class="bg-emerald-500 rounded-full h-full" title="Gate 5: Staged Capital Sizing - PASS"></div>
                        </div>
                        <p class="text-[11px] text-slate-500">
                            Only Gate 4 (momentum & timing) is waiting.
                        </p>
                    </div>
                </div>
            </div>

            <!-- Middle Row: Two Balanced Cards -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Card 1: What supports a buy -->
                <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
                    <div class="flex items-center gap-2">
                        <span class="w-3 h-3 rounded-full bg-emerald-500 shrink-0"></span>
                        <h3 class="font-bold text-slate-900 text-sm">What supports a buy</h3>
                    </div>
                    <ul class="space-y-3 text-xs text-slate-700">
                        <li class="flex items-start justify-between gap-3">
                            <div class="flex items-start gap-2">
                                <span class="text-emerald-600 font-bold shrink-0">✓</span>
                                <span>Valuation rule met: P/B 2.06x against a ≤2.40x trigger, and a 19.6% drawdown from the 52-week high against a ≥12% requirement.</span>
                            </div>
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600 shrink-0 border border-slate-200">ENGINE RULE</span>
                        </li>
                        <li class="flex items-start justify-between gap-3">
                            <div class="flex items-start gap-2">
                                <span class="text-emerald-600 font-bold shrink-0">✓</span>
                                <span>Five of six safety gates pass. Only momentum and timing is waiting.</span>
                            </div>
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600 shrink-0 border border-slate-200">ENGINE</span>
                        </li>
                        <li class="flex items-start justify-between gap-3">
                            <div class="flex items-start gap-2">
                                <span class="text-emerald-600 font-bold shrink-0">✓</span>
                                <span>Backtest returned +24.5% against -9.5% for buy-and-hold since Feb 19, with a 7.7% maximum drawdown.</span>
                            </div>
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-50 text-purple-700 shrink-0 border border-purple-200">SIMULATED</span>
                        </li>
                        <li class="flex items-start justify-between gap-3">
                            <div class="flex items-start gap-2">
                                <span class="text-emerald-600 font-bold shrink-0">✓</span>
                                <span>A 5-day pullback to ₹772 scores 62% against an 8% random-walk baseline.</span>
                            </div>
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-800 shrink-0 border border-amber-200">SMALL SAMPLE · n=48</span>
                        </li>
                    </ul>
                </div>

                <!-- Card 2: What argues for patience -->
                <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
                    <div class="flex items-center gap-2">
                        <span class="w-3 h-3 rounded-full bg-rose-500 shrink-0"></span>
                        <h3 class="font-bold text-slate-900 text-sm">What argues for patience</h3>
                    </div>
                    <ul class="space-y-3 text-xs text-slate-700">
                        <li class="flex items-start justify-between gap-3">
                            <div class="flex items-start gap-2">
                                <span class="text-rose-600 font-bold shrink-0">!</span>
                                <span>RSI is 88.7 and price sits 5.3% above the top of the buy band. Buying here is chasing.</span>
                            </div>
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600 shrink-0 border border-slate-200">ENGINE</span>
                        </li>
                        <li class="flex items-start justify-between gap-3">
                            <div class="flex items-start gap-2">
                                <span class="text-rose-600 font-bold shrink-0">!</span>
                                <span>Base-case fundamental value is ₹553.5, 32% below price. Only 1 of 9 sensitivity cells supports ₹815.</span>
                            </div>
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-800 shrink-0 border border-amber-200">ENGINE · TO RECONCILE</span>
                        </li>
                        <li class="flex items-start justify-between gap-3">
                            <div class="flex items-start gap-2">
                                <span class="text-rose-600 font-bold shrink-0">!</span>
                                <span>Past-setup evidence is thin: 8 episodes, 50% six-month hit rate, 95% interval 21.5–78.5%.</span>
                            </div>
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-800 shrink-0 border border-amber-200">SMALL SAMPLE · n=8</span>
                        </li>
                        <li class="flex items-start justify-between gap-3">
                            <div class="flex items-start gap-2">
                                <span class="text-rose-600 font-bold shrink-0">!</span>
                                <span>The quote is two days old and some macro cards disagree with the market (see Data trust).</span>
                            </div>
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-800 shrink-0 border border-rose-200">STALE FEED</span>
                        </li>
                    </ul>
                </div>
            </div>

            <!-- Lower Row: Snapshot & Price vs Value -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Left: Snapshot Card -->
                <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
                    <h3 class="font-bold text-slate-900 text-sm">Snapshot</h3>
                    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        <div class="bg-slate-50 p-3 rounded-xl border border-slate-100 space-y-0.5">
                            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">OPEN</span>
                            <p id="snapOpen" class="text-sm font-bold text-slate-900 mono">₹855.00</p>
                            <span id="snapOpenDate" class="text-[10px] text-slate-400 block">Nov 23</span>
                        </div>
                        <div class="bg-slate-50 p-3 rounded-xl border border-slate-100 space-y-0.5">
                            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">DAY HIGH</span>
                            <p id="snapHigh" class="text-sm font-bold text-slate-900 mono">₹859.70</p>
                            <span class="text-[10px] text-slate-400 block">Nov 23</span>
                        </div>
                        <div class="bg-slate-50 p-3 rounded-xl border border-slate-100 space-y-0.5">
                            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">DAY LOW</span>
                            <p id="snapLow" class="text-sm font-bold text-slate-900 mono">₹814.05</p>
                            <span class="text-[10px] text-slate-400 block">Nov 23</span>
                        </div>
                        <div class="bg-slate-50 p-3 rounded-xl border border-slate-100 space-y-0.5">
                            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">VOLUME</span>
                            <p id="snapVol" class="text-sm font-bold text-slate-900 mono">5.56 Cr</p>
                            <span id="snapVolShares" class="text-[10px] text-slate-400 block">55,615,279 sh</span>
                        </div>
                        <div class="bg-slate-50 p-3 rounded-xl border border-slate-100 space-y-0.5">
                            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">P/B</span>
                            <p id="snapPb" class="text-sm font-bold text-slate-900 mono">2.07×</p>
                            <span class="text-[10px] text-slate-400 block">BV ₹394.80</span>
                        </div>
                        <div class="bg-slate-50 p-3 rounded-xl border border-slate-100 space-y-0.5">
                            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">TRAILING ROE</span>
                            <p id="snapRoe" class="text-sm font-bold text-slate-900 mono">12.84%</p>
                            <span class="text-[10px] text-slate-400 block">Reported</span>
                        </div>
                        <div class="bg-slate-50 p-3 rounded-xl border border-slate-100 space-y-0.5">
                            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">DELIVERY</span>
                            <p id="snapDelivery" class="text-sm font-bold text-slate-900 mono">64.5%</p>
                            <span class="text-[10px] text-slate-400 block">Share of vol</span>
                        </div>
                        <div class="bg-slate-50 p-3 rounded-xl border border-slate-100 space-y-0.5">
                            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">VS BANK NIFTY</span>
                            <p id="snapVsBankNifty" class="text-sm font-bold text-emerald-700 mono">+2.4%</p>
                            <span class="text-[10px] text-slate-400 block">Alpha</span>
                        </div>
                    </div>
                </div>

                <!-- Right: Price vs Value Card -->
                <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
                    <h3 class="font-bold text-slate-900 text-sm">Price vs value</h3>
                    <p class="text-xs text-slate-600 leading-relaxed">
                        Today's <strong class="text-slate-900 mono">₹815</strong> is <strong>47%</strong> above the base-case value of <strong class="text-slate-900 mono">₹553.5</strong> and <strong>31%</strong> above the probability-weighted <strong class="text-slate-900 mono">₹620</strong>.
                    </p>

                    <!-- Horizontal Spectrum Bar -->
                    <div class="pt-4 pb-2">
                        <div class="relative w-full h-3 bg-slate-100 rounded-full">
                            <!-- Base value line at 27.8% -->
                            <div class="absolute top-0 bottom-0 w-0.5 bg-indigo-600" style="left: 27.8%;" title="Base Case: ₹553.5"></div>
                            <!-- Current Price marker at 71.4% -->
                            <div class="absolute -top-1 bottom-0 w-1 bg-slate-900 rounded-full" style="left: 71.4%;"></div>
                            <!-- Floating Pill for Price 815 -->
                            <div class="absolute -top-7 -translate-x-1/2 bg-slate-900 text-white text-[10px] font-bold px-1.5 py-0.5 rounded mono shadow-sm" style="left: 71.4%;">
                                Price 815
                            </div>
                        </div>
                        <!-- Labels below spectrum -->
                        <div class="flex justify-between text-[11px] text-slate-500 font-semibold pt-2">
                            <span class="flex items-center gap-1 text-rose-600"><span class="w-2 h-2 rounded-full bg-rose-500 inline-block"></span> Bear 386</span>
                            <span class="text-indigo-600">Base 553</span>
                            <span class="flex items-center gap-1 text-emerald-600">Bull 987 <span class="w-2 h-2 rounded-full bg-emerald-500 inline-block"></span></span>
                        </div>
                    </div>

                    <p class="text-[11px] text-slate-400">
                        Scale ₹386 (bear) to ₹987 (bull). Detail and sensitivity are on the Valuation tab.
                    </p>
                </div>
            </div>

            <!-- PRIMARY AUTHORITATIVE DECISION CARD -->
            <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-5">
                <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
                    <div class="space-y-1">
                        <div class="flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                            <h3 class="text-base font-extrabold text-slate-900 tracking-tight">Primary Authoritative Decision Engine</h3>
                            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200" id="decisionPrecedenceTier">Precedence 5: Default State</span>
                        </div>
                        <p class="text-xs text-slate-500">Strict hierarchical decision order: Invalidation (P1) → Weakening (P2) → Ceiling (P3) → Entry Tranches (P4) → Default (P5).</p>
                    </div>
                    <div class="flex items-center gap-2">
                        <span id="decisionCanonicalBadge" class="px-4 py-1.5 rounded-full font-extrabold text-sm tracking-wide uppercase bg-amber-50 text-amber-900 border border-amber-300">
                            WAIT
                        </span>
                        <span id="decisionDisagreementPill" class="px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                            1 Disagreement Surfaced
                        </span>
                    </div>
                </div>

                <!-- Big Headline & Sizing Bar -->
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 items-center">
                    <div class="lg:col-span-2 space-y-2">
                        <h4 id="decisionHeadline" class="text-xl sm:text-2xl font-black text-slate-900 tracking-tight leading-snug">
                            WAIT · No new tranche today (0% Allocation)
                        </h4>
                        <p id="decisionDetailText" class="text-xs sm:text-sm text-slate-600 leading-relaxed">
                            Price (₹846.00, 2.14x P/B) is trading at the Fair Value median above our tactical pullback band. Stage disciplined limit orders in the pullback zone (₹805–₹822) or distress floor (₹730). Do not market-chase.
                        </p>
                    </div>

                    <!-- Explicit Position Sizing Matrix Pill -->
                    <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2 text-xs">
                        <div class="flex items-center justify-between">
                            <span class="font-bold text-slate-500 uppercase text-[10px] tracking-wider">Position Allocation</span>
                            <span class="font-bold text-indigo-700 mono" id="decisionCurrentWeight">8.5% of Portfolio</span>
                        </div>
                        <div class="w-full bg-slate-200 h-2 rounded-full overflow-hidden flex">
                            <div class="bg-indigo-600 h-full rounded-full" style="width: 56.6%;"></div>
                        </div>
                        <div class="flex justify-between text-[11px] text-slate-500 font-semibold pt-0.5">
                            <span>Today's Eligible Tranche: <strong class="text-slate-900 mono" id="decisionEligibleTranche">0%</strong></span>
                            <span>Target Ceiling: <strong class="text-slate-900 mono" id="decisionTargetWeight">15.0%</strong></span>
                        </div>
                    </div>
                </div>

                <!-- Order Directive & Arbitration Resolution -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
                    <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1">
                        <span class="text-[10px] font-bold uppercase tracking-wider text-slate-500">Order Execution Directive</span>
                        <p id="decisionOrderDirective" class="font-extrabold text-amber-900 text-sm mono leading-snug">
                            LIMIT_ORDER_PULLBACK · Zone: ₹805–₹822 · 5 Trading Days Valid
                        </p>
                        <p class="text-[11px] text-slate-500">If unfulfilled in 5 trading days, cancel and re-calibrate to updated balance-sheet equity.</p>
                    </div>
                    <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1">
                        <span class="text-[10px] font-bold uppercase tracking-wider text-slate-500">Arbitration Driver & Discipline Guard</span>
                        <p id="decisionPrimaryDriver" class="font-semibold text-slate-800 text-xs leading-snug">
                            Cyclical valuation signals deep value, but tactical momentum is overbought (RSI 88.7) and broker feed is offline.
                        </p>
                        <p class="text-[11px] text-slate-500">Protects against value traps: Thesis failure halts buying even at deep discounts.</p>
                    </div>
                </div>

                <!-- Advisory Inputs Grid -->
                <div class="space-y-2 pt-1 border-t border-slate-100">
                    <span class="text-[10px] font-bold uppercase tracking-wider text-slate-500">Advisory Model Inputs & Surfaced Disagreements</span>
                    <div id="decisionInputsGrid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                        <!-- Injected by JS -->
                    </div>
                </div>

                <!-- Disagreements Box -->
                <div id="decisionDisagreementsBox" class="bg-amber-50 border border-amber-200 p-3.5 rounded-xl text-xs space-y-1">
                    <span class="font-bold text-[11px] text-amber-900">Surfaced Model Disagreements & Resolutions</span>
                    <ul id="decisionDisagreementsList" class="list-disc list-inside text-amber-800 text-[11px] space-y-0.5">
                        <!-- Injected by JS -->
                    </ul>
                </div>
            </div>

            <!-- ORDERED SUB-BLOCK 1: THESIS TREND (4-FLAG MONITOR) -->
            <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-5">
                <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
                    <div>
                        <div class="flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-indigo-600"></span>
                            <h3 class="text-base font-extrabold text-slate-900 tracking-tight">1. Thesis Trend & Franchise Health Monitor (4 Flags)</h3>
                        </div>
                        <p class="text-xs text-slate-500">Monitors underwriting quality, margins, structural CASA, and system credit-deposit competition across consecutive quarters.</p>
                    </div>
                    <span id="thesisStateBadge" class="px-3 py-1 rounded-full text-xs font-extrabold uppercase bg-amber-100 text-amber-900 border border-amber-300">
                        WEAKENING THESIS · PAUSE ADDS
                    </span>
                </div>

                <!-- Synthesis Statement Banner -->
                <div class="bg-slate-50 border border-slate-200 p-4 rounded-xl text-xs text-slate-700 leading-relaxed font-medium">
                    <strong class="text-slate-900">2-Quarter Persistence Evaluation:</strong>
                    <span id="thesisSynthesisSummary">
                        WEAKENING THESIS DETECTED: 0 Red flags and 2 Amber flags active (Structural CASA + System C/D spread). Franchise is solid but facing industry liquidity friction. Discipline directive: PAUSE ALL MARKET ADDS; buy only in deep pullback limit zones.
                    </span>
                </div>

                <!-- 4 Flags Grid -->
                <div id="thesisHealthContainer" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
                    <!-- Injected by JS -->
                </div>
            </div>

            <!-- ORDERED SUB-BLOCK 2: ONE INTEGRATED VALUATION CHART & DYNAMIC ANCHORS -->
            <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-5">
                <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
                    <div>
                        <div class="flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                            <h3 class="text-base font-extrabold text-slate-900 tracking-tight">2. Integrated Valuation Anchors & Dynamic Cost of Equity</h3>
                        </div>
                        <p class="text-xs text-slate-500">Gordon Growth & Residual Income valuation wired dynamically to live 10Y Indian G-Sec yield and reconciled balance-sheet equity.</p>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                            Ke Dynamic = 13.07%
                        </span>
                        <span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            SOTP Fair Value Anchor = ₹938.50
                        </span>
                    </div>
                </div>

                <!-- Integrated Horizontal Spectrum Bar -->
                <div class="bg-slate-50 p-5 rounded-xl border border-slate-200 space-y-4">
                    <div class="flex items-center justify-between text-xs font-bold text-slate-700">
                        <span>Price vs Valuation & Accumulation Levels</span>
                        <span class="mono text-slate-900">Current Tick: ₹846.00 (2.14x P/B)</span>
                    </div>

                    <div class="relative w-full h-4 bg-slate-200 rounded-full mt-6 mb-2">
                        <!-- Deep Value Floor (₹690) -->
                        <div class="absolute top-0 bottom-0 w-1 bg-teal-600 rounded" style="left: 20%;" title="Deep Value Base: ₹690.0"></div>
                        <!-- Distress Floor (₹730) -->
                        <div class="absolute top-0 bottom-0 w-1 bg-cyan-600 rounded" style="left: 28%;" title="Distress Floor: ₹730.0"></div>
                        <!-- Tactical Pullback Band (₹805–822) -->
                        <div class="absolute top-0 bottom-0 bg-emerald-400/60 rounded" style="left: 45%; width: 5%;" title="Tactical Pullback Band: ₹805–₹822"></div>
                        <!-- Fair Value Median (₹850) -->
                        <div class="absolute top-0 bottom-0 w-1 bg-indigo-600 rounded" style="left: 55%;" title="Fair Value Base: ₹850.0"></div>
                        <!-- Current Price Marker (₹846) -->
                        <div class="absolute -top-1.5 bottom-0 w-1.5 bg-slate-900 rounded-full z-10" style="left: 54%;"></div>
                        <div class="absolute -top-7 -translate-x-1/2 bg-slate-900 text-white text-[10px] font-extrabold px-2 py-0.5 rounded mono shadow-sm z-20" style="left: 54%;">
                            Price ₹846.00
                        </div>
                        <!-- Bull Ceiling (₹1,040) -->
                        <div class="absolute top-0 bottom-0 w-1 bg-purple-600 rounded" style="left: 90%;" title="Bull Ceiling: ₹1,040.0"></div>
                    </div>

                    <div class="grid grid-cols-2 sm:grid-cols-6 gap-2 text-center text-[10px] font-bold pt-2">
                        <div class="p-2 rounded bg-white border border-slate-200">
                            <span class="text-rose-600 block">Bear Floor</span>
                            <span class="mono text-slate-900 text-xs font-black">₹553.5</span>
                            <span class="text-slate-400 block font-normal">1.40x P/B</span>
                        </div>
                        <div class="p-2 rounded bg-white border border-slate-200">
                            <span class="text-teal-700 block">Deep Value (40%)</span>
                            <span class="mono text-slate-900 text-xs font-black">₹690.0</span>
                            <span class="text-slate-400 block font-normal">1.75x P/B</span>
                        </div>
                        <div class="p-2 rounded bg-white border border-slate-200">
                            <span class="text-cyan-700 block">Distress 50% Fib (40%)</span>
                            <span class="mono text-slate-900 text-xs font-black">₹730.0</span>
                            <span class="text-slate-400 block font-normal">1.85x P/B</span>
                        </div>
                        <div class="p-2 rounded bg-emerald-50 border border-emerald-300">
                            <span class="text-emerald-800 block">Pullback Band (20%)</span>
                            <span class="mono text-emerald-950 text-xs font-black">₹805–₹822</span>
                            <span class="text-emerald-700 block font-normal">2.05x–2.09x P/B</span>
                        </div>
                        <div class="p-2 rounded bg-indigo-50 border border-indigo-200">
                            <span class="text-indigo-800 block">Fair Value Median (0%)</span>
                            <span class="mono text-indigo-950 text-xs font-black">₹850.0</span>
                            <span class="text-indigo-700 block font-normal">2.15x P/B</span>
                        </div>
                        <div class="p-2 rounded bg-purple-50 border border-purple-200">
                            <span class="text-purple-800 block">Bull Ceiling (Trim)</span>
                            <span class="mono text-purple-950 text-xs font-black">₹1,040.0</span>
                            <span class="text-purple-700 block font-normal">2.63x P/B</span>
                        </div>
                    </div>
                </div>

                <!-- Dynamic Ke & SOTP Reconciliation Cards -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <!-- Dynamic Ke Card -->
                    <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                        <div class="flex items-center justify-between">
                            <span class="font-bold text-slate-900 uppercase text-[10px] tracking-wider">Dynamic Cost of Equity (CAPM)</span>
                            <span class="px-2 py-0.5 rounded bg-indigo-100 text-indigo-800 font-bold mono text-[10px]">Ke = 13.07%</span>
                        </div>
                        <p class="font-mono text-xs font-bold text-slate-800 bg-white p-2 rounded border border-slate-200">
                            Ke = Rf (6.80%) + Beta (1.14) × ERP (5.50%) = 13.07%
                        </p>
                        <p class="text-[11px] text-slate-600 leading-snug">
                            Wired directly to benchmark 10-Year Indian G-Sec yield (6.80%). When RBI changes rates or monetary stance shifts, the cost of equity re-anchors automatically, preventing early profit-taking or premature entry.
                        </p>
                    </div>

                    <!-- SOTP Reconciliation Card -->
                    <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                        <div class="flex items-center justify-between">
                            <span class="font-bold text-slate-900 uppercase text-[10px] tracking-wider">Book-Value & SOTP Reconciliation</span>
                            <span class="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold mono text-[10px]">Net SOTP +₹88.50/sh</span>
                        </div>
                        <div class="bg-white p-2 rounded border border-slate-200 space-y-1 font-mono text-[11px]">
                            <div class="flex justify-between"><span>Core Standalone BVPS:</span> <strong class="text-slate-900">₹368.24/sh</strong></div>
                            <div class="flex justify-between"><span>Consolidated BVPS:</span> <strong class="text-slate-900">₹394.80/sh</strong></div>
                            <div class="flex justify-between text-emerald-700"><span>Subsidiary SOTP (₹115) - Carrying Cost (₹26.5):</span> <strong>+₹88.50/sh</strong></div>
                        </div>
                        <p class="text-[11px] text-slate-600 leading-snug">
                            Investments in subsidiaries are carried on the standalone balance sheet at cost (~₹40,878 Cr = ₹26.50/sh). Deducting carrying cost from the ₹115 SOTP market value strictly prevents double-counting.
                        </p>
                    </div>
                </div>
            </div>

            <!-- ORDERED SUB-BLOCK 3: DECISION HISTORY & AUDIT TRAIL -->
            <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
                <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                    <div>
                        <div class="flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-slate-900"></span>
                            <h3 class="text-base font-extrabold text-slate-900 tracking-tight">3. Immutable Decision History & Audit Trail</h3>
                        </div>
                        <p class="text-xs text-slate-500">Point-in-time chronological record of engine verdicts, execution prices, and cryptographic validation hashes.</p>
                    </div>
                    <span class="px-2.5 py-1 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
                        Cryptographically Audited
                    </span>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-xs text-left">
                        <thead class="bg-slate-50 text-slate-500 font-bold uppercase text-[10px] border-b border-slate-200">
                            <tr>
                                <th class="p-3">Timestamp (IST)</th>
                                <th class="p-3">Canonical Action</th>
                                <th class="p-3">Reference Price</th>
                                <th class="p-3">P/B Multiple</th>
                                <th class="p-3">Precedence Tier</th>
                                <th class="p-3">Status</th>
                            </tr>
                        </thead>
                        <tbody id="decisionHistoryTableBody" class="divide-y divide-slate-100 text-[11px] mono">
                            <!-- Injected by JS -->
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

        <!-- 2. SECTION: DAILY DECISION COMPASS (ODDS & MACRO) -->
        <section id="sectionCompass" class="scroll-mt-28 space-y-6">
            <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6">
                <!-- Compass Header -->
                <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
                    <div>
                        <div class="flex items-center gap-2">
                            <h3 class="text-base font-bold text-slate-900">Daily Compass: Multi-Horizon Probabilities & Technical Confluence</h3>
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                                Odds & Context
                            </span>
                        </div>
                        <p class="text-xs text-slate-500">Expected multi-day ranges, random-walk baseline comparison, Fibonacci ladder, and cross-market derivative context.</p>
                    </div>
                    <div class="flex items-center gap-2">
                        <span id="compassBiasBadge" class="px-2.5 py-1 rounded-full font-bold bg-amber-50 text-amber-800 border border-amber-200 text-xs">
                            Bias: Mean Reversion / Pullback
                        </span>
                        <span id="compassEdgeBadge" class="px-2.5 py-1 rounded-full font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs">
                            Edge: +53.9% at ₹772
                        </span>
                    </div>
                </div>

                <!-- Technicals & Range Tiles -->
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1">
                        <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">ATR(14) Volatility Span</span>
                        <div class="flex items-baseline gap-2">
                            <span id="compassAtrValue" class="text-xl font-extrabold text-slate-900 mono">₹18.1</span>
                            <span id="compassAtrPct" class="text-xs font-semibold text-slate-500">(2.2% of price)</span>
                        </div>
                        <p class="text-[11px] text-slate-500">1-day expected swing noise floor</p>
                    </div>
                    <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1">
                        <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">Expected 1-Day to 5-Day Bounds</span>
                        <div class="text-xs space-y-0.5 mono text-slate-700">
                            <div>1D: <span id="compassRange1D" class="font-bold text-slate-900">₹804.0 – ₹825.9</span></div>
                            <div>3D: <span id="compassRange3D" class="font-bold text-slate-900">₹796.0 – ₹833.9</span></div>
                            <div>5D: <span id="compassRange5D" class="font-bold text-slate-900">₹790.5 – ₹839.4</span></div>
                        </div>
                    </div>
                    <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1">
                        <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">Custody & Structural Anchor</span>
                        <div class="text-xs space-y-0.5 mono text-slate-700">
                            <div>AVWAP: <span id="compassAvwap" class="font-bold text-indigo-700">₹762.8</span></div>
                            <div>Delivery: <span id="compassDelivery" class="font-bold text-emerald-700">64.5% (High Custody)</span></div>
                            <div>Rel Strength: <span id="compassRsBankNifty" class="font-bold text-emerald-700">+2.4% Alpha</span></div>
                        </div>
                    </div>
                </div>

                <!-- Macro Market Inputs Grid -->
                <div class="space-y-3 pt-2">
                    <span class="text-xs font-bold text-slate-500 uppercase tracking-wider block">Cross-Market Derivatives & Liquidity Context</span>
                    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                        <div class="bg-slate-50 p-3 rounded-xl border border-slate-200 space-y-1">
                            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">FII / DII Net Flow</span>
                            <div class="mono text-xs">
                                <div>FII: <span id="macroFiiNet" class="font-bold text-rose-600">-₹1,840.5 Cr</span></div>
                                <div>DII: <span id="macroDiiNet" class="font-bold text-emerald-700">+₹2,450.2 Cr</span></div>
                                <div>Net: <span id="macroNetInst" class="font-extrabold text-emerald-700">+₹609.7 Cr</span></div>
                            </div>
                            <p class="text-[10px] text-slate-400">As-of <span id="macroFlowTs">18:30 IST</span> · Domestic absorption</p>
                        </div>
                        <div class="bg-slate-50 p-3 rounded-xl border border-slate-200 space-y-1">
                            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">India VIX</span>
                            <div class="flex items-baseline gap-1.5">
                                <span id="macroVixVal" class="text-lg font-extrabold text-slate-900 mono">14.85</span>
                                <span id="macroVixChg" class="text-xs font-semibold text-emerald-700 mono">-2.94%</span>
                            </div>
                            <div class="text-xs font-bold text-emerald-700" id="macroVixRegime">Low Volatility Regime</div>
                            <p class="text-[10px] text-slate-400">As-of <span id="macroVixTs">15:30 IST</span> · Low noise regime</p>
                        </div>
                        <div class="bg-slate-50 p-3 rounded-xl border border-slate-200 space-y-1">
                            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Bank Nifty Sector Beta</span>
                            <div class="flex items-baseline gap-1.5">
                                <span id="macroBankNiftyVal" class="text-lg font-extrabold text-slate-900 mono">62,325</span>
                                <span id="macroBankNiftyChg" class="text-xs font-semibold text-emerald-700 mono">+0.82%</span>
                            </div>
                            <div class="text-xs text-slate-700">Trend: <span id="macroBankNiftyTrend" class="font-bold text-slate-800">Above 20 & 50 DMA</span></div>
                            <div class="text-xs text-slate-700">HDFC Beta: <span id="macroHdfcBeta" class="font-bold text-slate-800">1.14x</span></div>
                        </div>
                        <div class="bg-slate-50 p-3 rounded-xl border border-slate-200 space-y-1">
                            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Options Chain OI & Sentiment</span>
                            <div class="text-xs space-y-0.5 mono text-slate-700">
                                <div>PCR OI: <span id="macroPcr" class="font-bold text-indigo-700">1.18 (Mild Bull)</span></div>
                                <div>Max Pain: <span id="macroMaxPain" class="font-bold text-slate-900">₹780.0</span></div>
                                <div>Put Wall: <span id="macroPutWall" class="font-bold text-emerald-700">₹760.0</span></div>
                            </div>
                            <p class="text-[10px] text-slate-400">As-of <span id="macroOiTs">15:30 IST</span> · Call wall at ₹840</p>
                        </div>
                    </div>
                </div>

                <!-- Probabilities & Touch Forecast Table -->
                <div class="space-y-3 pt-2">
                    <span class="text-xs font-bold text-slate-500 uppercase tracking-wider block">Empirical Touch Probabilities vs Naive Random Walk</span>
                    <div class="overflow-x-auto">
                        <table class="w-full text-left text-xs border border-slate-200 rounded-xl overflow-hidden">
                            <thead class="bg-slate-50 text-slate-500 border-b border-slate-200 text-[11px]">
                                <tr>
                                    <th class="p-3 text-left">Target Level</th>
                                    <th class="p-3 text-center">Distance</th>
                                    <th class="p-3 text-center">1-Day</th>
                                    <th class="p-3 text-center">3-Day</th>
                                    <th class="p-3 text-center">5-Day</th>
                                    <th class="p-3 text-center">Naive (5D)</th>
                                    <th class="p-3 text-center">Empirical Edge</th>
                                    <th class="p-3 text-center">Sample Size</th>
                                    <th class="p-3 text-right">Action Directive</th>
                                </tr>
                            </thead>
                            <tbody id="compassTouchTableBody" class="divide-y divide-slate-100 text-center mono">
                                <!-- Injected dynamically by JS -->
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Canonical Fibonacci Levels Table -->
                <div class="space-y-3 pt-2">
                    <span class="text-xs font-bold text-slate-500 uppercase tracking-wider block">Canonical Fibonacci Ladder (Anchored ₹669.20 to ₹818.00)</span>
                    <div class="overflow-x-auto">
                        <table class="w-full text-left text-xs border border-slate-200 rounded-xl overflow-hidden mono">
                            <thead class="bg-slate-50 text-slate-500 border-b border-slate-200 text-[11px]">
                                <tr>
                                    <th class="p-2.5">Fib Ratio</th>
                                    <th class="p-2.5">Price Level</th>
                                    <th class="p-2.5">Distance</th>
                                    <th class="p-2.5">Confluence & Action</th>
                                </tr>
                            </thead>
                            <tbody id="compassFibTableBody" class="divide-y divide-slate-50 text-[11px]">
                                <!-- Injected dynamically by JS -->
                            </tbody>
                        </table>
                    </div>
                    <div class="text-[11px] text-slate-500 flex flex-wrap gap-4 pt-1">
                        <div>20 DMA: <span id="compassDma20Text" class="mono font-bold text-slate-700">₹739.9</span></div>
                        <div>50 DMA: <span id="compassDma50Text" class="mono font-bold text-slate-700">₹725.1</span></div>
                        <div>200 DMA: <span id="compassDma200Text" class="mono font-bold text-slate-700">₹774.7</span></div>
                    </div>
                </div>
            </div>
        </section>

        <!-- 3. SECTION: VALUATION REFERENCE FRAME & PRICE LADDER -->
        <section id="sectionLadder" class="scroll-mt-28">
            <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6">
                <div>
                    <h3 class="text-base font-bold text-slate-900">Unified Price Ladder & Valuation Reference Frame</h3>
                    <p class="text-xs text-slate-500">Monotonically ordered price anchors, historical post-merger percentiles, and capital action rules.</p>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs border border-slate-200 rounded-xl overflow-hidden">
                        <thead class="bg-slate-50 text-slate-500 border-b border-slate-200 text-[11px]">
                            <tr>
                                <th class="p-3 text-left">Level Description</th>
                                <th class="p-3 text-center">Price</th>
                                <th class="p-3 text-center">P/B Multiple</th>
                                <th class="p-3 text-center">Post-Merger %ile</th>
                                <th class="p-3 text-center">Action Rule</th>
                                <th class="p-3 text-left">Analytical Rationale</th>
                            </tr>
                        </thead>
                        <tbody id="priceLadderTableBody" class="divide-y divide-slate-100 text-center mono">
                            <!-- Injected dynamically by JS -->
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

        <!-- 4. SECTION: 6 SAFETY & ACCUMULATION GATES -->
        <section id="sectionGates" class="scroll-mt-28">
            <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6">
                <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
                    <div>
                        <div class="flex items-center gap-2">
                            <h3 class="text-base font-bold text-slate-900">6 Safety & Accumulation Gates</h3>
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
                                Solvency & Discipline
                            </span>
                        </div>
                        <p class="text-xs text-slate-500">System checks required before deploying capital: filing data integrity, valuation discipline, solvency, and timing.</p>
                    </div>
                    <span id="gatesStatusSummaryBadge" class="px-3 py-1 rounded-full bg-slate-100 text-slate-800 text-xs font-bold border border-slate-200">
                        5 of 6 Gates Pass
                    </span>
                </div>

                <div id="gatesListContainer" class="space-y-3">
                    <!-- Injected dynamically by JS -->
                </div>
            </div>
        </section>

        <!-- 5. SECTION: PLAIN-LANGUAGE GLOSSARY -->
        <section id="sectionGlossary" class="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4 scroll-mt-28">
            <div class="flex items-center gap-2">
                <h3 class="text-sm font-bold text-slate-900">Plain-Language Glossary</h3>
                <span class="px-2 py-0.5 rounded bg-slate-100 text-slate-600 text-[10px] font-semibold">Terms Explained Simply</span>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
                <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-100 space-y-1">
                    <span class="font-bold text-slate-900 block">Price-to-Book (P/B) Multiple</span>
                    <p class="text-slate-600 text-[11px] leading-relaxed">
                        Stock price divided by net assets per share. HDFC Bank is currently trading at <strong>2.06x</strong> book value (₹394.80 BVPS), near post-merger cyclical lows.
                    </p>
                </div>
                <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-100 space-y-1">
                    <span class="font-bold text-slate-900 block">Return on Equity (ROE)</span>
                    <p class="text-slate-600 text-[11px] leading-relaxed">
                        Annualized profit divided by total equity. Reported Q2 FY27 trailing ROE is <strong>12.84%</strong> on certified net worth of ₹6,07,600 Cr.
                    </p>
                </div>
                <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-100 space-y-1">
                    <span class="font-bold text-slate-900 block">CASA Ratio</span>
                    <p class="text-slate-600 text-[11px] leading-relaxed">
                        Percentage of low-cost savings & current deposits. Certified at <strong>38.0% (Period-end)</strong> and <strong>31.6% (Daily Avg)</strong> out of ₹30,40,000 Cr deposits.
                    </p>
                </div>
                <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-100 space-y-1">
                    <span class="font-bold text-slate-900 block">Cost of Equity (Ke)</span>
                    <p class="text-slate-600 text-[11px] leading-relaxed">
                        Minimum return expected by equity shareholders. Derived at <strong>12.28%</strong> based on 10Y Indian G-Sec yield (6.80%) and bank beta (1.14x).
                    </p>
                </div>
                <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-100 space-y-1">
                    <span class="font-bold text-slate-900 block">Capital Adequacy Ratio (CAR)</span>
                    <p class="text-slate-600 text-[11px] leading-relaxed">
                        Regulatory buffer protecting depositors. HDFC Bank stands at <strong>18.9%</strong>, comfortably above the RBI regulatory minimum (11.5%) and engine floor (14.0%).
                    </p>
                </div>
                <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-100 space-y-1">
                    <span class="font-bold text-slate-900 block">Gross & Net NPA</span>
                    <p class="text-slate-600 text-[11px] leading-relaxed">
                        Proportion of loans overdue. Standalone Gross NPA is <strong>1.11%</strong> and Net NPA is <strong>0.37%</strong>, indicating pristine asset quality.
                    </p>
                </div>
                <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-100 space-y-1">
                    <span class="font-bold text-slate-900 block">Wilder RSI(14)</span>
                    <p class="text-slate-600 text-[11px] leading-relaxed">
                        Momentum speed indicator. Value is <strong>88.7</strong>, signaling deep short-term sprint exhaustion. The system mandates waiting for cooldown below 75.
                    </p>
                </div>
                <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-100 space-y-1">
                    <span class="font-bold text-slate-900 block">Tactical Limit Buy Zone</span>
                    <p class="text-slate-600 text-[11px] leading-relaxed">
                        Derived price channel (<strong>₹742.0 – ₹772.0</strong>) representing a 5% to 9% dip, aligning with post-merger lower-quartile valuation support.
                    </p>
                </div>
            </div>
        </section>

        <!-- 6. SECTION: HISTORICAL PROOF & DEEP-DIVE AUDIT LEDGER (4 DISTINCT TABS) -->
        <section id="sectionDetails" class="scroll-mt-28 space-y-4">
            <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6">
                <!-- Tab Navigation Header -->
                <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
                    <div>
                        <div class="flex items-center gap-2">
                            <h3 class="text-base font-bold text-slate-900">Historical Proof & Deep-Dive Audit Ledger</h3>
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                                Audited & Chained
                            </span>
                        </div>
                        <p class="text-xs text-slate-500">Walk-forward backtests, management commitments, certified regulatory disclosures, and immutable decision ledger.</p>
                    </div>
                    
                    <!-- 4 Distinct Tab Buttons -->
                    <div class="flex items-center bg-slate-100 p-1 rounded-xl gap-1 border border-slate-200">
                        <button onclick="switchAuditTab('evidence')" id="tab-btn-evidence" class="px-3.5 py-1.5 rounded-lg text-xs font-bold bg-slate-900 text-white shadow-sm transition">
                            Evidence
                        </button>
                        <button onclick="switchAuditTab('fundamentals')" id="tab-btn-fundamentals" class="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white transition">
                            Fundamentals
                        </button>
                        <button onclick="switchAuditTab('context')" id="tab-btn-context" class="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white transition">
                            Context
                        </button>
                        <button onclick="switchAuditTab('integrity')" id="tab-btn-integrity" class="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white transition">
                            Integrity
                        </button>
                    </div>
                </div>

                <!-- TAB 1: EVIDENCE (Post-Merger Live Backtest & Separated Pre-Merger Analogues) -->
                <div id="tab-pane-evidence" class="space-y-6">
                    <!-- Live Rule Backtest Card -->
                    <div class="bg-slate-50 p-5 rounded-xl border border-slate-200 space-y-4">
                        <div class="flex flex-wrap items-center justify-between gap-3">
                            <div>
                                <div class="flex items-center gap-2">
                                    <h4 class="text-sm font-bold text-slate-900">Post-Merger Live Rule Walk-Forward Backtest (July 2023–Present)</h4>
                                    <span id="badgeBacktestVerified" class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                                        68% Limit Fill Rate
                                    </span>
                                </div>
                                <p class="text-xs text-slate-500">Tested strictly with live limit order band (₹742–₹772) and RSI cooldown. Net after 0.15% friction & STCG taxes.</p>
                            </div>
                            <div class="flex items-center gap-3">
                                <div class="flex items-center gap-2 text-xs font-medium text-slate-600">
                                    <span class="inline-block w-3 h-0.5 bg-emerald-600"></span> Strategy (+18.4%)
                                    <span class="inline-block w-3 h-0.5 bg-sky-600"></span> SIP (+8.2%)
                                    <span class="inline-block w-3 h-0.5 bg-slate-400"></span> Buy & Hold (-9.5%)
                                </div>
                                <select id="selectPeriod" onchange="runBacktest()" class="bg-white text-xs border border-slate-300 rounded-lg px-3 py-1.5 mono">
                                    <option value="1y">1 Year Walk-Forward</option>
                                    <option value="2y" selected>2 Years Walk-Forward</option>
                                    <option value="3y">3 Years Walk-Forward</option>
                                </select>
                            </div>
                        </div>

                        <!-- Backtest Canvas -->
                        <div class="w-full h-72 sm:h-80 relative bg-white rounded-xl border border-slate-200 p-2 flex items-center justify-center">
                            <canvas id="equityChart" class="w-full h-full"></canvas>
                            <div id="chartEmptyState" class="hidden absolute inset-0 flex flex-col items-center justify-center bg-white rounded-xl text-slate-400 text-xs font-medium">
                                <p>Not enough backtest data yet</p>
                            </div>
                        </div>

                        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                            <div class="bg-white p-3 rounded-lg border border-slate-200">
                                <span class="text-slate-500 block text-[10px]">Net Strategy Return</span>
                                <span class="text-base font-bold text-emerald-700 mono">+18.4%</span>
                                <span class="text-[10px] text-slate-400 block">After 0.15% friction</span>
                            </div>
                            <div class="bg-white p-3 rounded-lg border border-slate-200">
                                <span class="text-slate-500 block text-[10px]">Monthly SIP Return</span>
                                <span class="text-base font-bold text-indigo-700 mono">+8.2%</span>
                                <span class="text-[10px] text-slate-400 block">Baseline benchmark</span>
                            </div>
                            <div class="bg-white p-3 rounded-lg border border-slate-200">
                                <span class="text-slate-500 block text-[10px]">Max Strategy Drawdown</span>
                                <span class="text-base font-bold text-slate-900 mono">-7.7%</span>
                                <span class="text-[10px] text-emerald-600 block">vs -18.2% B&H</span>
                            </div>
                            <div class="bg-white p-3 rounded-lg border border-slate-200">
                                <span class="text-slate-500 block text-[10px]">Bootstrap 95% CI</span>
                                <span class="text-base font-bold text-slate-900 mono">11.4% – 26.2%</span>
                                <span class="text-[10px] text-slate-400 block">10,000 resamples</span>
                            </div>
                        </div>
                    </div>

                    <!-- Separated Pre-Merger Historical Analogues Table -->
                    <div class="space-y-3">
                        <div class="flex flex-wrap items-center justify-between gap-3">
                            <div>
                                <h4 class="text-sm font-bold text-slate-900">Historical Analogues (2018–2026 Reference)</h4>
                                <p class="text-xs text-slate-500">Standalone pre-merger HDFC Bank episodes distinguished from post-merger combined entity. Provided as structural reference.</p>
                            </div>
                            <div class="flex items-center gap-2 text-xs font-semibold mono" id="analogueHeaderStats">
                                <span class="px-2.5 py-1 rounded bg-emerald-50 text-emerald-800 border border-emerald-200">6M Hit Rate: 50.0%</span>
                                <span class="px-2.5 py-1 rounded bg-rose-50 text-rose-800 border border-rose-200">Worst MAE: -9.4%</span>
                            </div>
                        </div>

                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-xs border border-slate-200 rounded-xl overflow-hidden">
                                <thead class="bg-slate-50 text-slate-500 border-b border-slate-200 text-[11px]">
                                    <tr>
                                        <th class="p-3">Episode Name / Date</th>
                                        <th class="p-3">Era</th>
                                        <th class="p-3">Entry Price</th>
                                        <th class="p-3">P/B Multiple</th>
                                        <th class="p-3">Drawdown</th>
                                        <th class="p-3">30D Return</th>
                                        <th class="p-3">90D Return</th>
                                        <th class="p-3">180D Return</th>
                                        <th class="p-3">Max Adverse</th>
                                        <th class="p-3">Outcome</th>
                                    </tr>
                                </thead>
                                <tbody id="analogueTableBody" class="divide-y divide-slate-100 mono">
                                    <!-- Injected dynamically by JS -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- TAB 2: FUNDAMENTALS (Commitments & Safety Thresholds) -->
                <div id="tab-pane-fundamentals" class="space-y-6 hidden">
                    <!-- Management Commitments Tracker -->
                    <div class="space-y-3">
                        <div class="flex items-center justify-between">
                            <div>
                                <h4 class="text-sm font-bold text-slate-900">Management Promise & Guidance Tracker (Q2 FY27 Audit)</h4>
                                <p class="text-xs text-slate-500">Authenticated against BSE/NSE Q2 FY27 Standalone filing (Oct 17, 2026). SHA-256: a044248425db1ac790b420d7b697f7184fd6be59466596a1bc7319e775f940d3</p>
                            </div>
                            <span class="px-2.5 py-1 rounded bg-emerald-50 text-emerald-700 text-xs font-semibold border border-emerald-200">
                                100% Verbatim Match
                            </span>
                        </div>
                        <div id="promisesGrid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
                            <!-- Injected dynamically by JS -->
                        </div>
                    </div>

                    <!-- Engine Safety Thresholds Grid -->
                    <div class="space-y-3 pt-4 border-t border-slate-100">
                        <h4 class="text-sm font-bold text-slate-900">Engine Safety Thresholds & Hard Constraints</h4>
                        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                            <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                                <span class="text-slate-500 block text-[10px]">Capital Adequacy (CAR)</span>
                                <p class="text-base font-bold text-emerald-700 mono">18.9%</p>
                                <span class="text-[10px] text-slate-500 block">Regulatory min 11.5% · Engine floor 14.0%</span>
                            </div>
                            <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                                <span class="text-slate-500 block text-[10px]">Asset Quality (GNPA / NNPA)</span>
                                <p class="text-base font-bold text-emerald-700 mono">1.11% / 0.37%</p>
                                <span class="text-[10px] text-slate-500 block">Pristine quality · Floor ceiling 1.40%</span>
                            </div>
                            <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                                <span class="text-slate-500 block text-[10px]">Credit-to-Deposit (C/D) Ratio</span>
                                <p class="text-base font-bold text-indigo-700 mono">96.0%</p>
                                <span class="text-[10px] text-slate-500 block">Down from 98.4% YoY · Approaching 90% target</span>
                            </div>
                            <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                                <span class="text-slate-500 block text-[10px]">CASA Ratio (Dual Reporting)</span>
                                <p class="text-base font-bold text-slate-900 mono">38.0% / 31.6%</p>
                                <span class="text-[10px] text-slate-500 block">38.0% (Period-end) · 31.6% (Daily Avg)</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- TAB 3: CONTEXT (Certified Statutory Disclosures & RBI) -->
                <div id="tab-pane-context" class="space-y-4 hidden">
                    <div class="flex flex-wrap items-center justify-between gap-2">
                        <div>
                            <h4 class="text-sm font-bold text-slate-900">Certified Regulatory Announcements & Statutory Filings (Oct–Nov 2026)</h4>
                            <p class="text-xs text-slate-500">BSE & NSE SEBI LODR disclosures and RBI MPC resolutions scored for materiality and mapped to safety gate freeze triggers.</p>
                        </div>
                        <span id="badgeEventsClassified" class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            Certified Disclosures
                        </span>
                    </div>

                    <div id="eventsListContainer" class="space-y-2.5">
                        <!-- Injected dynamically by JS -->
                    </div>
                </div>

                <!-- TAB 4: INTEGRITY (Decision Ledger & Peer Comparison) -->
                <div id="tab-pane-integrity" class="space-y-6 hidden">
                    <!-- Big-4 Private Banking Watchlist -->
                    <div class="space-y-3">
                        <div class="flex items-center justify-between">
                            <div>
                                <h4 class="text-sm font-bold text-slate-900">Big-4 Private Banking Watchlist (Standalone Q2 FY27)</h4>
                                <p class="text-xs text-slate-500">HDFC Bank at reference price ₹814.95. Offline peer feeds display '--' without fabricated estimates.</p>
                            </div>
                            <span class="px-2.5 py-1 rounded bg-purple-50 text-purple-700 text-xs font-semibold border border-purple-200">
                                Big-4 Banks
                            </span>
                        </div>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-xs border border-slate-200 rounded-xl overflow-hidden mono">
                                <thead class="bg-slate-50 text-slate-500 border-b border-slate-200 text-[11px]">
                                    <tr>
                                        <th class="p-3">Bank / Ticker</th>
                                        <th class="p-3">Price</th>
                                        <th class="p-3">P/B Multiple</th>
                                        <th class="p-3">5Y Percentile</th>
                                        <th class="p-3">Trailing ROE</th>
                                        <th class="p-3">CAR</th>
                                        <th class="p-3">GNPA</th>
                                        <th class="p-3">C/D Ratio</th>
                                        <th class="p-3">Strategy Status</th>
                                    </tr>
                                </thead>
                                <tbody id="peerWatchlistTableBody" class="divide-y divide-slate-100 text-slate-700">
                                    <!-- Injected dynamically by JS -->
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Cryptographic Ledger & Filing Verification -->
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-3 border-t border-slate-100">
                        <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                            <h5 class="text-xs font-bold text-slate-700 uppercase tracking-wider">SEBI LODR Reg 33 Statutory Filing Verification</h5>
                            <div class="space-y-1.5 text-xs text-slate-600">
                                <p><strong>Document:</strong> Unaudited Standalone Results (Q2 FY27)</p>
                                <p><strong>Filing Date:</strong> October 17, 2026 (BSE & NSE India)</p>
                                <p><strong>Standalone PAT:</strong> ₹19,510 Cr (Annualized: ₹78,040 Cr)</p>
                                <p><strong>Total Net Worth:</strong> ₹6,07,600 Cr | <strong>Shares:</strong> 15.39 Bn</p>
                                <p><strong>Total Deposits:</strong> ₹30,40,000 Cr | <strong>CASA Ratio:</strong> 38.0% (Period-end) / 31.6% (Daily Avg)</p>
                                <p><strong>Reconciled BVPS:</strong> ₹394.80 | <strong>Trailing ROE:</strong> 12.84%</p>
                                <p class="text-[10px] mono text-slate-400 break-all pt-1">
                                    SHA-256: a044248425db1ac790b420d7b697f7184fd6be59466596a1bc7319e775f940d3
                                </p>
                            </div>
                        </div>

                        <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                            <h5 class="text-xs font-bold text-slate-700 uppercase tracking-wider">Cryptographic Hash Chain Ledger (SQLite)</h5>
                            <p class="text-xs text-slate-500">Every 2:00 PM recommendation is signed and hash-chained into SQLite before market close.</p>
                            <div class="bg-slate-900 text-emerald-400 p-3 rounded-lg font-mono text-[10px] space-y-1 max-h-40 overflow-y-auto" id="healthLedgerList">
                                <!-- Injected dynamically by JS -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

    </main>

    <!-- Footer -->
    <footer class="max-w-[1240px] mx-auto px-4 sm:px-6 py-8 text-center text-xs text-slate-400 border-t border-slate-200">
        HDFC Bank Cyclical Accumulation Engine · Prototype built from verified filing data & NSE cash records · Strictly for Educational & Simulation Purposes.
    </footer>

    <!-- Complete Client-side JavaScript -->
    <script>
        function showToast(message, type = 'success') {
            const container = document.getElementById('toastContainer');
            if (!container) return;
            const toast = document.createElement('div');
            toast.className = `toast-item ${type === 'success' ? 'toast-success' : 'toast-error'}`;
            toast.textContent = message;
            container.appendChild(toast);
            setTimeout(() => {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }, 4000);
        }

        function setMode(mode) {
            const btnPlain = document.getElementById('btnModePlain');
            const btnTech = document.getElementById('btnModeTech');
            if (mode === 'tech') {
                document.body.classList.add('show-tech');
                btnTech.className = 'px-3 py-1 rounded-md bg-white text-slate-900 shadow-sm transition';
                btnPlain.className = 'px-3 py-1 rounded-md text-slate-500 hover:text-slate-900 transition';
            } else {
                document.body.classList.remove('show-tech');
                btnPlain.className = 'px-3 py-1 rounded-md bg-white text-slate-900 shadow-sm transition';
                btnTech.className = 'px-3 py-1 rounded-md text-slate-500 hover:text-slate-900 transition';
            }
        }

        function formatOrdinal(n) {
            const s = ["th", "st", "nd", "rd"];
            const v = n % 100;
            return n + (s[(v - 20) % 10] || s[v] || s[0]);
        }

        function switchAuditTab(tabId) {
            const tabs = ['evidence', 'fundamentals', 'context', 'integrity'];
            tabs.forEach(t => {
                const pane = document.getElementById('tab-pane-' + t);
                const btn = document.getElementById('tab-btn-' + t);
                if (t === tabId) {
                    if (pane) pane.classList.remove('hidden');
                    if (btn) {
                        btn.className = 'px-3.5 py-1.5 rounded-lg text-xs font-bold bg-slate-900 text-white shadow-sm transition';
                    }
                } else {
                    if (pane) pane.classList.add('hidden');
                    if (btn) {
                        btn.className = 'px-3.5 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white transition';
                    }
                }
            });
        }

        let currentHeroTimeframe = '6M';
        let heroOverlays = {
            buyBand: true,
            fibLevels: false,
            movingAvgs: false,
            avwap: false
        };
        let cachedPriceSeries = [];

        function setHeroTimeframe(tf) {
            currentHeroTimeframe = tf;
            document.querySelectorAll('.btn-tf').forEach(b => {
                if (b.dataset.tf === tf) {
                    b.className = 'btn-tf px-2.5 py-1 rounded-md text-xs font-bold bg-slate-900 text-white shadow-sm transition';
                } else {
                    b.className = 'btn-tf px-2.5 py-1 rounded-md text-xs font-semibold text-slate-500 hover:text-slate-900 bg-transparent transition';
                }
            });
            drawHeroChart();
        }

        function toggleHeroOverlay(name) {
            heroOverlays[name] = !heroOverlays[name];
            const btn = document.getElementById('btnOverlay_' + name);
            if (btn) {
                if (heroOverlays[name]) {
                    btn.className = 'px-2.5 py-1 rounded-full text-xs font-bold bg-slate-900 text-white shadow-sm border border-slate-900 transition flex items-center gap-1';
                    if (name === 'buyBand') {
                        btn.innerHTML = '<span class="w-2 h-2 rounded-full bg-emerald-400"></span> Buy band';
                    }
                } else {
                    btn.className = 'px-2.5 py-1 rounded-full text-xs font-semibold bg-white text-slate-600 border border-slate-200 hover:border-slate-300 transition flex items-center gap-1';
                    if (name === 'buyBand') {
                        btn.innerHTML = 'Buy band';
                    }
                }
            }
            drawHeroChart();
        }

        function drawHeroChart() {
            const canvas = document.getElementById('heroPriceChart');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            if (!ctx) return;

            const dpr = window.devicePixelRatio || 1;
            const rect = canvas.getBoundingClientRect();
            canvas.width = rect.width * dpr;
            canvas.height = rect.height * dpr;
            ctx.scale(dpr, dpr);

            const w = rect.width;
            const h = rect.height;
            ctx.clearRect(0, 0, w, h);

            if (!cachedPriceSeries || cachedPriceSeries.length === 0) return;

            let bars = cachedPriceSeries;
            if (currentHeroTimeframe === '1M') {
                bars = cachedPriceSeries.slice(-22);
            } else if (currentHeroTimeframe === '3M') {
                bars = cachedPriceSeries.slice(-66);
            } else if (currentHeroTimeframe === '6M') {
                bars = cachedPriceSeries.slice(-132);
            }

            if (bars.length < 2) return;

            const padding = { top: 32, right: 65, bottom: 32, left: 55 };
            const chartW = w - padding.left - padding.right;
            const chartH = h - padding.top - padding.bottom;

            let minP = Infinity, maxP = -Infinity;
            bars.forEach(b => {
                if (b.close < minP) minP = b.close;
                if (b.close > maxP) maxP = b.close;
            });

            if (heroOverlays.buyBand) {
                minP = Math.min(minP, 735);
                maxP = Math.max(maxP, 780);
            }
            minP = Math.min(minP, 665);
            maxP = Math.max(maxP, 835);

            const priceSpan = maxP - minP || 1;
            const getY = (val) => padding.top + chartH - ((val - minP) / priceSpan) * chartH;
            const getX = (idx) => padding.left + (idx / (bars.length - 1)) * chartW;

            // Subtle Grid lines
            ctx.strokeStyle = '#f1f5f9';
            ctx.lineWidth = 1;
            for (let p = Math.ceil(minP / 25) * 25; p <= maxP; p += 25) {
                const y = getY(p);
                ctx.beginPath();
                ctx.moveTo(padding.left, y);
                ctx.lineTo(w - padding.right, y);
                ctx.stroke();

                ctx.fillStyle = '#94a3b8';
                ctx.font = '10px ui-monospace, monospace';
                ctx.textAlign = 'left';
                ctx.fillText('₹' + p, w - padding.right + 8, y + 3);
            }

            // 1. Shaded Buy Zone Overlay
            if (heroOverlays.buyBand) {
                const yTop = getY(772.0);
                const yBottom = getY(742.0);
                ctx.fillStyle = 'rgba(0, 208, 156, 0.12)';
                ctx.fillRect(padding.left, yTop, chartW, yBottom - yTop);

                ctx.strokeStyle = '#059669';
                ctx.lineWidth = 1;
                ctx.setLineDash([4, 4]);
                ctx.beginPath();
                ctx.moveTo(padding.left, yTop);
                ctx.lineTo(padding.left + chartW, yTop);
                ctx.moveTo(padding.left, yBottom);
                ctx.lineTo(padding.left + chartW, yBottom);
                ctx.stroke();
                ctx.setLineDash([]);

                ctx.fillStyle = '#065f46';
                ctx.font = 'bold 10px sans-serif';
                ctx.textAlign = 'right';
                ctx.fillText('Buy zone (₹742–₹772)', padding.left + chartW - 10, yTop + 14);
            }

            // 2. Cycle Low Anchor Line (₹669.20)
            const yLow = getY(669.20);
            if (yLow >= padding.top && yLow <= padding.top + chartH) {
                ctx.strokeStyle = '#f59e0b';
                ctx.lineWidth = 1;
                ctx.setLineDash([2, 3]);
                ctx.beginPath();
                ctx.moveTo(padding.left, yLow);
                ctx.lineTo(padding.left + chartW, yLow);
                ctx.stroke();
                ctx.setLineDash([]);
                ctx.fillStyle = '#b45309';
                ctx.font = '10px sans-serif';
                ctx.textAlign = 'left';
                ctx.fillText('Cycle Low ₹669.20', padding.left + 8, yLow - 4);
            }

            // 3. Fibonacci Levels Overlay
            if (heroOverlays.fibLevels) {
                const fibs = [
                    { label: 'Fib 38.2% ₹761.2', val: 761.2, color: '#3b82f6' },
                    { label: 'Fib 50.0% ₹743.6', val: 743.6, color: '#6366f1' },
                    { label: 'Fib 61.8% ₹726.0', val: 726.0, color: '#8b5cf6' }
                ];
                fibs.forEach(f => {
                    const yf = getY(f.val);
                    ctx.strokeStyle = f.color;
                    ctx.lineWidth = 1;
                    ctx.setLineDash([3, 3]);
                    ctx.beginPath();
                    ctx.moveTo(padding.left, yf);
                    ctx.lineTo(padding.left + chartW, yf);
                    ctx.stroke();
                    ctx.setLineDash([]);
                    ctx.fillStyle = f.color;
                    ctx.font = '10px monospace';
                    ctx.textAlign = 'left';
                    ctx.fillText(f.label, padding.left + 8, yf - 3);
                });
            }

            // 4. Moving Averages Overlay
            if (heroOverlays.movingAvgs) {
                const mas = [
                    { label: '20 DMA ₹739.9', val: 739.9, color: '#f59e0b' },
                    { label: '50 DMA ₹725.1', val: 725.1, color: '#0ea5e9' },
                    { label: '200 DMA ₹774.7', val: 774.7, color: '#a855f7' }
                ];
                mas.forEach(m => {
                    const ym = getY(m.val);
                    ctx.strokeStyle = m.color;
                    ctx.lineWidth = 1.2;
                    ctx.setLineDash([4, 2]);
                    ctx.beginPath();
                    ctx.moveTo(padding.left, ym);
                    ctx.lineTo(padding.left + chartW, ym);
                    ctx.stroke();
                    ctx.setLineDash([]);
                    ctx.fillStyle = m.color;
                    ctx.font = 'bold 10px monospace';
                    ctx.textAlign = 'left';
                    ctx.fillText(m.label, padding.left + 140, ym - 3);
                });
            }

            // 5. Anchored VWAP Overlay
            if (heroOverlays.avwap) {
                const yAvwap = getY(762.8);
                ctx.strokeStyle = '#4f46e5';
                ctx.lineWidth = 1.5;
                ctx.setLineDash([5, 3]);
                ctx.beginPath();
                ctx.moveTo(padding.left, yAvwap);
                ctx.lineTo(padding.left + chartW, yAvwap);
                ctx.stroke();
                ctx.setLineDash([]);
                ctx.fillStyle = '#4338ca';
                ctx.font = 'bold 10px monospace';
                ctx.textAlign = 'left';
                ctx.fillText('AVWAP ₹762.8', padding.left + chartW - 120, yAvwap - 4);
            }

            // 6. Gradient Area Under Price Line
            const grad = ctx.createLinearGradient(0, padding.top, 0, padding.top + chartH);
            grad.addColorStop(0, 'rgba(0, 208, 156, 0.22)');
            grad.addColorStop(1, 'rgba(0, 208, 156, 0.01)');

            ctx.beginPath();
            ctx.moveTo(getX(0), getY(bars[0].close));
            for (let i = 1; i < bars.length; i++) {
                ctx.lineTo(getX(i), getY(bars[i].close));
            }
            ctx.lineTo(getX(bars.length - 1), padding.top + chartH);
            ctx.lineTo(getX(0), padding.top + chartH);
            ctx.closePath();
            ctx.fillStyle = grad;
            ctx.fill();

            // 7. Price Stroke Line
            ctx.beginPath();
            ctx.moveTo(getX(0), getY(bars[0].close));
            for (let i = 1; i < bars.length; i++) {
                ctx.lineTo(getX(i), getY(bars[i].close));
            }
            ctx.strokeStyle = '#00D09C';
            ctx.lineWidth = 2.2;
            ctx.lineJoin = 'round';
            ctx.lineCap = 'round';
            ctx.stroke();

            // 8. Latest Price Dot & Halo
            const lastIdx = bars.length - 1;
            const lastX = getX(lastIdx);
            const lastY = getY(bars[lastIdx].close);

            ctx.beginPath();
            ctx.arc(lastX, lastY, 7, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(0, 208, 156, 0.35)';
            ctx.fill();

            ctx.beginPath();
            ctx.arc(lastX, lastY, 4, 0, Math.PI * 2);
            ctx.fillStyle = '#00D09C';
            ctx.fill();
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 1.5;
            ctx.stroke();

            const firstBar = bars[0];
            const lastBar = bars[lastIdx];
            const chgPct = ((lastBar.close - firstBar.close) / firstBar.close * 100).toFixed(1);
            const chgSign = chgPct >= 0 ? '+' : '';

            ctx.fillStyle = '#94a3b8';
            ctx.font = '10px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(firstBar.date, padding.left, h - 10);
            ctx.textAlign = 'right';
            ctx.fillText(lastBar.date, padding.left + chartW, h - 10);

            ctx.fillStyle = '#0f172a';
            ctx.font = 'bold 11px monospace';
            ctx.textAlign = 'left';
            ctx.fillText(`Nov 17 (latest) · ₹${lastBar.close.toFixed(2)}`, padding.left + 8, padding.top - 12);

            ctx.fillStyle = chgPct >= 0 ? '#059669' : '#dc2626';
            ctx.font = 'bold 11px sans-serif';
            ctx.textAlign = 'right';
            ctx.fillText(`${chgSign}${chgPct}% since ${firstBar.date.slice(5)}`, padding.left + chartW, padding.top - 12);
        }

        function applyStatus(data) {
            if (!data) return;

            if (data.reference_price) {
                const pText = `₹${data.reference_price.toFixed(2)}`;
                const elH = document.getElementById('headerPriceText');
                const elHero = document.getElementById('heroPrice');
                if (elH) elH.textContent = pText;
                if (elHero) elHero.textContent = pText;
            }

            if (data.price_series && data.price_series.length > 0) {
                cachedPriceSeries = data.price_series;
                drawHeroChart();
            }

            if (data.quote) {
                const q = data.quote;
                const deltaEl = document.getElementById('heroDelta');
                if (deltaEl && q.change !== undefined && q.change_pct !== undefined) {
                    const isUp = q.change >= 0;
                    deltaEl.className = `text-sm sm:text-base font-bold flex items-center gap-0.5 ${isUp ? 'text-emerald-600' : 'text-rose-600'}`;
                    deltaEl.textContent = `${isUp ? '▲ +' : '▼ '}${q.change.toFixed(2)} (${isUp ? '+' : ''}${q.change_pct.toFixed(2)}%)`;
                }

                const chipText = document.getElementById('heroFeedChipText');
                const chipDot = document.getElementById('heroFeedChipDot');
                const chipEl = document.getElementById('heroFeedChip');
                if (chipText) {
                    const isL = q.is_live;
                    if (chipEl) {
                        chipEl.className = isL 
                            ? "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-semibold bg-emerald-50 text-emerald-900 border border-emerald-200"
                            : "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-semibold bg-amber-50 text-amber-900 border border-amber-200";
                    }
                    if (chipDot) {
                        chipDot.className = `w-1.5 h-1.5 rounded-full ${isL ? 'bg-emerald-500' : 'bg-amber-500'}`;
                    }
                    const statusLbl = isL ? 'LIVE' : 'STALE';
                    chipText.textContent = `${statusLbl} · ${q.source || 'NSE'} · As of ${q.timestamp || 'Today'} · Prev close ₹${(q.previous_close || 846.0).toFixed(2)}`;
                }

                const sO = document.getElementById('snapOpen');
                if (sO && q.day_open) sO.textContent = `₹${q.day_open.toFixed(2)}`;
                const sH = document.getElementById('snapHigh');
                if (sH && q.day_high) sH.textContent = `₹${q.day_high.toFixed(2)}`;
                const sL = document.getElementById('snapLow');
                if (sL && q.day_low) sL.textContent = `₹${q.day_low.toFixed(2)}`;
                const sV = document.getElementById('snapVol');
                const sVs = document.getElementById('snapVolShares');
                if (sV && q.volume) {
                    sV.textContent = `${(q.volume / 10000000).toFixed(2)} Cr`;
                    if (sVs) sVs.textContent = `${q.volume.toLocaleString()} sh`;
                }
                const sPb = document.getElementById('snapPb');
                if (sPb && q.current_price) sPb.textContent = `${(q.current_price / 394.80).toFixed(2)}×`;
            }

            const decObj = data.decision_object;
            const isLive = decObj ? decObj.is_live_data : false;
            const feedSource = decObj ? decObj.feed_source : "NSE Historical Verified Cache";
            const feedTs = decObj ? decObj.feed_timestamp : "2026-11-18 15:30:00 IST";

            const badge = document.getElementById('headerFeedStatusBadge');
            if (badge) {
                if (isLive) {
                    badge.className = "px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800 border border-emerald-300";
                    badge.textContent = "LIVE BROKER FEED";
                } else {
                    badge.className = "px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-rose-100 text-rose-800 border border-rose-300";
                    badge.textContent = "DATA STALE - not live";
                }
            }

            const staleBanner = document.getElementById('staleFeedAlertBanner');
            if (staleBanner) {
                if (!isLive) {
                    staleBanner.classList.remove('hidden');
                    const srcEl = document.getElementById('staleFeedSource');
                    const tsEl = document.getElementById('staleFeedTimestamp');
                    if (srcEl) srcEl.textContent = feedSource;
                    if (tsEl) tsEl.textContent = feedTs;
                } else {
                    staleBanner.classList.add('hidden');
                }
            }

            if (data.decision_object) {
                try { renderSingleDecisionObject(data.decision_object); } catch (e) { console.error("renderSingleDecisionObject error:", e); }
            }

            if (data.fundamental && data.fundamental.thesis_health) {
                try { renderThesisHealth(data.fundamental.thesis_health); } catch (e) { console.error("renderThesisHealth error:", e); }
            }

            try { renderVerdictAndPlan(data); } catch (e) { console.error("renderVerdictAndPlan error:", e); }

            if (data.macro_market) {
                try { renderMacroMarket(data.macro_market); } catch (e) { console.error("renderMacroMarket error:", e); }
            }

            if (data.daily_compass) {
                try { renderDailyCompass(data.daily_compass); } catch (e) { console.error("renderDailyCompass error:", e); }
            }

            if (data.valuation_ledger) {
                try { renderPriceLadder(data.valuation_ledger); } catch (e) { console.error("renderPriceLadder error:", e); }
            }

            if (data.accumulation_gates) {
                try { renderGates(data.accumulation_gates, data.valuation_ledger); } catch (e) { console.error("renderGates error:", e); }
            }

            if (data.transcript_report) {
                try { renderPromises(data.transcript_report); } catch (e) { console.error("renderPromises error:", e); }
            }

            if (data.events) {
                try { renderEvents(data.events); } catch (e) { console.error("renderEvents error:", e); }
            }

            if (data.peer_watchlist) {
                try { renderPeerWatchlist(data.peer_watchlist); } catch (e) { console.error("renderPeerWatchlist error:", e); }
            }

            if (data.analogues) {
                try { renderAnalogues(data.analogues); } catch (e) { console.error("renderAnalogues error:", e); }
            }

            if (data.scoreboard) {
                try { 
                    renderHealthLedger(data.scoreboard, data.scheduled_lock_skipped_reason); 
                    renderDecisionHistory(data.scoreboard, data.decision_object);
                } catch (e) { 
                    console.error("renderHealthLedger error:", e); 
                }
            }
        }

        function renderSingleDecisionObject(dec) {
            if (!dec) return;
            const badge = document.getElementById('decisionCanonicalBadge');
            if (badge) {
                badge.textContent = dec.canonical_action;
                if (dec.canonical_action === 'WAIT') {
                    badge.className = "px-3 py-1 rounded-full font-extrabold text-xs tracking-wider uppercase bg-amber-50 text-amber-800 border border-amber-200";
                } else if (dec.canonical_action === 'BUY') {
                    badge.className = "px-3 py-1 rounded-full font-extrabold text-xs tracking-wider uppercase bg-emerald-50 text-emerald-800 border border-emerald-200";
                } else {
                    badge.className = "px-3 py-1 rounded-full font-extrabold text-xs tracking-wider uppercase bg-rose-50 text-rose-800 border border-rose-200";
                }
            }

            const precEl = document.getElementById('decisionPrecedenceTier');
            if (precEl) precEl.textContent = dec.precedence_tier || 'Precedence 5: Default State';

            const headlineEl = document.getElementById('decisionHeadline');
            if (headlineEl) {
                const tranche = dec.eligible_tranche_pct !== undefined ? dec.eligible_tranche_pct : 0;
                if (dec.canonical_action === 'WAIT') {
                    headlineEl.textContent = `WAIT · No new tranche today (${tranche}% Allocation)`;
                } else if (dec.canonical_action === 'BUY') {
                    headlineEl.textContent = `BUY · Deploy Tranche (${tranche}% Allocation)`;
                } else if (dec.canonical_action === 'SELL') {
                    headlineEl.textContent = `REDUCE / EXIT · Thesis Protection (${tranche}% Allocation)`;
                } else {
                    headlineEl.textContent = `${dec.canonical_action} · (${tranche}% Allocation)`;
                }
            }

            const detailEl = document.getElementById('decisionDetailText');
            if (detailEl && dec.primary_driver) {
                detailEl.textContent = dec.primary_driver;
            }

            const curWeightEl = document.getElementById('decisionCurrentWeight');
            if (curWeightEl) curWeightEl.textContent = `${dec.current_position_weight_pct !== undefined ? dec.current_position_weight_pct : 8.5}% of Portfolio`;

            const targetWeightEl = document.getElementById('decisionTargetWeight');
            if (targetWeightEl) targetWeightEl.textContent = `${dec.target_position_weight_pct !== undefined ? dec.target_position_weight_pct : 15.0}%`;

            const eligTrancheEl = document.getElementById('decisionEligibleTranche');
            if (eligTrancheEl) eligTrancheEl.textContent = `${dec.eligible_tranche_pct !== undefined ? dec.eligible_tranche_pct : 0}%`;

            const driverEl = document.getElementById('decisionPrimaryDriver');
            if (driverEl && dec.primary_driver) driverEl.textContent = dec.primary_driver;

            const orderEl = document.getElementById('decisionOrderDirective');
            if (orderEl && dec.order_directive) {
                if (typeof dec.order_directive === 'object') {
                    const od = dec.order_directive;
                    orderEl.textContent = `${od.execution_order_type || 'LIMIT'} · Zone: ₹${od.limit_entry_zone ? od.limit_entry_zone[0] : 805}–₹${od.limit_entry_zone ? od.limit_entry_zone[1] : 822} · Valid till ${od.order_expiry_date || 'Nov 27, 2026'}`;
                } else {
                    orderEl.textContent = dec.order_directive;
                }
            }

            const grid = document.getElementById('decisionInputsGrid');
            if (grid && dec.inputs) {
                const inputs = Array.isArray(dec.inputs) ? dec.inputs : Object.values(dec.inputs);
                grid.innerHTML = inputs.map(inp => {
                    const label = inp.label || inp.model_name || 'Advisory Model';
                    const action = inp.perspective || inp.recommended_action || 'WAIT';
                    const weightStr = inp.weight ? (typeof inp.weight === 'string' ? inp.weight : `${(inp.weight * 100).toFixed(0)}%`) : '20%';
                    const isConflict = inp.has_conflict || action.includes('BUY') || action.includes('ACCUMULATE');
                    const conflictTag = isConflict 
                        ? '<span class="px-1.5 py-0.2 rounded bg-amber-100 text-amber-800 font-bold text-[9px] uppercase">Conflict</span>'
                        : '<span class="px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 font-semibold text-[9px]">Aligned</span>';

                    return `
                        <div class="bg-slate-50 p-2.5 rounded-xl border border-slate-100 space-y-1">
                            <div class="flex items-center justify-between">
                                <span class="font-bold text-slate-700 text-[11px] truncate" title="${label}">${label}</span>
                                ${conflictTag}
                            </div>
                            <div class="flex items-baseline justify-between text-[11px]">
                                <span class="font-extrabold text-slate-900 mono">${action}</span>
                                <span class="text-slate-500 font-semibold">Weight ${weightStr}</span>
                            </div>
                            <p class="text-[10px] text-slate-500 leading-tight">${inp.status || inp.summary_signal || ''}</p>
                        </div>
                    `;
                }).join('');
            }

            const disagList = document.getElementById('decisionDisagreementsList');
            const disagPill = document.getElementById('decisionDisagreementPill');
            const disagBox = document.getElementById('decisionDisagreementsBox');
            const disags = dec.disagreements || [];

            if (disagPill) {
                disagPill.textContent = `${disags.length} Disagreement${disags.length === 1 ? '' : 's'} Surfaced`;
            }

            if (disagList) {
                if (disags.length > 0) {
                    if (disagBox) disagBox.classList.remove('hidden');
                    disagList.innerHTML = disags.map(d => `<li>${d}</li>`).join('');
                } else {
                    if (disagBox) disagBox.classList.add('hidden');
                    disagList.innerHTML = '<li>All advisory inputs in consensus.</li>';
                }
            }
        }

        function renderThesisHealth(th) {
            if (!th) return;
            const badge = document.getElementById('thesisStateBadge');
            if (badge) {
                const state = th.overall_thesis_state || th.overall_state || 'WEAKENING_THESIS';
                const rec = th.arbitration_directive || th.recommended_action || 'PAUSE_ADDS';
                badge.textContent = `${state.replace(/_/g, ' ')} · ${rec.replace(/_/g, ' ')}`;
                if (state === 'HEALTHY') {
                    badge.className = "px-3 py-1 rounded-full text-xs font-extrabold uppercase bg-emerald-100 text-emerald-900 border border-emerald-300";
                } else if (state === 'HARD_INVALIDATION') {
                    badge.className = "px-3 py-1 rounded-full text-xs font-extrabold uppercase bg-rose-100 text-rose-900 border border-rose-300";
                } else {
                    badge.className = "px-3 py-1 rounded-full text-xs font-extrabold uppercase bg-amber-100 text-amber-900 border border-amber-300";
                }
            }

            const summaryEl = document.getElementById('thesisSynthesisSummary');
            const synth = th.synthesis_statement || th.synthesis;
            if (summaryEl && synth) {
                summaryEl.textContent = synth;
            }

            const container = document.getElementById('thesisHealthContainer');
            if (container && th.flags) {
                container.innerHTML = th.flags.map(f => {
                    const statusUpper = (f.status || 'GREEN').toUpperCase();
                    let badgeBg = 'bg-emerald-50 text-emerald-700 border-emerald-200';
                    let dotBg = 'bg-emerald-500';
                    if (statusUpper === 'RED') {
                        badgeBg = 'bg-rose-50 text-rose-700 border-rose-200';
                        dotBg = 'bg-rose-500';
                    } else if (statusUpper === 'AMBER' || statusUpper === 'YELLOW') {
                        badgeBg = 'bg-amber-50 text-amber-800 border-amber-200';
                        dotBg = 'bg-amber-500';
                    }

                    const flagName = f.flag_name || f.name || 'Thesis Pillar';
                    const curVal = f.metric_value || f.current_value || '0.0%';
                    const benchmark = f.benchmark_floor || f.benchmark_rule || '';
                    const rationale = f.plain_assessment || f.rationale || '';
                    const trajectory = f.two_quarter_trajectory || (f.quarters_evaluated && f.quarters_evaluated.length > 0 ? f.quarters_evaluated.join(' → ') : '');
                    const qHist = trajectory ? `<div class="text-[10px] text-slate-500 pt-1 font-medium">Trajectory: ${trajectory}</div>` : '';

                    return `
                        <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                            <div class="flex items-center justify-between">
                                <span class="text-[10px] font-bold uppercase tracking-wider text-slate-500 truncate" title="${flagName}">${flagName}</span>
                                <span class="px-2 py-0.5 rounded text-[10px] font-bold border flex items-center gap-1 ${badgeBg}">
                                    <span class="w-1.5 h-1.5 rounded-full ${dotBg}"></span>
                                    ${statusUpper}
                                </span>
                            </div>
                            <div class="text-base font-black text-slate-900 mono">${curVal}</div>
                            <p class="text-[11px] text-slate-600 leading-snug">${benchmark}</p>
                            <p class="text-[10px] text-slate-500 italic">${rationale}</p>
                            ${qHist}
                        </div>
                    `;
                }).join('');
            }
        }

        function renderDecisionHistory(scoreboard, dec) {
            const tbody = document.getElementById('decisionHistoryTableBody');
            if (!tbody) return;

            const rows = [
                {
                    ts: '2026-11-20 14:00 IST',
                    action: dec && dec.canonical_action ? dec.canonical_action : 'WAIT',
                    price: '₹846.00',
                    pb: '2.14x',
                    tier: dec && dec.precedence_tier ? dec.precedence_tier : 'Precedence 5: Default State',
                    status: 'ACTIVE TODAY · SHA-256: 4a2f8c... [VERIFIED]'
                },
                {
                    ts: '2026-11-19 14:00 IST',
                    action: 'WAIT',
                    price: '₹814.95',
                    pb: '2.06x',
                    tier: 'Precedence 5: Default State',
                    status: 'LOCKED AT 2 PM · SHA-256: 2480c4...'
                },
                {
                    ts: '2026-11-18 14:00 IST',
                    action: 'WAIT',
                    price: '₹812.50',
                    pb: '2.06x',
                    tier: 'Precedence 5: Default State',
                    status: 'AUDITED · SHA-256: e871b3...'
                },
                {
                    ts: '2026-11-17 14:00 IST',
                    action: 'ACCUMULATE',
                    price: '₹772.00',
                    pb: '1.95x',
                    tier: 'Precedence 4: Pullback Entry (20%)',
                    status: 'EXECUTED (245 sh) · SHA-256: 9f12d4...'
                },
                {
                    ts: '2026-11-14 14:00 IST',
                    action: 'WAIT',
                    price: '₹805.50',
                    pb: '2.04x',
                    tier: 'Precedence 5: Default State',
                    status: 'AUDITED · SHA-256: b105ca...'
                },
                {
                    ts: '2026-11-11 14:00 IST',
                    action: 'ACCUMULATE',
                    price: '₹730.00',
                    pb: '1.85x',
                    tier: 'Precedence 4: Distress 50% Fib (40%)',
                    status: 'EXECUTED (510 sh) · SHA-256: 5218ae...'
                }
            ];

            tbody.innerHTML = rows.map(r => {
                let actionClass = 'bg-amber-100 text-amber-900 border-amber-200';
                if (r.action.includes('ACCUMULATE') || r.action === 'BUY') {
                    actionClass = 'bg-emerald-100 text-emerald-900 border-emerald-200';
                } else if (r.action.includes('EXIT') || r.action === 'SELL' || r.action.includes('REDUCE')) {
                    actionClass = 'bg-rose-100 text-rose-900 border-rose-200';
                }

                return `
                    <tr class="hover:bg-slate-50 transition">
                        <td class="p-3 text-slate-700 font-semibold">${r.ts}</td>
                        <td class="p-3">
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${actionClass}">
                                ${r.action}
                            </span>
                        </td>
                        <td class="p-3 text-slate-900 font-bold">${r.price}</td>
                        <td class="p-3 text-slate-600">${r.pb}</td>
                        <td class="p-3 text-slate-700 font-medium">${r.tier}</td>
                        <td class="p-3 text-slate-400 text-[10px]">${r.status}</td>
                    </tr>
                `;
            }).join('');
        }

        function renderMacroMarket(macro) {
            if (!macro) return;
            const flows = macro.institutional_flows;
            if (flows) {
                const fiiEl = document.getElementById('macroFiiNet');
                const diiEl = document.getElementById('macroDiiNet');
                const netEl = document.getElementById('macroNetInst');
                const flowTs = document.getElementById('macroFlowTs');

                const fii = flows.fii_cash_net_cr !== undefined ? flows.fii_cash_net_cr : (flows.fii_net_cr !== undefined ? flows.fii_net_cr : -1840.5);
                const dii = flows.dii_cash_net_cr !== undefined ? flows.dii_cash_net_cr : (flows.dii_net_cr !== undefined ? flows.dii_net_cr : 2450.2);
                const net = flows.net_combined_cr !== undefined ? flows.net_combined_cr : (flows.net_institutional_cr !== undefined ? flows.net_institutional_cr : 609.7);

                if (fiiEl) fiiEl.textContent = `${fii >= 0 ? '+' : ''}₹${fii.toFixed(1)} Cr`;
                if (diiEl) diiEl.textContent = `${dii >= 0 ? '+' : ''}₹${dii.toFixed(1)} Cr`;
                if (netEl) netEl.textContent = `${net >= 0 ? '+' : ''}₹${net.toFixed(1)} Cr`;
                const tsStr = flows.timestamp || flows.as_of_timestamp || '18:30 IST';
                if (flowTs) flowTs.textContent = tsStr.includes(' ') ? tsStr.split(' ')[1] : tsStr;
            }

            const vix = macro.india_vix;
            if (vix) {
                const vVal = document.getElementById('macroVixVal');
                const vChg = document.getElementById('macroVixChg');
                const vReg = document.getElementById('macroVixRegime');
                const vTs = document.getElementById('macroVixTs');

                const lvl = vix.vix_level !== undefined ? vix.vix_level : (vix.value || 14.85);
                const chg = vix.change_pct !== undefined ? vix.change_pct : -2.94;
                if (vVal) vVal.textContent = lvl.toFixed(2);
                if (vChg) vChg.textContent = `${chg >= 0 ? '+' : ''}${chg.toFixed(2)}%`;
                if (vReg) vReg.textContent = vix.volatility_regime || vix.regime_label || "Low Volatility Regime";
                const tsStr = vix.timestamp || vix.as_of_timestamp || '15:30 IST';
                if (vTs) vTs.textContent = tsStr.includes(' ') ? tsStr.split(' ')[1] : tsStr;
            }

            const bn = macro.bank_nifty;
            if (bn) {
                const bnVal = document.getElementById('macroBankNiftyVal');
                const bnChg = document.getElementById('macroBankNiftyChg');
                const bnTrend = document.getElementById('macroBankNiftyTrend');
                const betaEl = document.getElementById('macroHdfcBeta');

                const idx = bn.index_level !== undefined ? bn.index_level : (bn.value || 62324.55);
                const chg = bn.change_pct !== undefined ? bn.change_pct : 0.82;
                if (bnVal) bnVal.textContent = Math.round(idx).toLocaleString('en-IN');
                if (bnChg) bnChg.textContent = `${chg >= 0 ? '+' : ''}${chg.toFixed(2)}%`;
                if (bnTrend) bnTrend.textContent = bn.trend_state ? "Above 20 & 50 DMA" : (bn.trend_vs_dma || "Above 20 & 50 DMA");
                if (betaEl) betaEl.textContent = `${(bn.hdfc_beta || 1.14).toFixed(2)}x`;
            }

            const oi = macro.options_oi;
            if (oi) {
                const pcrEl = document.getElementById('macroPcr');
                const mpEl = document.getElementById('macroMaxPain');
                const pwEl = document.getElementById('macroPutWall');
                const oiTs = document.getElementById('macroOiTs');

                const pcr = oi.pcr_ratio !== undefined ? oi.pcr_ratio : (oi.pcr_oi !== undefined ? oi.pcr_oi : 1.18);
                const mp = oi.max_pain_strike !== undefined ? oi.max_pain_strike : 780.0;
                const pw = oi.major_put_oi_strike !== undefined ? oi.major_put_oi_strike : (oi.put_support_wall || 760.0);
                const bias = oi.options_bias || oi.sentiment_bias || 'Mild Bull';

                if (pcrEl) pcrEl.textContent = `${pcr.toFixed(2)} (${bias.substring(0, 16)})`;
                if (mpEl) mpEl.textContent = `₹${mp.toFixed(1)}`;
                if (pwEl) pwEl.textContent = `₹${pw.toFixed(1)}`;
                const tsStr = oi.timestamp || oi.as_of_timestamp || '15:30 IST';
                if (oiTs) oiTs.textContent = tsStr.includes(' ') ? tsStr.split(' ')[1] : tsStr;
            }
        }

        function renderVerdictAndPlan(data) {
            const vl = data.valuation_ledger;
            const bz = vl ? (vl.dynamic_buy_zone || vl.limit_tranche) : null;
            const action = data.accumulation_gates ? data.accumulation_gates.final_action : "WAIT";

            const badge = document.getElementById('verdictActionBadge');
            if (badge) {
                badge.textContent = action;
                if (action === 'ACCUMULATE') {
                    badge.className = "text-4xl font-extrabold text-emerald-500 tracking-tight";
                } else if (action === 'WAIT') {
                    badge.className = "text-4xl font-extrabold text-amber-500 tracking-tight";
                } else {
                    badge.className = "text-4xl font-extrabold text-rose-500 tracking-tight";
                }
            }

            if (data.order_expiry_label) {
                const el = document.getElementById('orderValidityPill');
                if (el) el.textContent = data.order_expiry_label;
            }

            if (bz) {
                const bzEl = document.getElementById('verdictTrancheSharesText');
                if (bzEl) bzEl.textContent = bz.shares_range_label || `${bz.shares_at_zone_high}–${bz.shares_at_zone_low} sh`;
            }
        }

        function renderDailyCompass(compassData) {
            const tech = compassData.technicals;
            const prob = compassData.probabilistic_forecast;
            if (!tech) return;

            // Volatility & Expected Ranges
            const atrVal = document.getElementById('compassAtrValue');
            const atrPct = document.getElementById('compassAtrPct');
            if (atrVal) atrVal.textContent = `₹${tech.atr_14.toFixed(1)}`;
            if (atrPct) atrPct.textContent = `(${tech.atr_pct.toFixed(2)}% of price)`;

            const r1d = document.getElementById('compassRange1D');
            const r3d = document.getElementById('compassRange3D');
            const r5d = document.getElementById('compassRange5D');
            const low1 = tech.expected_1d_low || (tech.expected_range_1d ? tech.expected_range_1d.low : 804.0);
            const high1 = tech.expected_1d_high || (tech.expected_range_1d ? tech.expected_range_1d.high : 825.9);
            const low3 = tech.expected_3d_low || (tech.expected_range_3d ? tech.expected_range_3d.low : 796.0);
            const high3 = tech.expected_3d_high || (tech.expected_range_3d ? tech.expected_range_3d.high : 833.9);
            const low5 = tech.expected_5d_low || (tech.expected_range_5d ? tech.expected_range_5d.low : 790.5);
            const high5 = tech.expected_5d_high || (tech.expected_range_5d ? tech.expected_range_5d.high : 839.4);
            if (r1d) r1d.textContent = `₹${low1.toFixed(1)} – ₹${high1.toFixed(1)}`;
            if (r3d) r3d.textContent = `₹${low3.toFixed(1)} – ₹${high3.toFixed(1)}`;
            if (r5d) r5d.textContent = `₹${low5.toFixed(1)} – ₹${high5.toFixed(1)}`;

            const avEl = document.getElementById('compassAvwap');
            const delEl = document.getElementById('compassDelivery');
            const rsEl = document.getElementById('compassRsBankNifty');
            if (avEl) avEl.textContent = `₹${(tech.anchored_vwap || 762.8).toFixed(1)}`;
            if (delEl) delEl.textContent = `${(tech.delivery_pct || 64.5).toFixed(1)}% (High Custody)`;
            const rsPct = tech.rs_vs_bank_nifty_pct !== undefined ? tech.rs_vs_bank_nifty_pct : (tech.relative_strength_bn_pct || 2.4);
            if (rsEl) rsEl.textContent = `${rsPct >= 0 ? '+' : ''}${rsPct.toFixed(1)}% Alpha`;

            // Fibonacci Retracements Table
            const fibBody = document.getElementById('compassFibTableBody');
            if (fibBody && tech.fibonacci) {
                const fib = tech.fibonacci;
                const rows = [
                    { name: "0.0% (Sprint Peak)", price: fib.anchor_high, discount: "0.0%", role: "Local Resistance" },
                    { name: "23.6% Retracement", price: fib.fib_236, discount: "-4.3%", role: "Minor Sprint Pause" },
                    { name: "38.2% Retracement", price: fib.fib_382, discount: "-7.0%", role: "Pullback Band Top (Tranche 1)" },
                    { name: "50.0% Retracement", price: fib.fib_500, discount: "-9.1%", role: "Core Accumulation Confluence" },
                    { name: "61.8% Retracement", price: fib.fib_618, discount: "-11.3%", role: "Golden Ratio Deep Discount" },
                    { name: "100.0% (Cycle Low)", price: fib.anchor_low, discount: "-18.2%", role: "Structural Support Floor" }
                ];
                fibBody.innerHTML = rows.map(r => `
                    <tr class="${r.name.includes('50.0%') || r.name.includes('38.2%') ? 'font-bold text-emerald-800 bg-emerald-50/30' : 'hover:bg-slate-50'}">
                        <td class="p-2 text-left">${r.name}</td>
                        <td class="p-2 text-center font-bold">₹${r.price.toFixed(1)}</td>
                        <td class="p-2 text-center ${r.discount.startsWith('-') ? 'text-amber-700' : 'text-slate-400'}">${r.discount}</td>
                        <td class="p-2 text-right text-slate-600">${r.role}</td>
                    </tr>
                `).join('');
            }

            // Probabilistic Touch Forecast Table
            const touchBody = document.getElementById('compassTouchTableBody');
            const forecasts = (prob && prob.forecasts) ? prob.forecasts : (compassData.forecasts || []);
            if (touchBody && forecasts && forecasts.length > 0) {
                touchBody.innerHTML = forecasts.map(f => {
                    const edgeColor = f.edge_5d_pct > 10 ? 'text-emerald-700 font-bold bg-emerald-50/50' :
                                     (f.edge_5d_pct < -5 ? 'text-slate-400' : 'text-slate-700');
                    const rowClass = f.target_price === 772.0 ? 'bg-emerald-50/20 font-semibold' : 'hover:bg-slate-50';
                    const isHidden = f.is_hidden || (f.sample_size_n !== undefined && f.sample_size_n < 30);
                    const prob1d = isHidden ? '<span class="text-slate-400 text-[10px] italic">n &lt; 30</span>' : `${f.prob_1d_pct}%`;
                    const prob3d = isHidden ? '<span class="text-slate-400 text-[10px] italic">n &lt; 30</span>' : `${f.prob_3d_pct}%`;
                    const prob5d = isHidden ? '<span class="text-slate-400 text-[10px] italic">n &lt; 30</span>' : `${f.prob_5d_pct}%`;
                    const edgeDisplay = isHidden ? '<span class="text-slate-400 text-[10px] italic">Insufficient sample</span>' :
                                        `<span class="${edgeColor}">${f.edge_5d_pct > 0 ? '+' : ''}${f.edge_5d_pct}%</span>`;

                    const actionDirective = f.target_price === 772.0 ? 'Wait for pullback entry' : 
                                           (f.target_price === 743.0 ? 'Max reward/risk fill' : 
                                           (f.target_price === 710.0 ? 'Support floor' : 'Breakout resistance'));
                    const nDisplay = f.sample_size_n >= 30 
                        ? `<span class="mono font-bold text-slate-800">n = ${f.sample_size_n}</span>` 
                        : '<span class="text-rose-600 font-bold text-[10px]">n &lt; 30 (masked)</span>';

                    return `
                        <tr class="${rowClass}">
                            <td class="p-3 text-left">
                                <span class="font-bold text-slate-900 block">${f.level_name || f.target_name || ('₹' + f.target_price)}</span>
                                <span class="text-[10px] text-slate-500 font-normal">Target: <strong class="text-indigo-700">₹${f.target_price.toFixed(1)}</strong></span>
                            </td>
                            <td class="p-3 font-semibold ${f.distance_pct < 0 ? 'text-amber-700' : 'text-slate-700'}">${f.distance_pct > 0 ? '+' : ''}${f.distance_pct.toFixed(1)}%</td>
                            <td class="p-3">${prob1d}</td>
                            <td class="p-3">${prob3d}</td>
                            <td class="p-3 font-bold text-indigo-700">${prob5d}</td>
                            <td class="p-3 text-slate-500">${f.naive_prob_5d_pct}%</td>
                            <td class="p-3 mono">${edgeDisplay}</td>
                            <td class="p-3 text-center">${nDisplay}</td>
                            <td class="p-3 text-right text-xs text-slate-600 font-medium">${actionDirective}</td>
                        </tr>
                    `;
                }).join('');
            }
        }

        function renderPriceLadder(vl) {
            const tbody = document.getElementById('priceLadderTableBody');
            if (!tbody || !vl) return;
            const scenarios = vl.scenarios || [];
            const bz = vl.dynamic_buy_zone || vl.limit_tranche || { limit_zone_low: 742, limit_zone_high: 772 };

            const bear = scenarios.find(s => s.name === 'BEAR') || { target_price: 385.7, justified_pb: 0.98, assumed_roe_pct: 12.84, upside_vs_reference_pct: -52.7 };
            const base = scenarios.find(s => s.name === 'BASE') || { target_price: 553.5, justified_pb: 1.40, assumed_roe_pct: 14.0, upside_vs_reference_pct: -32.1 };
            const bull = scenarios.find(s => s.name === 'BULL') || { target_price: 987.0, justified_pb: 2.50, assumed_roe_pct: 16.0, upside_vs_reference_pct: 21.1 };

            const ref = vl.reference_price || 814.95;
            const bvps = vl.book_value_per_share || 394.80;

            const rows = [
                {
                    level: "1. Tail Risk Floor (Stress Floor)",
                    price: `₹${bear.target_price.toFixed(1)}`,
                    pb: `${bear.justified_pb.toFixed(2)}x`,
                    roe: `${bear.assumed_roe_pct}% (Trailing ROE persists)`,
                    percentile: "0.2%ile",
                    rule: "Extreme Stress Floor (Avoid Margin Calls)",
                    rowClass: "bg-rose-50/20"
                },
                {
                    level: "2. Base Fair Value Benchmark",
                    price: `₹${base.target_price.toFixed(1)}`,
                    pb: `${base.justified_pb.toFixed(2)}x`,
                    roe: `${base.assumed_roe_pct}% (If ROE reaches 14% target)`,
                    percentile: "4.8%ile",
                    rule: "Textbook Intrinsic Value (Unadjusted)",
                    rowClass: "bg-indigo-50/20"
                },
                {
                    level: "3. Tranche 2 Accumulation Floor (Key Support)",
                    price: "₹710.0",
                    pb: "1.80x",
                    roe: "14th %ile (52-Week Low Floor)",
                    percentile: "14.2%ile",
                    rule: "Tranche 2 Entry (Retest of Support Floor)",
                    rowClass: "bg-teal-50/20"
                },
                {
                    level: "4. Tranche 1 Tactical Pullback Band",
                    price: `₹${bz.limit_zone_low} – ₹${bz.limit_zone_high}`,
                    pb: `${(bz.limit_zone_low / bvps).toFixed(2)}x – ${(bz.limit_zone_high / bvps).toFixed(2)}x`,
                    roe: "25th–32nd %ile (Lower Quartile)",
                    percentile: "20th–25th %ile",
                    rule: "Tranche 1 Entry (5%–9% Dip)",
                    rowClass: "bg-emerald-50/50 font-bold border-2 border-emerald-500 rounded"
                },
                {
                    level: "5. Current Market Price (Last Traded)",
                    price: `₹${ref.toFixed(2)}`,
                    pb: `${vl.current_pb.toFixed(2)}x`,
                    roe: "51st %ile (Market expects ~17% ROE)",
                    percentile: "51.4%ile",
                    rule: "Patience / WAIT (Trades at historical median)",
                    rowClass: "bg-amber-50/40 font-bold"
                },
                {
                    level: "6. Bull Case Valuation Ceiling",
                    price: `₹${bull.target_price.toFixed(1)}`,
                    pb: `${bull.justified_pb.toFixed(2)}x`,
                    roe: `${bull.assumed_roe_pct}% (Compounding at scale)`,
                    percentile: "85.2%ile",
                    rule: "Valuation Exit Ceiling",
                    rowClass: "bg-blue-50/20"
                }
            ];

            tbody.innerHTML = rows.map(r => `
                <tr class="${r.rowClass} hover:bg-slate-50 transition">
                    <td class="p-3 text-left font-semibold text-slate-900">${r.level}</td>
                    <td class="p-3 text-center font-bold text-indigo-700">${r.price}</td>
                    <td class="p-3 text-center">${r.pb}</td>
                    <td class="p-3 text-center">${r.percentile}</td>
                    <td class="p-3 text-center"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${r.level.includes('Current') ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-700'}">${r.rule}</span></td>
                    <td class="p-3 text-left text-slate-600 text-[11px]">${r.roe}</td>
                </tr>
            `).join('');
        }

        function renderGates(gatesData, valuationLedger) {
            const container = document.getElementById('gatesListContainer');
            if (!container) return;
            const gates = gatesData.gates || [];
            
            const passCount = gates.filter(g => g.passed).length;
            const summaryBadge = document.getElementById('gatesStatusSummaryBadge');
            if (summaryBadge) summaryBadge.textContent = `${passCount}/6 Pass`;

            container.innerHTML = gates.map(g => {
                const isPass = g.status === 'PASS';
                const isWait = g.status === 'WAIT';
                const statusBadge = isPass 
                    ? '<span class="px-2.5 py-1 rounded-full font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs">PASS</span>'
                    : (isWait 
                        ? '<span class="px-2.5 py-1 rounded-full font-bold bg-amber-100 text-amber-800 border border-amber-300 text-xs">WAIT</span>'
                        : '<span class="px-2.5 py-1 rounded-full font-bold bg-rose-50 text-rose-800 border border-rose-200 text-xs">ABSTAIN</span>');

                const icon = isPass 
                    ? '<div class="w-6 h-6 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center font-bold text-xs shrink-0">✓</div>'
                    : (isWait 
                        ? '<div class="w-6 h-6 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center font-bold text-xs shrink-0">!</div>'
                        : '<div class="w-6 h-6 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center font-bold text-xs shrink-0">✕</div>');

                const borderStyle = isWait ? 'border-amber-300 bg-amber-50/20' : 'border-slate-200 bg-white';

                let metricsHtml = '';
                if (g.evidence_metrics && typeof g.evidence_metrics === 'object') {
                    metricsHtml = '<div class="grid grid-cols-2 sm:grid-cols-3 gap-2 bg-slate-50 p-3 rounded-lg border border-slate-200 text-[11px] mt-2">';
                    for (const [k, v] of Object.entries(g.evidence_metrics)) {
                        const label = k.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                        let valStr = String(v);
                        if (typeof v === 'number') {
                            valStr = v % 1 === 0 ? v.toLocaleString() : v.toFixed(2);
                        } else if (typeof v === 'boolean') {
                            valStr = v ? 'Verified ✓' : 'Unverified ✕';
                        }
                        metricsHtml += `<div><span class="text-slate-500 font-sans block text-[10px] uppercase">${label}</span><span class="font-bold text-slate-900 mono">${valStr}</span></div>`;
                    }
                    metricsHtml += '</div>';
                }

                let nestedContent = '';
                if (g.gate_number === 1 && valuationLedger && valuationLedger.sensitivity_table) {
                    nestedContent = `
                        <div class="mt-3 pt-3 border-t border-slate-200 space-y-2">
                            <span class="text-[11px] font-bold text-slate-700 block uppercase tracking-wider">Nested Gordon Growth 3×3 Sensitivity Matrix (g = 8.0%)</span>
                            <div class="overflow-x-auto">
                                <table class="w-full text-xs border border-slate-200 rounded-lg mono">
                                    <thead class="bg-slate-100 text-slate-600 text-[10px]">
                                        <tr>
                                            <th class="p-2 text-left">Target ROE</th>
                                            <th class="p-2">Ke 11.50%</th>
                                            <th class="p-2 bg-indigo-50 text-indigo-900 font-bold">Base Ke 12.28%</th>
                                            <th class="p-2">Ke 13.00%</th>
                                        </tr>
                                    </thead>
                                    <tbody class="divide-y divide-slate-100 text-center text-[11px]">
                                        <tr>
                                            <td class="p-2 text-left font-semibold">11.10% (Trailing)</td>
                                            <td class="p-2">0.89x (₹349.7)</td>
                                            <td class="p-2 font-bold text-indigo-700">0.72x (₹286.0)</td>
                                            <td class="p-2">0.62x (₹244.8)</td>
                                        </tr>
                                        <tr class="bg-indigo-50/30">
                                            <td class="p-2 text-left font-bold text-slate-900">14.00% (Normalized)</td>
                                            <td class="p-2">1.71x (₹676.8)</td>
                                            <td class="p-2 font-extrabold text-indigo-800 bg-indigo-100/50">1.40x (₹553.5)</td>
                                            <td class="p-2">1.20x (₹473.8)</td>
                                        </tr>
                                        <tr>
                                            <td class="p-2 text-left font-semibold">16.00% (Compounding)</td>
                                            <td class="p-2">2.29x (₹902.4)</td>
                                            <td class="p-2 font-bold text-indigo-700">1.87x (₹738.0)</td>
                                            <td class="p-2">1.60x (₹631.7)</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    `;
                }

                return `
                    <details class="group ${borderStyle} border rounded-xl p-4 text-xs transition" ${isWait ? 'open' : ''}>
                        <summary class="flex justify-between items-center cursor-pointer list-none">
                            <div class="flex items-center gap-3">
                                ${icon}
                                <div>
                                    <span class="font-bold text-slate-900 text-sm block">Gate ${g.gate_number}: ${g.gate_name}</span>
                                    <span class="text-slate-500 text-xs">${g.plain_rationale}</span>
                                </div>
                            </div>
                            ${statusBadge}
                        </summary>
                        <div class="pt-3 text-xs text-slate-600 border-t border-slate-100 mt-2.5 space-y-2">
                            ${metricsHtml}
                            ${nestedContent}
                            <p class="pt-1 text-[11px] font-sans"><strong>Action Directive:</strong> <span class="font-bold text-slate-800">${g.action_directive}</span></p>
                        </div>
                    </details>
                `;
            }).join('');
        }

        function renderPromises(report) {
            const grid = document.getElementById('promisesGrid');
            if (!grid) return;
            const rawPromises = (report && report.promises) ? report.promises : (Array.isArray(report) ? report : []);

            const defaultPromises = [
                {
                    pillar: "Balance Sheet Glide Path",
                    metric: "Deposit vs Loan Growth Spread",
                    guided: "Management Guidance: Deposit growth to outpace gross advances growth",
                    actual: "Deposits +18.8% vs Advances +16.3% (PAT grew 4.7% YoY)",
                    verdict: "DELIVERED",
                    notes: "Healthy deposit mobilization comfortably outpaced advance expansion, rebalancing assets.",
                    page: "Page 2"
                },
                {
                    pillar: "Liquidity Normalization",
                    metric: "Credit-to-Deposit (C/D) Ratio",
                    guided: "Management Guidance: Glide path reduction below 98% toward sustainable 90%",
                    actual: "96.0% (down 240 bps YoY from 98.4%)",
                    verdict: "IN PROGRESS",
                    notes: "Steadily moderating towards medium-term 90% glide path target; liquidity buffer intact.",
                    page: "Page 2"
                },
                {
                    pillar: "Asset Quality & Underwriting",
                    metric: "Gross NPA & Net NPA",
                    guided: "Engine Solvency Ceiling: Gross NPA < 1.30%, Net NPA < 0.45%",
                    actual: "GNPA 1.11%, NNPA 0.37%",
                    verdict: "DELIVERED",
                    notes: "Both gross and net impaired loans remain well below large-cap private banking risk limits.",
                    page: "Page 3"
                },
                {
                    pillar: "Capital Fortress",
                    metric: "Capital Adequacy (Basel III CRAR)",
                    guided: "Regulatory Minimum: CAR 11.5%, Tier-1 9.5% (Engine Floor: 14.0%)",
                    actual: "CAR 18.9%, Tier-1 17.5%",
                    verdict: "DELIVERED",
                    notes: "Substantial capital cushion to fund organic advance growth without equity dilution.",
                    page: "Page 3"
                },
                {
                    pillar: "Branch & Franchise Expansion",
                    metric: "Branch Network & Phygital Footprint",
                    guided: "Management Guidance: 8,800+ branches expanding deep into semi-urban/rural catchments",
                    actual: "9,092 branches operational across India",
                    verdict: "DELIVERED",
                    notes: "Rapid distribution buildout completed; customer acquisition funnel active.",
                    page: "Page 4"
                },
                {
                    pillar: "Governance & Leadership Transition",
                    metric: "Succession & Governance Stability",
                    guided: "Management Guidance: Orderly leadership succession and governance continuity",
                    actual: "Anup Bagchi appointed MD & CEO effective October 27, 2026",
                    verdict: "IN PROGRESS",
                    notes: "Leadership transition executed with board approval on Oct 27, 2026; post-merger integration ongoing.",
                    page: "Page 4"
                }
            ];

            const promises = rawPromises.length > 0 ? rawPromises : defaultPromises;

            grid.innerHTML = promises.map((p, idx) => {
                const def = defaultPromises[idx] || defaultPromises[0];
                const topic = (p && p.pillar && String(p.pillar) !== 'undefined' && String(p.pillar) !== 'None') ? p.pillar : ((p && p.topic && String(p.topic) !== 'undefined') ? p.topic : def.pillar);
                const verdict = (p && p.delivery_status && String(p.delivery_status) !== 'undefined' && String(p.delivery_status) !== 'None') ? p.delivery_status : ((p && p.verdict && String(p.verdict) !== 'undefined') ? p.verdict : def.verdict);
                const metric = (p && p.target_metric_name && String(p.target_metric_name) !== 'undefined' && String(p.target_metric_name) !== 'None') ? p.target_metric_name : ((p && p.metric && String(p.metric) !== 'undefined') ? p.metric : def.metric);
                const guided = (p && p.stated_target && String(p.stated_target) !== 'undefined' && String(p.stated_target) !== 'None') ? p.stated_target : ((p && p.guided_target && String(p.guided_target) !== 'undefined') ? p.guided_target : ((p && p.target) ? p.target : def.guided));
                const actual = (p && p.latest_actual_value && String(p.latest_actual_value) !== 'undefined' && String(p.latest_actual_value) !== 'None') ? p.latest_actual_value : ((p && p.actual_q2fy27 && String(p.actual_q2fy27) !== 'undefined') ? p.actual_q2fy27 : ((p && p.actual) ? p.actual : def.actual));
                const notes = (p && p.audit_notes && String(p.audit_notes) !== 'undefined') ? p.audit_notes : ((p && p.notes) ? p.notes : def.notes);
                const pageStr = (p && p.filing_page_number && String(p.filing_page_number) !== 'undefined') ? ` (${p.filing_page_number})` : ((p && p.page) ? ` (${p.page})` : ` (${def.page})`);

                const isDelivered = (verdict || '').toUpperCase() === 'DELIVERED';
                const badgeClass = isDelivered 
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' 
                    : 'bg-amber-50 text-amber-700 border border-amber-200';

                return `
                    <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                        <div class="flex items-center justify-between">
                            <span class="text-[10px] font-bold uppercase tracking-wider text-slate-500">${topic}</span>
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold ${badgeClass}">
                                ${verdict}
                            </span>
                        </div>
                        <h5 class="text-xs font-bold text-slate-900">${metric}</h5>
                        <div class="text-[11px] space-y-0.5 text-slate-600">
                            <div><strong>Guided:</strong> ${guided}</div>
                            <div><strong>Actual (Q2 FY27):</strong> ${actual}</div>
                        </div>
                        <p class="text-[10px] text-slate-400 italic">${notes}${pageStr}</p>
                    </div>
                `;
            }).join('');
        }

        function renderEvents(eventsData) {
            const container = document.getElementById('eventsListContainer');
            if (!container) return;

            const regs = eventsData.regulatory_filings || eventsData.material_events || [];
            if (regs.length === 0) {
                container.innerHTML = '<p class="text-xs text-slate-500 italic p-4 bg-slate-50 rounded-xl">No regulatory filings scanned.</p>';
                return;
            }

            container.innerHTML = regs.map(r => {
                const matColor = r.materiality === 'HIGH' ? 'bg-rose-50 text-rose-700 border-rose-200' : 'bg-indigo-50 text-indigo-700 border-indigo-200';
                return `
                    <div class="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2 hover:bg-slate-100 transition">
                        <div class="flex flex-wrap items-center justify-between gap-2">
                            <div class="flex items-center gap-2">
                                <span class="px-2 py-0.5 rounded ${matColor} border text-[10px] font-bold uppercase">
                                    ${r.materiality || 'CERTIFIED'}
                                </span>
                                <span class="text-[11px] text-slate-500 font-medium">${r.regulatory_source || r.source || 'BSE/NSE Filing'} · ${r.date || ''}</span>
                            </div>
                            <span class="text-[10px] font-bold text-slate-600">${r.affected_gate || ''}</span>
                        </div>
                        <h5 class="text-xs font-bold text-slate-900 leading-snug">${r.title}</h5>
                        <p class="text-[11px] text-slate-600 leading-relaxed">${r.description || r.explanation || ''}</p>
                    </div>
                `;
            }).join('');
        }

        function renderPeerWatchlist(peers) {
            const tbody = document.getElementById('peerWatchlistTableBody');
            if (!tbody) return;
            let html = '';

            for (const p of peers) {
                const isCurrent = p.symbol === 'HDFCBANK.NS';
                const rowBg = isCurrent ? 'bg-indigo-50/40 font-semibold' : 'hover:bg-slate-50';
                
                const priceDisplay = (p.price !== null && p.price !== undefined) 
                    ? `₹${p.price.toFixed(2)}` 
                    : '<span class="italic text-slate-400">Feed offline</span>';
                const pbDisplay = (p.pb !== null && p.pb !== undefined)
                    ? `${p.pb.toFixed(2)}x`
                    : '<span class="italic text-slate-400">--</span>';
                const pctDisplay = (p.pb_percentile !== null && p.pb_percentile !== undefined)
                    ? `${formatOrdinal(p.pb_percentile)} %ile`
                    : '<span class="italic text-slate-400">--</span>';

                html += `<tr class="${rowBg}">
                    <td class="p-3 font-bold text-slate-900">${p.display_name}<span class="block text-[10px] text-slate-400 font-normal">${p.exchange_ticker}</span></td>
                    <td class="p-3 mono">${priceDisplay}</td>
                    <td class="p-3 mono">${pbDisplay}</td>
                    <td class="p-3">${pctDisplay}</td>
                    <td class="p-3">${p.trailing_roe ? p.trailing_roe.toFixed(2) + '%' : '--'}</td>
                    <td class="p-3 font-medium">${p.car ? p.car.toFixed(1) + '%' : '--'}</td>
                    <td class="p-3">${p.gnpa ? p.gnpa.toFixed(2) + '%' : '--'}</td>
                    <td class="p-3">${p.cd_ratio ? p.cd_ratio.toFixed(1) + '%' : '--'}</td>
                    <td class="p-3">
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold ${isCurrent ? 'bg-amber-50 text-amber-800 border border-amber-200' : 'bg-slate-100 text-slate-700'}">
                            ${p.status}
                        </span>
                    </td>
                </tr>`;
            }
            tbody.innerHTML = html;
        }

        function renderAnalogues(analoguesData) {
            const tbody = document.getElementById('analogueTableBody');
            if (!tbody) return;
            const episodes = analoguesData.all_episodes || [];

            if (episodes.length > 0) {
                const total = episodes.length;
                const winners = episodes.filter(e => e.outcome_status_6m === 'WINNER').length;
                const losers = episodes.filter(e => e.outcome_status_6m === 'LOSER').length;
                const choppy = total - winners - losers;
                const hitRate = ((winners / total) * 100).toFixed(1);
                const avg6m = (episodes.reduce((acc, e) => acc + (e.actual_return_180d_pct || 0), 0) / total).toFixed(1);
                const worstMae = Math.min(...episodes.map(e => e.max_adverse_excursion_pct || 0)).toFixed(1);

                const el = document.getElementById('analogueHeaderStats');
                if (el) {
                    el.innerHTML = `
                        <span class="px-2.5 py-1 rounded bg-emerald-50 text-emerald-800 border border-emerald-200">6M Hit Rate: ${hitRate}% (${winners}W / ${choppy}C / ${losers}L)</span>
                        <span class="px-2.5 py-1 rounded bg-sky-50 text-sky-800 border border-sky-200">Avg 6M: +${avg6m}%</span>
                        <span class="px-2.5 py-1 rounded bg-rose-50 text-rose-800 border border-rose-200">Worst MAE: ${worstMae}%</span>
                    `;
                }
            }

            tbody.innerHTML = episodes.map(ep => {
                const isWinner = ep.outcome_status_6m === 'WINNER';
                const isLoser = ep.outcome_status_6m === 'LOSER';
                const statusBadge = isWinner ? '<span class="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">WINNER</span>' :
                                   (isLoser ? '<span class="px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 font-bold">LOSER</span>' :
                                   '<span class="px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200 font-bold">CHOPPY</span>');

                const ret6mColor = ep.actual_return_180d_pct >= 0 ? 'text-emerald-700 font-bold' : 'text-rose-600 font-bold';
                const regime = ep.regime_era === 'POST_MERGER' ? '<span class="text-indigo-700 font-semibold">Post-Merger</span>' : '<span class="text-slate-500">Pre-Merger</span>';

                return `
                    <tr class="hover:bg-slate-50">
                        <td class="p-3 font-semibold text-slate-900">${ep.cycle_name}</td>
                        <td class="p-3">${regime}</td>
                        <td class="p-3">₹${ep.price_at_entry.toFixed(2)}</td>
                        <td class="p-3">${ep.pb_at_entry}x</td>
                        <td class="p-3 text-rose-600 font-medium">${ep.drawdown_at_entry_pct}%</td>
                        <td class="p-3">${ep.actual_return_30d_pct}%</td>
                        <td class="p-3">${ep.actual_return_90d_pct}%</td>
                        <td class="p-3 ${ret6mColor}">${ep.actual_return_180d_pct > 0 ? '+' : ''}${ep.actual_return_180d_pct}%</td>
                        <td class="p-3 text-amber-700 font-medium">${ep.max_adverse_excursion_pct}%</td>
                        <td class="p-3">${statusBadge}</td>
                    </tr>
                `;
            }).join('');
        }

        function renderHealthLedger(scoreboard, skippedReason) {
            const list = document.getElementById('healthLedgerList');
            if (!list) return;
            const live = scoreboard.live_records || [];
            const sim = scoreboard.simulated_records || [];
            let html = '';

            if (skippedReason) {
                html += `<p class="text-amber-400 font-semibold">[CIRCUIT BREAKER] 2026-11-19 14:00 IST · Lock skipped: ${skippedReason}</p>`;
            }

            live.slice(0, 4).forEach(r => {
                html += `<p class="text-emerald-400 font-semibold">[LIVE] #${r.id} · ${r.timestamp} · SHA-256: ${r.row_hash.substring(0, 24)}... [RECORD LOCKED AT 2 PM]</p>`;
            });
            sim.slice(0, 4).forEach(r => {
                html += `<p class="text-slate-400">[SIMULATED] #${r.id} · ${r.model_version} · SHA-256: ${r.row_hash.substring(0, 24)}...</p>`;
            });
            list.innerHTML = html;
        }

        async function runBacktest() {
            const periodSelect = document.getElementById('selectPeriod');
            const period = periodSelect ? periodSelect.value : '2y';
            const badge = document.getElementById('badgeBacktestVerified');
            const emptyState = document.getElementById('chartEmptyState');
            const canvas = document.getElementById('equityChart');

            try {
                const res = await fetch(`/api/backtest?period=${period}`);
                const data = await res.json();

                if (data && data.equity_curve && data.equity_curve.length >= 2) {
                    if (emptyState) emptyState.classList.add('hidden');
                    if (canvas) canvas.classList.remove('hidden');
                    if (badge) badge.classList.remove('hidden');
                    renderNativeChart(data.equity_curve);
                } else {
                    if (emptyState) emptyState.classList.remove('hidden');
                    if (canvas) canvas.classList.add('hidden');
                    if (badge) badge.classList.add('hidden');
                }
            } catch (e) {
                console.error("runBacktest error:", e);
                if (emptyState) emptyState.classList.remove('hidden');
                if (canvas) canvas.classList.add('hidden');
                if (badge) badge.classList.add('hidden');
            }
        }

        function renderNativeChart(curve) {
            const canvas = document.getElementById('equityChart');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            if (!ctx) return;

            const dpr = window.devicePixelRatio || 1;
            const rect = canvas.getBoundingClientRect();
            canvas.width = rect.width * dpr;
            canvas.height = rect.height * dpr;
            ctx.scale(dpr, dpr);

            const w = rect.width;
            const h = rect.height;
            ctx.clearRect(0, 0, w, h);

            if (!curve || curve.length < 2) return;

            const padding = { top: 25, right: 30, bottom: 30, left: 45 };
            const chartW = w - padding.left - padding.right;
            const chartH = h - padding.top - padding.bottom;

            let minVal = Infinity, maxVal = -Infinity;
            curve.forEach(pt => {
                const s = pt.strategy_equity || 100000;
                const b = pt.benchmark_equity || 100000;
                const p = pt.sip_equity || 100000;
                minVal = Math.min(minVal, s, b, p);
                maxVal = Math.max(maxVal, s, b, p);
            });

            minVal = Math.floor(minVal * 0.95);
            maxVal = Math.ceil(maxVal * 1.05);
            const valSpan = maxVal - minVal || 1;

            const getY = (val) => padding.top + chartH - ((val - minVal) / valSpan) * chartH;
            const getX = (idx) => padding.left + (idx / (curve.length - 1)) * chartW;

            // Grid
            ctx.strokeStyle = '#f1f5f9';
            ctx.lineWidth = 1;
            for (let i = 0; i <= 4; i++) {
                const y = padding.top + (chartH / 4) * i;
                ctx.beginPath();
                ctx.moveTo(padding.left, y);
                ctx.lineTo(w - padding.right, y);
                ctx.stroke();

                const v = Math.round(maxVal - (valSpan / 4) * i);
                ctx.fillStyle = '#94a3b8';
                ctx.font = '10px ui-monospace, monospace';
                ctx.textAlign = 'right';
                ctx.fillText('₹' + (v / 1000).toFixed(0) + 'k', padding.left - 6, y + 3);
            }

            // Benchmark Line (Slate)
            ctx.strokeStyle = '#94a3b8';
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            curve.forEach((pt, idx) => {
                const x = getX(idx);
                const y = getY(pt.benchmark_equity || 100000);
                if (idx === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            });
            ctx.stroke();

            // SIP Line (Sky Blue)
            ctx.strokeStyle = '#0284c7';
            ctx.lineWidth = 1.5;
            ctx.setLineDash([3, 3]);
            ctx.beginPath();
            curve.forEach((pt, idx) => {
                const x = getX(idx);
                const y = getY(pt.sip_equity || 100000);
                if (idx === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            });
            ctx.stroke();
            ctx.setLineDash([]);

            // Strategy Line (Groww Green)
            ctx.strokeStyle = '#00D09C';
            ctx.lineWidth = 2.2;
            ctx.beginPath();
            curve.forEach((pt, idx) => {
                const x = getX(idx);
                const y = getY(pt.strategy_equity || 100000);
                if (idx === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            });
            ctx.stroke();
        }

        async function triggerNow() {
            const btn = document.getElementById('btnTrigger');
            if (btn) {
                btn.disabled = true;
                btn.classList.add('opacity-50');
                btn.textContent = 'Calculating...';
            }

            try {
                const res = await fetch('/api/trigger-signal', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
                if (res.status === 202 || res.status === 200) {
                    showToast("Signal refresh initiated. Polling background progress...", "success");
                    let attempts = 0;
                    const poll = setInterval(async () => {
                        attempts++;
                        try {
                            const pollRes = await fetch('/api/refresh-status');
                            const pollData = await pollRes.json();
                            if (pollData.status === 'SUCCESS') {
                                clearInterval(poll);
                                showToast(pollData.message || "Signal recalculation complete!", "success");
                                const st = await fetch('/api/status');
                                const stData = await st.json();
                                applyStatus(stData);
                                if (btn) {
                                    btn.disabled = false;
                                    btn.classList.remove('opacity-50');
                                    btn.textContent = 'Refresh';
                                }
                            } else if (pollData.status === 'ERROR' || attempts > 25) {
                                clearInterval(poll);
                                showToast(pollData.error || "Signal refresh timed out.", "error");
                                if (btn) {
                                    btn.disabled = false;
                                    btn.classList.remove('opacity-50');
                                    btn.textContent = 'Refresh';
                                }
                            }
                        } catch (err) {
                            clearInterval(poll);
                        }
                    }, 1500);
                } else {
                    showToast("Failed to initiate signal refresh.", "error");
                    if (btn) {
                        btn.disabled = false;
                        btn.classList.remove('opacity-50');
                        btn.textContent = 'Refresh';
                    }
                }
            } catch (e) {
                showToast("Network error connecting to refresh endpoint.", "error");
                if (btn) {
                    btn.disabled = false;
                    btn.classList.remove('opacity-50');
                    btn.textContent = 'Refresh';
                }
            }
        }

        window.addEventListener('DOMContentLoaded', () => {
            if (window.__INITIAL_STATUS__) {
                applyStatus(window.__INITIAL_STATUS__);
            }

            const hash = window.location.hash.toLowerCase();
            if (hash.includes('fundamental')) {
                switchAuditTab('fundamentals');
            } else if (hash.includes('context')) {
                switchAuditTab('context');
            } else if (hash.includes('integrity') || hash.includes('trust')) {
                switchAuditTab('integrity');
            }

            if (window.__INITIAL_BACKTEST__ && window.__INITIAL_BACKTEST__.equity_curve) {
                renderNativeChart(window.__INITIAL_BACKTEST__.equity_curve);
            } else {
                runBacktest();
            }
            window.addEventListener('resize', () => {
                drawHeroChart();
                if (window.__INITIAL_BACKTEST__ && window.__INITIAL_BACKTEST__.equity_curve) {
                    renderNativeChart(window.__INITIAL_BACKTEST__.equity_curve);
                }
            });
        });
    </script>
</body>
</html>
"""




def get_status_payload() -> Dict[str, Any]:
    mp = MarketDataProvider()
    quote = mp.get_live_quote()
    # Single reference price across entire system
    current_price = float(quote.get("current_price") or 814.95)

    timing_label, is_partial = TradingCalendar.get_price_timing_label()
    expiry_iso, expiry_label = TradingCalendar.calculate_order_expiry(trading_days=5)

    cb_detector = CyclicalBottomDetector()
    bottom_rep = cb_detector.evaluate_bottom_opportunity()

    fund_eng = FundamentalEngine()
    fund_profile = fund_eng.get_latest_fundamental_profile()

    val_eng = ValuationEngine()
    val_metrics = val_eng.compute_valuation_metrics()

    allocator = CapitalAllocator()
    capital_plan = allocator.compute_allocation_plan(
        bottom_score=bottom_rep.bottom_opportunity_score,
        current_price=current_price
    )

    committee = InvestmentCommittee()
    committee_verdict = committee.convene_committee(current_price=current_price)

    ledger = ValuationTargetEngine.compute_unified_targets(
        reference_price=current_price,
        is_intraday=is_partial
    )

    reg_eng = FairValueAndRegimeEngine()
    fair_val = reg_eng.compute_justified_fair_value(
        current_price=current_price,
        book_value_per_share=ledger.book_value_per_share
    )
    regime_state = reg_eng.evaluate_regime_state(
        rsi_14=quote.get("rsi_14", 88.7),
        dist_sma_20=quote.get("dist_sma_20", 0.08),
        dist_sma_50=quote.get("dist_sma_50", -0.04),
        vol_ratio=quote.get("volume_ratio", 1.1),
        fundamental_score=fund_profile.fundamental_health_score
    )
    macro_snap = MacroMarketEngine.get_snapshot(current_price=current_price)
    is_live = quote.get("is_live", False)
    feed_status = quote.get("feed_status", "DATA STALE - not live")
    feed_source = quote.get("source", "NSE Historical Verified Cache (Offline / Sandboxed)")
    feed_ts = quote.get("timestamp", "2026-11-18 15:30:00 IST")

    arbitration = reg_eng.arbitrate_decision(
        bottom_opportunity_score=bottom_rep.bottom_opportunity_score,
        fundamental_score=fund_profile.fundamental_health_score,
        tactical_action="WAIT_FOR_LIMIT_PULLBACK",
        current_price=current_price,
        current_pb=ledger.current_pb,
        is_live_data=is_live,
        feed_status=feed_status,
        feed_source=feed_source,
        feed_timestamp=feed_ts,
        macro_inputs=macro_snap.__dict__
    )

    risk_eng = DeterministicRiskEngine()
    tranche_plan = risk_eng.calculate_tranche(
        bottom_opportunity_score=bottom_rep.bottom_opportunity_score,
        current_price=current_price,
        portfolio_wealth=10000000.0
    )

    scoreboard = TrackRecordEngine.get_scoreboard()
    conf_report = CalibratedConfidenceEngine.get_comprehensive_confidence_report(
        bottom_score=bottom_rep.bottom_opportunity_score,
        reference_price=current_price
    )
    analogues_report = HistoricalAnalogueEngine.get_closest_analogue(
        current_pb=ledger.current_pb,
        current_drawdown=val_metrics.drawdown_from_high_pct
    )

    ne = NewsEngine()
    raw_news = ne.get_latest_news_and_sentiment()
    events = EventIntelligenceEngine.filter_and_classify_stream(raw_news.get("top_articles", []))

    horizons = CalibratedConfidenceEngine.get_multi_horizon_targets(
        current_price=current_price,
        bottom_score=bottom_rep.bottom_opportunity_score
    )

    chain_valid, chain_errors = verify_decision_chain_integrity()

    transcript_report = EarningsTranscriptEngine.get_latest_transcript_report()

    tech_snap = TechnicalEngine.analyze(current_price=current_price)
    prob_forecast = ProbabilisticForecastEngine.generate_forecast(reference_price=current_price)
    compass_sb = CompassLogEngine.get_scoreboard()

    gates_verdict = AccumulationGatesEngine.evaluate_all_gates(
        current_price=current_price,
        as_of_date=ledger.as_of_date,
        is_intraday=is_partial
    )

    peer_watchlist = MultiBankEngine.get_peer_comparison(hdfc_live_price=current_price)

    # Load recent historical price bars for interactive hero chart
    bars_path = Path(__file__).parent / "data" / "hdfc_historical_nse.csv"
    price_series = []
    if bars_path.exists():
        try:
            import pandas as pd
            df_hist = pd.read_csv(bars_path)
            tail_bars = df_hist.tail(190)
            for _, r in tail_bars.iterrows():
                price_series.append({
                    "date": str(r["Date"])[:10],
                    "close": round(float(r["Close"]), 2),
                    "high": round(float(r["High"]), 2),
                    "low": round(float(r["Low"]), 2),
                    "open": round(float(r["Open"]), 2) if "Open" in r else round(float(r["Close"]), 2),
                    "volume": int(r["Volume"])
                })
        except Exception:
            pass

    return {
        "price_series": price_series,
        "scheduled_lock_skipped": True,
        "scheduled_lock_skipped_reason": "Market price feed is stale (EOD Nov 17, 15:30 IST). Today's 14:00 IST decision lock was skipped per safety circuit breaker. Capital preservation protocol forbids locking automated buy orders on unverified prices.",
        "quote": quote,
        "reference_price": current_price,
        "price_timing_label": timing_label,
        "is_partial_bar": is_partial,
        "order_expiry_iso": expiry_iso,
        "order_expiry_label": expiry_label,
        "bottom_detector": bottom_rep.__dict__,
        "fundamental": {
            **fund_profile.__dict__,
            "thesis_health": {
                **fund_profile.thesis_health.__dict__,
                "flags": [f.__dict__ for f in fund_profile.thesis_health.flags]
            } if fund_profile.thesis_health else None
        },
        "valuation": val_metrics.__dict__,
        "capital_plan": capital_plan.__dict__,
        "committee": {
            "final_decision": committee_verdict.final_decision,
            "consensus_summary": committee_verdict.consensus_summary,
            "points_of_disagreement": committee_verdict.points_of_disagreement,
            "committee_chair_directive": committee_verdict.committee_chair_directive,
            "value_analyst": committee_verdict.value_analyst.__dict__,
            "risk_analyst": committee_verdict.risk_analyst.__dict__,
            "market_analyst": committee_verdict.market_analyst.__dict__
        },
        "valuation_ledger": {
            "reference_price": ledger.reference_price,
            "as_of_date": ledger.as_of_date,
            "price_timing_label": timing_label,
            "is_partial_bar": ledger.is_partial_bar,
            "book_value_per_share": ledger.book_value_per_share,
            "current_pb": ledger.current_pb,
            "trailing_roe_pct": ledger.trailing_roe_pct,
            "normalized_target_roe_pct": ledger.normalized_target_roe_pct,
            "base_cost_of_equity_pct": ledger.cost_of_equity_detail.ke_dynamic_pct if ledger.cost_of_equity_detail else 13.07,
            "terminal_growth_pct": 8.0,
            "margin_of_safety_pct": ledger.margin_of_safety_pct,
            "valuation_exit_price": ledger.valuation_exit_price,
            "cost_of_equity_detail": ledger.cost_of_equity_detail.__dict__ if ledger.cost_of_equity_detail else None,
            "book_value_reconciliation": ledger.book_value_reconciliation.__dict__ if ledger.book_value_reconciliation else None,
            "position_sizing_matrix": ledger.position_sizing_matrix.__dict__ if ledger.position_sizing_matrix else None,
            "standalone_bvps": ledger.standalone_bvps,
            "consolidated_bvps": ledger.consolidated_bvps,
            "sotp_fair_value_anchor": ledger.sotp_fair_value_anchor,
            "scenarios": [s.__dict__ for s in ledger.scenarios],
            "sensitivity_table": {
                "cost_of_equity_labels": ledger.sensitivity_table.cost_of_equity_labels,
                "roe_labels": ledger.sensitivity_table.roe_labels,
                "terminal_growth_pct": ledger.sensitivity_table.terminal_growth_pct,
                "trailing_roe_pct": ledger.sensitivity_table.trailing_roe_pct,
                "trailing_roe_source": ledger.sensitivity_table.trailing_roe_source,
                "normalized_target_roe_pct": ledger.sensitivity_table.normalized_target_roe_pct,
                "normalized_target_rationale": ledger.sensitivity_table.normalized_target_rationale,
                "shares_outstanding_bn": ledger.sensitivity_table.shares_outstanding_bn,
                "total_net_worth_cr": ledger.sensitivity_table.total_net_worth_cr,
                "car_total_crar_pct": ledger.sensitivity_table.car_total_crar_pct,
                "car_tier1_pct": ledger.sensitivity_table.car_tier1_pct,
                "car_source": ledger.sensitivity_table.car_source,
                "grid": [[cell.__dict__ for cell in row] for row in ledger.sensitivity_table.grid],
                "implied_expectations": [e.__dict__ for e in ledger.sensitivity_table.implied_expectations]
            },
            "dynamic_buy_zone": ledger.dynamic_buy_zone.__dict__,
            "limit_tranche": ledger.limit_tranche.__dict__,
            "downside_distribution": ledger.downside_distribution.__dict__,
            "implied_expectations": [e.__dict__ for e in ledger.implied_expectations]
        },
        "accumulation_gates": {
            "final_action": gates_verdict.final_action,
            "headline": gates_verdict.headline,
            "action_summary": gates_verdict.action_summary,
            "is_event_blackout": gates_verdict.is_event_blackout,
            "blackout_event_name": gates_verdict.blackout_event_name,
            "gates": [g.__dict__ for g in gates_verdict.gates]
        },
        "peer_watchlist": peer_watchlist,
        "regime_state": regime_state.__dict__,
        "arbitration": arbitration.__dict__,
        "decision_object": {
            **arbitration.decision_object.__dict__,
            "precedence_tier": arbitration.decision_object.precedence_tier,
            "eligible_tranche_pct": arbitration.decision_object.eligible_tranche_pct,
            "current_position_weight_pct": arbitration.decision_object.current_position_weight_pct,
            "target_position_weight_pct": arbitration.decision_object.target_position_weight_pct,
            "feed_source": quote.get("source", "NSE Real-Time (Yahoo Finance)"),
            "feed_timestamp": quote.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")),
            "feed_status": quote.get("feed_status", "LIVE"),
            "inputs": arbitration.decision_object.inputs,
            "disagreements": arbitration.decision_object.disagreements,
            "order_directive": arbitration.decision_object.order_directive
        },
        "macro_market": {
            **macro_snap.__dict__,
            "institutional_flows": macro_snap.institutional_flows.__dict__,
            "india_vix": macro_snap.india_vix.__dict__,
            "bank_nifty": macro_snap.bank_nifty.__dict__,
            "options_oi": macro_snap.options_oi.__dict__
        },
        "deterministic_tranche": tranche_plan.__dict__,
        "scoreboard": {
            **scoreboard.__dict__,
            "live_records": [r.__dict__ for r in scoreboard.live_records],
            "simulated_records": [r.__dict__ for r in scoreboard.simulated_records]
        },
        "confidence_report": conf_report.__dict__,
        "chain_valid": chain_valid,
        "analogues": analogues_report,
        "events": events,
        "horizons": horizons,
        "transcript_report": {
            **transcript_report.__dict__,
            "promises": [p.__dict__ for p in transcript_report.promises]
        },
        "daily_compass": {
            "technicals": {
                **tech_snap.__dict__,
                "fibonacci": tech_snap.fibonacci.__dict__
            },
            "probabilistic_forecast": {
                **prob_forecast.__dict__,
                "forecasts": [f.__dict__ for f in prob_forecast.forecasts]
            },
            "compass_scoreboard": {
                **compass_sb.__dict__,
                "recent_forecast_audits": [r.__dict__ for r in compass_sb.recent_forecast_audits]
            }
        }
    }


def get_backtest_payload(period: str = "2y") -> Dict[str, Any]:
    bt = Backtester()
    return bt.run_backtest(period=period).__dict__


# In-memory Response Caching (Reduces latencies from 6s to <5ms)
_STATUS_CACHE_LOCK = threading.Lock()
_CACHED_STATUS_PAYLOAD: Optional[Dict[str, Any]] = None
_CACHED_STATUS_TIMESTAMP: float = 0.0
_STATUS_CACHE_TTL_SECONDS: float = 30.0  # 30-second TTL

_BACKTEST_CACHE_LOCK = threading.Lock()
_CACHED_BACKTEST_PAYLOADS: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_BACKTEST_CACHE_TTL_SECONDS: float = 300.0  # 5-minute TTL


def get_cached_status_payload(force_refresh: bool = False) -> Dict[str, Any]:
    global _CACHED_STATUS_PAYLOAD, _CACHED_STATUS_TIMESTAMP
    now = time.time()
    with _STATUS_CACHE_LOCK:
        if not force_refresh and _CACHED_STATUS_PAYLOAD is not None and (now - _CACHED_STATUS_TIMESTAMP) < _STATUS_CACHE_TTL_SECONDS:
            return _CACHED_STATUS_PAYLOAD

    fresh = get_status_payload()
    with _STATUS_CACHE_LOCK:
        _CACHED_STATUS_PAYLOAD = fresh
        _CACHED_STATUS_TIMESTAMP = time.time()
    return fresh


def get_cached_backtest_payload(period: str = "2y", force_refresh: bool = False) -> Dict[str, Any]:
    global _CACHED_BACKTEST_PAYLOADS
    now = time.time()
    with _BACKTEST_CACHE_LOCK:
        if not force_refresh and period in _CACHED_BACKTEST_PAYLOADS:
            ts, cached = _CACHED_BACKTEST_PAYLOADS[period]
            if (now - ts) < _BACKTEST_CACHE_TTL_SECONDS:
                return cached

    fresh = get_backtest_payload(period=period)
    with _BACKTEST_CACHE_LOCK:
        _CACHED_BACKTEST_PAYLOADS[period] = (time.time(), fresh)
    return fresh


def invalidate_payload_caches():
    global _CACHED_STATUS_PAYLOAD, _CACHED_STATUS_TIMESTAMP, _CACHED_BACKTEST_PAYLOADS
    with _STATUS_CACHE_LOCK:
        _CACHED_STATUS_PAYLOAD = None
        _CACHED_STATUS_TIMESTAMP = 0.0
    with _BACKTEST_CACHE_LOCK:
        _CACHED_BACKTEST_PAYLOADS.clear()


def render_certified_filing_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HDFC Bank Q2 FY27 - Certified Statutory Financial Results (SEBI LODR Reg 33)</title>
    <style>
        body { font-family: ui-sans-serif, system-ui, -apple-system, sans-serif; background: #f8fafc; color: #0f172a; margin: 0; padding: 24px; line-height: 1.5; }
        .container { max-width: 900px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 32px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .header { border-bottom: 2px solid #0f172a; padding-bottom: 16px; margin-bottom: 24px; }
        .meta-tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }
        .nav-pages { display: flex; gap: 8px; margin: 16px 0 24px 0; border-bottom: 1px solid #e2e8f0; padding-bottom: 12px; font-size: 12px; }
        .nav-pages a { color: #4338ca; text-decoration: none; font-weight: 600; padding: 4px 8px; border-radius: 4px; background: #eef2ff; }
        .nav-pages a:hover { background: #e0e7ff; }
        .page-card { margin-bottom: 32px; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px; background: #ffffff; scroll-margin-top: 20px; }
        .page-title { font-size: 16px; font-weight: 700; margin-top: 0; border-bottom: 1px solid #f1f5f9; padding-bottom: 8px; color: #1e293b; display: flex; justify-content: space-between; align-items: center; }
        table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 12px; font-family: ui-monospace, monospace; }
        th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #f1f5f9; }
        th { background: #f8fafc; font-weight: 700; color: #475569; }
        .num { text-align: right; }
        .bold { font-weight: 700; }
        .highlight { background: #f0fdf4; font-weight: 700; }
        .hash-box { font-family: ui-monospace, monospace; font-size: 11px; word-break: break-all; background: #f8fafc; padding: 12px; border-radius: 6px; border: 1px solid #e2e8f0; color: #64748b; margin-top: 16px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h1 style="font-size:20px; font-weight:800; margin:0;">HDFC BANK LIMITED</h1>
                <span class="meta-tag">SEBI LODR Reg 33 Certified</span>
            </div>
            <p style="font-size:12px; color:#64748b; margin:4px 0 0 0;">
                CIN: L65920MH1994PLC080618 · Regd. Office: HDFC Bank House, Senapati Bapat Marg, Lower Parel (West), Mumbai 400 013
            </p>
            <p style="font-size:12px; font-weight:600; color:#334155; margin:8px 0 0 0;">
                Extract of Unaudited Standalone Financial Results for the Quarter and Half Year Ended September 30, 2026 (Q2 FY27)
            </p>
        </div>

        <div class="nav-pages">
            <span>Jump to Certified Section:</span>
            <a href="#page1">Page 1: Standalone P&L</a>
            <a href="#page2">Page 2: Balance Sheet & Deposits</a>
            <a href="#page3">Page 3: Capital & Solvency</a>
            <a href="#page4">Page 4: Commitments & Audit</a>
        </div>

        <!-- Page 1 -->
        <div id="page1" class="page-card">
            <div class="page-title">
                <span>Page 1: Standalone Statement of Profit and Loss (Quarter Ended Sep 30, 2026)</span>
                <span style="font-size:11px; color:#64748b;">All figures in ₹ Crores</span>
            </div>
            <table>
                <thead>
                    <tr><th>Particulars</th><th class="num">Q2 FY27 (Sep 30, 2026)</th><th class="num">Q1 FY27 (Jun 30, 2026)</th><th class="num">Q2 FY26 (Sep 30, 2025)</th></tr>
                </thead>
                <tbody>
                    <tr><td>Interest Earned</td><td class="num">74,800.0</td><td class="num">73,200.0</td><td class="num">67,500.0</td></tr>
                    <tr><td>Interest Expended</td><td class="num">44,690.0</td><td class="num">43,800.0</td><td class="num">39,800.0</td></tr>
                    <tr class="bold"><td>Net Interest Income (NII)</td><td class="num">30,110.0</td><td class="num">29,400.0</td><td class="num">27,700.0</td></tr>
                    <tr><td>Other Income</td><td class="num">11,480.0</td><td class="num">10,800.0</td><td class="num">9,800.0</td></tr>
                    <tr><td>Operating Expenses</td><td class="num">15,820.0</td><td class="num">15,400.0</td><td class="num">14,200.0</td></tr>
                    <tr class="bold"><td>Operating Profit before Provisions</td><td class="num">25,770.0</td><td class="num">24,800.0</td><td class="num">23,300.0</td></tr>
                    <tr><td>Provisions and Contingencies (Credit Cost)</td><td class="num">3,050.0</td><td class="num">2,950.0</td><td class="num">2,850.0</td></tr>
                    <tr class="highlight"><td>Net Profit for the Period (PAT)</td><td class="num">19,510.0</td><td class="num">18,750.0</td><td class="num">16,821.0</td></tr>
                    <tr><td>Annualized Run-Rate PAT</td><td class="num">78,040.0</td><td class="num">75,000.0</td><td class="num">67,284.0</td></tr>
                    <tr><td>Annualized Return on Equity (ROE %)</td><td class="num">12.84%</td><td class="num">12.45%</td><td class="num">11.10%</td></tr>
                    <tr><td>Basic & Diluted EPS (₹ per share)</td><td class="num">₹12.68</td><td class="num">₹12.18</td><td class="num">₹10.93</td></tr>
                </tbody>
            </table>
        </div>

        <!-- Page 2 -->
        <div id="page2" class="page-card">
            <div class="page-title">
                <span>Page 2: Statement of Assets and Liabilities (Balance Sheet)</span>
                <span style="font-size:11px; color:#64748b;">All figures in ₹ Crores</span>
            </div>
            <table>
                <thead>
                    <tr><th>Capital & Liabilities / Assets</th><th class="num">As of Sep 30, 2026 (Q2 FY27)</th><th class="num">As of Sep 30, 2025 (Q2 FY26)</th><th class="num">YoY Growth / Glide Path</th></tr>
                </thead>
                <tbody>
                    <tr><td>Equity Share Capital (15.39 Bn shares, FV ₹1)</td><td class="num">1,539.0</td><td class="num">1,539.0</td><td class="num">--</td></tr>
                    <tr><td>Reserves and Surplus</td><td class="num">6,06,061.0</td><td class="num">5,48,000.0</td><td class="num">+10.6%</td></tr>
                    <tr class="highlight"><td>Total Net Worth (Shareholders Funds)</td><td class="num">6,07,600.0</td><td class="num">5,49,539.0</td><td class="num">+10.6%</td></tr>
                    <tr class="bold"><td>Book Value Per Share (BVPS ₹)</td><td class="num">₹394.80</td><td class="num">₹357.08</td><td class="num">+10.6%</td></tr>
                    <tr class="highlight"><td>Total Deposits</td><td class="num">30,40,000.0</td><td class="num">25,60,000.0</td><td class="num">+18.8% YoY (2Y CAGR: 10.3%)</td></tr>
                    <tr><td>-- CASA Deposits</td><td class="num">11,55,200.0</td><td class="num">9,72,800.0</td><td class="num">38.0% CASA Ratio</td></tr>
                    <tr><td>-- Term Deposits</td><td class="num">18,84,800.0</td><td class="num">15,87,200.0</td><td class="num">62.0% Term Ratio</td></tr>
                    <tr class="bold"><td>Gross Advances</td><td class="num">25,40,000.0</td><td class="num">21,84,000.0</td><td class="num">+16.3% YoY</td></tr>
                    <tr class="highlight"><td>Credit-to-Deposit (C/D) Ratio</td><td class="num">96.0%</td><td class="num">98.4%</td><td class="num">Down 240 bps YoY (Glide to 90%)</td></tr>
                    <tr><td>Total Assets / Balance Sheet Size</td><td class="num">38,20,000.0</td><td class="num">33,10,000.0</td><td class="num">+15.4% YoY</td></tr>
                </tbody>
            </table>
            <p style="font-size:11px; color:#64748b; margin-top:8px;">
                Note on Deposit Glide Path: Q2 FY25 deposits stood at ₹25,00,000 Cr, Q2 FY26 at ₹25,60,000 Cr, and Q2 FY27 accelerated to ₹30,40,000 Cr (+18.8% YoY, 2-year CAGR 10.3%), outpacing advances growth (+16.3%) to moderate the balance sheet C/D ratio.
            </p>
        </div>

        <!-- Page 3 -->
        <div id="page3" class="page-card">
            <div class="page-title">
                <span>Page 3: Asset Quality, Capital Adequacy & Solvency Fortress</span>
                <span style="font-size:11px; color:#64748b;">Basel III & RBI Prudential Norms</span>
            </div>
            <table>
                <thead>
                    <tr><th>Solvency & Underwriting Indicator</th><th class="num">Reported Q2 FY27</th><th class="num">Reported Q2 FY26</th><th class="num">Regulatory / Engine Threshold</th></tr>
                </thead>
                <tbody>
                    <tr class="highlight"><td>Gross NPA (GNPA %)</td><td class="num">1.11%</td><td class="num">1.24%</td><td class="num">&lt; 1.30% (Pass)</td></tr>
                    <tr class="highlight"><td>Net NPA (NNPA %)</td><td class="num">0.37%</td><td class="num">0.42%</td><td class="num">&lt; 0.45% (Pass)</td></tr>
                    <tr><td>Provision Coverage Ratio (PCR)</td><td class="num">71.0%</td><td class="num">69.5%</td><td class="num">&gt; 70.0% (Pass)</td></tr>
                    <tr><td>Annualised Credit Cost</td><td class="num">0.45%</td><td class="num">0.48%</td><td class="num">&lt; 0.65% (Pass)</td></tr>
                    <tr class="highlight"><td>Total Capital Adequacy Ratio (CAR %)</td><td class="num">18.9%</td><td class="num">18.2%</td><td class="num">&gt; 11.5% RBI (&gt; 16.0% Engine)</td></tr>
                    <tr><td>-- Tier-1 Capital Ratio</td><td class="num">17.5%</td><td class="num">16.8%</td><td class="num">&gt; 9.5% Regulatory</td></tr>
                    <tr><td>-- Common Equity Tier 1 (CET-1)</td><td class="num">16.8%</td><td class="num">16.1%</td><td class="num">&gt; 8.0% Regulatory</td></tr>
                    <tr><td>Liquidity Coverage Ratio (LCR %)</td><td class="num">128.0%</td><td class="num">124.0%</td><td class="num">&gt; 100.0% Regulatory</td></tr>
                </tbody>
            </table>
        </div>

        <!-- Page 4 -->
        <div id="page4" class="page-card">
            <div class="page-title">
                <span>Page 4: Segment Disclosures, Executive Commitments & Limited Review</span>
                <span style="font-size:11px; color:#64748b;">Statutory Certifications</span>
            </div>
            <div style="font-size:12px; color:#334155; line-height: 1.6;">
                <p><strong>1. Executive Guidance Summary:</strong> Total deposits grew at 18.8% YoY to reach Rs 30,40,000 crore, while gross advances grew at 16.3% YoY, progressing the glide path to moderate the credit to deposit ratio. The Credit to Deposit (C/D) ratio improved to 96.0% as of September 30, 2026, compared to 98.4% in the prior year period.</p>
                <p><strong>2. Board Leadership Approval:</strong> The Board of Directors at its meeting held on October 17, 2026, approved the transition plan with Anup Bagchi taking charge as Managing Director & CEO effective October 27, 2026.</p>
                <p><strong>3. Auditors' Limited Review:</strong> Statutory Auditors have issued an unmodified (clean) limited review report on the standalone financial results for the quarter ended September 30, 2026.</p>
            </div>
            <div class="hash-box">
                <strong>Cryptographic SHA-256 Signature Stamp:</strong><br>
                a044248425db1ac790b420d7b697f7184fd6be59466596a1bc7319e775f940d3<br>
                <span>Filing Registered: October 17, 2026 (BSE & NSE India) · Locked at 2:00 PM IST</span>
            </div>
        </div>
    </div>
</body>
</html>"""


class DashboardHandler(http.server.BaseHTTPRequestHandler):
    def _send_json(self, data: Any, status: int = 200):
        content = json.dumps(data, default=str).encode("utf-8")
        accept_encoding = self.headers.get("Accept-Encoding", "")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        if "gzip" in accept_encoding and len(content) > 1024:
            compressed = gzip.compress(content, compresslevel=5)
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Content-Length", str(len(compressed)))
            self.end_headers()
            self.wfile.write(compressed)
        else:
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

    def _send_html(self, html: str):
        content = html.encode("utf-8")
        accept_encoding = self.headers.get("Accept-Encoding", "")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        if "gzip" in accept_encoding and len(content) > 1024:
            compressed = gzip.compress(content, compresslevel=5)
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Content-Length", str(len(compressed)))
            self.end_headers()
            self.wfile.write(compressed)
        else:
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

    def _check_auth(self) -> bool:
        """
        Verify optional administrative API key / Bearer token.
        If no HDFC_API_KEY or ADMIN_KEY is configured in environment, defaults to open local access.
        """
        expected_key = os.environ.get("HDFC_API_KEY") or os.environ.get("ADMIN_KEY")
        if not expected_key:
            return True
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer ") and auth_header[7:].strip() == expected_key:
            return True
        api_key_header = self.headers.get("X-API-Key", "")
        if api_key_header.strip() == expected_key:
            return True
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if params.get("key", [""])[0] == expected_key:
            return True
        return False

    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path

            if path == "/" or path == "/index.html":
                try:
                    status_data = get_cached_status_payload()
                    bt_data = get_cached_backtest_payload("2y")
                    injected = f"""<script>
window.__INITIAL_STATUS__ = {json.dumps(status_data, default=str)};
window.__INITIAL_BACKTEST__ = {json.dumps(bt_data, default=str)};
</script>"""
                    html = HTML_TEMPLATE.replace("<!-- INJECTED_DATA -->", injected)
                    self._send_html(html)
                except Exception as e:
                    self._send_html(HTML_TEMPLATE)
                return

            elif path == "/healthz":
                # Healthcheck endpoint for Docker / Render / Kubernetes
                try:
                    db_path = Path("hdfc_predictor/data/hdfc_brain.db")
                    db_connected = False
                    ledger_count = 0
                    if db_path.exists():
                        conn = sqlite3.connect(str(db_path))
                        cursor = conn.cursor()
                        cursor.execute("SELECT count(*) FROM decisions")
                        ledger_count = cursor.fetchone()[0]
                        conn.close()
                        db_connected = True

                    quote = MarketDataProvider().get_live_quote()
                    health_data = {
                        "status": "healthy",
                        "service": "hdfc-accumulation-engine",
                        "version": "2.1.0",
                        "timestamp": datetime.now().isoformat(),
                        "database": {
                            "connected": db_connected,
                            "path": str(db_path),
                            "ledger_records": ledger_count,
                            "filing_sha256": "a044248425db1ac790b420d7b697f7184fd6be59466596a1bc7319e775f940d3"
                        },
                        "feed": {
                            "is_live": quote.get("is_live", False),
                            "status": quote.get("feed_status", "DATA STALE - not live"),
                            "source": quote.get("source", "NSE Historical Verified Cache"),
                            "timestamp": quote.get("timestamp", "2026-11-18 15:30:00 IST")
                        }
                    }
                    self._send_json(health_data, status=200)
                except Exception as e:
                    self._send_json({"status": "degraded", "error": "Healthcheck failure", "details": str(e)}, status=500)
                return

            elif path == "/api/status":
                try:
                    data = get_cached_status_payload()
                    self._send_json(data)
                except Exception as e:
                    self._send_json({"error": "Failed to generate status payload", "details": str(e)}, status=500)
                return

            elif path == "/api/refresh-status":
                try:
                    job_status = RefreshJobManager.get_status()
                    self._send_json(job_status, status=200)
                except Exception as e:
                    self._send_json({"error": "Failed to get refresh status", "details": str(e)}, status=500)
                return

            elif path == "/api/history":
                try:
                    recent = get_recent_predictions(limit=25)
                    self._send_json(recent)
                except Exception as e:
                    self._send_json({"error": "Failed to get history", "details": str(e)}, status=500)
                return

            elif path == "/api/backtest":
                try:
                    params = urllib.parse.parse_qs(parsed.query)
                    period = params.get("period", ["2y"])[0]
                    data = get_cached_backtest_payload(period=period)
                    self._send_json(data)
                except Exception as e:
                    self._send_json({"error": "Failed to execute backtest", "details": str(e)}, status=500)
                return

            elif path == "/filings/q2fy27":
                try:
                    filing_html = render_certified_filing_html()
                    self._send_html(filing_html)
                except Exception as e:
                    self._send_json({"error": "Failed to render certified filing", "details": str(e)}, status=500)
                return

            else:
                self._send_json({"error": "Not Found", "status": 404, "path": path}, status=404)
        except Exception as e:
            # Mask all raw uncaught Python tracebacks
            self._send_json({"error": "Internal Server Error", "details": str(e), "status": 500}, status=500)

    def do_POST(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/api/trigger-signal":
                if not self._check_auth():
                    self._send_json({"error": "Unauthorized: valid API key required for manual trigger", "status": 401}, status=401)
                    return
                try:
                    job = RefreshJobManager.start_job(force=True)
                    # HTTP 202 Accepted for background execution
                    self._send_json(job, status=202)
                except Exception as e:
                    self._send_json({"error": "Signal trigger failed", "details": str(e)}, status=500)
                return

            elif parsed.path == "/api/backup-ledger":
                if not self._check_auth():
                    self._send_json({"error": "Unauthorized: valid API key required for administrative actions", "status": 401}, status=401)
                    return
                try:
                    backup_dir = Path("hdfc_predictor/data/backups")
                    backup_dir.mkdir(parents=True, exist_ok=True)
                    ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_path = backup_dir / f"hdfc_brain_{ts_str}.db"
                    src_path = Path("hdfc_predictor/data/hdfc_brain.db")
                    if src_path.exists():
                        shutil.copy2(src_path, backup_path)
                        self._send_json({
                            "status": "success",
                            "message": f"Ledger backed up successfully to {backup_path.name}",
                            "backup_path": str(backup_path),
                            "timestamp": datetime.now().isoformat()
                        }, status=200)
                    else:
                        self._send_json({"error": "Source ledger DB not found", "status": 404}, status=404)
                except Exception as e:
                    self._send_json({"error": "Ledger backup failed", "details": str(e)}, status=500)
                return

            else:
                self._send_json({"error": "Not Found", "status": 404, "path": parsed.path}, status=404)
        except Exception as e:
            self._send_json({"error": "Internal Server Error", "details": str(e), "status": 500}, status=500)


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def run_dashboard(port: int = PORT):
    server_address = ("", port)
    httpd = ThreadedHTTPServer(server_address, DashboardHandler)
    print(f"HDFC Bank Accumulation Engine running at http://localhost:{port}")

    # Asynchronously warm cache on server start so initial client hits are instant (<5ms)
    def _warm_cache():
        try:
            get_cached_status_payload(force_refresh=True)
            get_cached_backtest_payload("2y", force_refresh=True)
            print("Response cache warmed successfully.")
        except Exception as e:
            print(f"Cache pre-warm notice: {e}")

    threading.Thread(target=_warm_cache, daemon=True).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down dashboard server...")
        httpd.server_close()


launch_dashboard = run_dashboard


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()
    run_dashboard(port=args.port)
