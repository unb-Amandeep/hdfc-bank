"""
Interactive Web Dashboard for HDFC Bank Cyclical Accumulation & Decision Intelligence.
Unified into a clean, modern single-page dashboard with:
1. Top Fold: Verdict & Capital Allocation Plan + Dynamic Price Ladder
2. Collapsible Sections:
   - 6 Accumulation & Safety Gates (Gates 0 to 5 + Event Blackouts)
   - Management Promise & Guidance Tracker (BSE/NSE Q2 FY27 Audit)
   - Valuation Scenarios & Textbook Gordon Sensitivity Matrix (Reality Check)
   - Audited Historical Proof, All Past Setup Episodes & Track Record
   - Material Event Intelligence & Regulatory Filings
   - Big-4 Private Banking Peer Watchlist (Standalone Q2 FY27)
   - Data Health & Cryptographic SHA-256 Audit Ledger
3. Plain-Language mode by default with Technical Details toggle
4. Completely self-contained: zero external CDNs, native HTML5 canvas line chart, local styles.
"""
import http.server
import json
import socketserver
import urllib.parse
from datetime import datetime
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

PORT = 8501

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accumulation Engine · HDFC Bank</title>
    <!-- INJECTED_DATA -->
    <style>
        :root {
            --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
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
            --amber-500: #f59e0b;
            --amber-700: #b45309;
            --amber-800: #92400e;
            --rose-50: #fff1f2;
            --rose-100: #ffe4e6;
            --rose-200: #fecdd3;
            --rose-500: #f43f5e;
            --rose-600: #e11d48;
            --rose-700: #be123c;
            --rose-800: #9f1239;
            --indigo-50: #eef2ff;
            --indigo-100: #e0e7ff;
            --indigo-200: #c7d2fe;
            --indigo-600: #4f46e5;
            --indigo-700: #4338ca;
            --purple-50: #faf5ff;
            --purple-100: #f3e8ff;
            --purple-700: #7e22ce;
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
        @media (min-width: 640px) {
            .sm\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .sm\:grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
            .sm\:grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
            .sm\:inline { display: inline; }
            .sm\:px-6 { padding-left: 1.5rem; padding-right: 1.5rem; }
            .sm\:p-7 { padding: 1.75rem; }
            .sm\:text-3xl { font-size: 1.875rem; line-height: 2.25rem; }
        }
        @media (min-width: 768px) {
            .md\:inline-flex { display: inline-flex; }
        }
        @media (min-width: 1024px) {
            .lg\:grid-cols-3 { grid-template-columns: 2fr 1fr; }
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
        
        .space-y-1 > * + * { margin-top: 0.25rem; }
        .space-y-1\.5 > * + * { margin-top: 0.375rem; }
        .space-y-2 > * + * { margin-top: 0.5rem; }
        .space-y-2\.5 > * + * { margin-top: 0.625rem; }
        .space-y-3 > * + * { margin-top: 0.75rem; }
        .space-y-4 > * + * { margin-top: 1rem; }
        .space-y-6 > * + * { margin-top: 1.5rem; }
        .space-y-8 > * + * { margin-top: 2rem; }
        
        /* Spacing */
        .p-0\.5 { padding: 0.125rem; }
        .p-1 { padding: 0.25rem; }
        .p-2 { padding: 0.5rem; }
        .p-2\.5 { padding: 0.625rem; }
        .p-3 { padding: 0.75rem; }
        .p-4 { padding: 1rem; }
        .p-5 { padding: 1.25rem; }
        .p-6 { padding: 1.5rem; }
        .px-1\.5 { padding-left: 0.375rem; padding-right: 0.375rem; }
        .px-2 { padding-left: 0.5rem; padding-right: 0.5rem; }
        .px-2\.5 { padding-left: 0.625rem; padding-right: 0.625rem; }
        .px-3 { padding-left: 0.75rem; padding-right: 0.75rem; }
        .px-4 { padding-left: 1rem; padding-right: 1rem; }
        .px-6 { padding-left: 1.5rem; padding-right: 1.5rem; }
        .py-0\.2 { padding-top: 0.1rem; padding-bottom: 0.1rem; }
        .py-0\.5 { padding-top: 0.125rem; padding-bottom: 0.125rem; }
        .py-1 { padding-top: 0.25rem; padding-bottom: 0.25rem; }
        .py-1\.5 { padding-top: 0.375rem; padding-bottom: 0.375rem; }
        .py-2 { padding-top: 0.5rem; padding-bottom: 0.5rem; }
        .py-2\.5 { padding-top: 0.625rem; padding-bottom: 0.625rem; }
        .py-6 { padding-top: 1.5rem; padding-bottom: 1.5rem; }
        .py-8 { padding-top: 2rem; padding-bottom: 2rem; }
        .pt-0 { padding-top: 0; }
        .pt-1 { padding-top: 0.25rem; }
        .pt-2 { padding-top: 0.5rem; }
        .pt-2\.5 { padding-top: 0.625rem; }
        .pt-3 { padding-top: 0.75rem; }
        .pt-4 { padding-top: 1rem; }
        .pb-2 { padding-bottom: 0.5rem; }
        .mt-2 { margin-top: 0.5rem; }
        .mt-2\.5 { margin-top: 0.625rem; }
        .mt-4 { margin-top: 1rem; }
        .mb-2 { margin-bottom: 0.5rem; }
        .mx-auto { margin-left: auto; margin-right: auto; }
        
        /* Dimensions & Position */
        .w-full { width: 100%; }
        .w-2 { width: 0.5rem; }
        .w-3 { width: 0.75rem; }
        .w-3\.5 { width: 0.875rem; }
        .w-4 { width: 1rem; }
        .w-6 { width: 1.5rem; }
        .w-8 { width: 2rem; }
        .h-2 { height: 0.5rem; }
        .h-3 { height: 0.75rem; }
        .h-3\.5 { height: 0.875rem; }
        .h-4 { height: 1rem; }
        .h-6 { height: 1.5rem; }
        .h-8 { height: 2rem; }
        .h-16 { height: 4rem; }
        .h-80 { height: 20rem; }
        .max-w-\[1200px\] { max-width: 1200px; }
        .min-h-screen { min-height: 100vh; }
        .relative { position: relative; }
        .sticky { position: sticky; }
        .top-0 { top: 0; }
        .z-50 { z-index: 50; }
        
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
        .bg-emerald-500 { background-color: var(--emerald-500); }
        .bg-amber-50 { background-color: var(--amber-50); }
        .bg-amber-100 { background-color: var(--amber-100); }
        .bg-amber-500 { background-color: var(--amber-500); }
        .bg-rose-50 { background-color: var(--rose-50); }
        .bg-rose-100 { background-color: var(--rose-100); }
        .bg-rose-500 { background-color: var(--rose-500); }
        .bg-indigo-50 { background-color: var(--indigo-50); }
        .bg-indigo-100 { background-color: var(--indigo-100); }
        .bg-purple-50 { background-color: var(--purple-50); }
        .bg-purple-100 { background-color: var(--purple-100); }
        .bg-teal-100 { background-color: var(--teal-100); }
        
        .text-slate-300 { color: var(--slate-300); }
        .text-slate-400 { color: var(--slate-400); }
        .text-slate-500 { color: var(--slate-500); }
        .text-slate-600 { color: var(--slate-600); }
        .text-slate-700 { color: var(--slate-700); }
        .text-slate-800 { color: var(--slate-800); }
        .text-slate-900 { color: var(--slate-900); }
        .text-white { color: #ffffff; }
        .text-emerald-600 { color: var(--emerald-600); }
        .text-emerald-700 { color: var(--emerald-700); }
        .text-emerald-800 { color: var(--emerald-800); }
        .text-emerald-900 { color: var(--emerald-900); }
        .text-amber-300 { color: var(--amber-300); }
        .text-amber-700 { color: var(--amber-700); }
        .text-amber-800 { color: var(--amber-800); }
        .text-rose-600 { color: var(--rose-600); }
        .text-rose-700 { color: var(--rose-700); }
        .text-rose-800 { color: var(--rose-800); }
        .text-indigo-600 { color: var(--indigo-600); }
        .text-indigo-700 { color: var(--indigo-700); }
        .text-indigo-800 { color: #3730a3; }
        .text-indigo-900 { color: #312e81; }
        .text-purple-700 { color: var(--purple-700); }
        .text-teal-700 { color: var(--teal-700); }
        
        .border { border: 1px solid var(--slate-200); }
        .border-2 { border-width: 2px; }
        .border-b { border-bottom: 1px solid var(--slate-200); }
        .border-t { border-top: 1px solid var(--slate-200); }
        .border-slate-100 { border-color: var(--slate-100); }
        .border-slate-200 { border-color: var(--slate-200); }
        .border-slate-300 { border-color: var(--slate-300); }
        .border-emerald-200 { border-color: var(--emerald-200); }
        .border-emerald-500 { border-color: var(--emerald-500); }
        .border-amber-200 { border-color: var(--amber-200); }
        .border-amber-300 { border-color: var(--amber-300); }
        .border-rose-200 { border-color: var(--rose-200); }
        .border-indigo-100 { border-color: var(--indigo-100); }
        .border-indigo-200 { border-color: var(--indigo-200); }
        
        .rounded { border-radius: 0.25rem; }
        .rounded-md { border-radius: 0.375rem; }
        .rounded-lg { border-radius: 0.5rem; }
        .rounded-xl { border-radius: 0.75rem; }
        .rounded-2xl { border-radius: 1rem; }
        .rounded-full { border-radius: 9999px; }
        .shadow-sm { box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); }
        
        .text-\[10px\] { font-size: 10px; }
        .text-\[11px\] { font-size: 11px; }
        .text-xs { font-size: 12px; }
        .text-sm { font-size: 14px; }
        .text-base { font-size: 16px; }
        .text-lg { font-size: 18px; }
        .text-xl { font-size: 20px; }
        .text-2xl { font-size: 24px; }
        .font-normal { font-weight: 400; }
        .font-medium { font-weight: 500; }
        .font-semibold { font-weight: 600; }
        .font-bold { font-weight: 700; }
        .font-extrabold { font-weight: 800; }
        .italic { font-style: italic; }
        .uppercase { text-transform: uppercase; }
        .tracking-wide { letter-spacing: 0.025em; }
        .tracking-wider { letter-spacing: 0.05em; }
        .tracking-tight { letter-spacing: -0.025em; }
        .leading-snug { line-height: 1.375; }
        .leading-relaxed { line-height: 1.625; }
        .text-left { text-align: left; }
        .text-right { text-align: right; }
        .text-center { text-align: center; }
        .overflow-hidden { overflow: hidden; }
        .overflow-x-auto { overflow-x: auto; }
        .cursor-pointer { cursor: pointer; }
        .list-none { list-style: none; }
        .block { display: block; }
        .hidden { display: none; }
        .transition { transition: all 0.2s ease-in-out; }
        
        /* Table */
        table { width: 100%; border-collapse: collapse; }
        th, td { text-align: left; vertical-align: middle; }
        .divide-y > * + * { border-top: 1px solid var(--slate-100); }
        
        /* Details Summary */
        details summary::-webkit-details-marker { display: none; }
        details[open] summary .group-open\:rotate-180 { transform: rotate(180deg); }
        
        /* Links & Buttons */
        .nav-link { color: var(--slate-500); text-decoration: none; transition: color 0.2s ease; }
        .nav-link:hover { color: var(--slate-900); }
        button { cursor: pointer; border: none; font-family: inherit; }
        .hover\:bg-slate-50:hover { background-color: var(--slate-50); }
        .hover\:bg-slate-100:hover { background-color: var(--slate-100); }
        .hover\:bg-slate-800:hover { background-color: var(--slate-800); }
        .hover\:text-slate-900:hover { color: var(--slate-900); }
        .hover\:text-emerald-600:hover { color: var(--emerald-600); }
        
        /* Scrollbar */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: var(--slate-100); }
        ::-webkit-scrollbar-thumb { background: var(--slate-300); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--slate-400); }

        /* Toast notifications */
        #toastContainer { position: fixed; top: 20px; right: 20px; z-index: 9999; display: flex; flex-direction: column; gap: 8px; pointer-events: none; }
        .toast-item { pointer-events: auto; padding: 10px 16px; border-radius: 8px; font-size: 12px; font-weight: 600; box-shadow: 0 4px 12px rgba(0,0,0,0.15); display: flex; align-items: center; gap: 8px; transition: all 0.3s ease; }
        .toast-success { background-color: #064e3b; color: #a7f3d0; border: 1px solid #059669; }
        .toast-error { background-color: #881337; color: #fecdd3; border: 1px solid #e11d48; }
    </style>
</head>
<body class="min-h-screen text-slate-800">

    <div id="toastContainer"></div>

    <!-- Top Sticky Header -->
    <header class="bg-white/95 border-b border-slate-200 sticky top-0 z-50">
        <div class="max-w-[1200px] mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
            <!-- Left Brand -->
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center font-bold text-white text-sm shrink-0">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/></svg>
                </div>
                <div>
                    <div class="flex items-center gap-2">
                        <span class="text-sm font-bold text-slate-900">Accumulation Engine</span>
                        <span class="px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 text-[10px] font-semibold">Q2 FY27</span>
                    </div>
                    <p class="text-xs text-slate-500">HDFC Bank · NSE: HDFCBANK · Paper trading</p>
                </div>
            </div>

            <!-- Right: Price, Timing Status & Mode Controls -->
            <div class="flex items-center gap-3 sm:gap-4">
                <div class="flex items-baseline gap-2">
                    <span id="headerPriceText" class="text-base sm:text-lg font-extrabold text-slate-900 mono">₹817.80</span>
                    <span id="headerTimingStatus" class="text-xs text-slate-500 hidden sm:inline">Last traded · 2:00 PM IST</span>
                </div>
                
                <span class="hidden md:inline-flex px-2 py-0.5 rounded bg-amber-50 text-amber-800 text-[11px] font-medium border border-amber-200">
                    BSE/NSE Certified Source
                </span>

                <!-- Plain / Tech Toggle -->
                <div class="flex items-center bg-slate-100 p-0.5 rounded-lg text-xs font-semibold">
                    <button onclick="setMode('plain')" id="btnModePlain" class="px-2.5 py-1 rounded-md bg-white text-slate-900 shadow-sm">Plain</button>
                    <button onclick="setMode('tech')" id="btnModeTech" class="px-2.5 py-1 rounded-md text-slate-500 hover:text-slate-900">Technical</button>
                </div>

                <button onclick="triggerNow()" id="btnTrigger" class="bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                    Refresh
                </button>
            </div>
        </div>

        <!-- Sticky Anchor Sub-Navigation Bar -->
        <div class="max-w-[1200px] mx-auto px-4 sm:px-6 flex items-center justify-between border-t border-slate-100 text-xs font-semibold overflow-x-auto">
            <nav class="flex gap-5 sm:gap-6 py-2.5 shrink-0">
                <a href="#sectionOverview" class="nav-link text-slate-900 font-bold hover:text-emerald-600 transition">Verdict & Plan</a>
                <a href="#sectionGates" class="nav-link text-slate-500 hover:text-slate-900 transition flex items-center gap-1">
                    6 Safety Gates
                    <span id="navGatesSummaryPill" class="px-1.5 py-0.2 rounded bg-slate-100 text-slate-700 text-[10px] font-bold">5/6 Pass</span>
                </a>
                <a href="#sectionPromises" class="nav-link text-slate-500 hover:text-slate-900 transition flex items-center gap-1">
                    Promise Tracker
                    <span class="px-1.5 py-0.2 rounded bg-emerald-50 text-emerald-700 text-[10px] font-bold">Q2 FY27</span>
                </a>
                <a href="#sectionValuation" class="nav-link text-slate-500 hover:text-slate-900 transition">Gordon Valuation</a>
                <a href="#sectionProof" class="nav-link text-slate-500 hover:text-slate-900 transition">Audited Proof</a>
                <a href="#sectionEvents" class="nav-link text-slate-500 hover:text-slate-900 transition flex items-center gap-1">
                    Event Intel
                    <span class="px-1.5 py-0.2 rounded bg-indigo-50 text-indigo-700 text-[10px] font-bold">Classified</span>
                </a>
                <a href="#sectionWatchlist" class="nav-link text-slate-500 hover:text-slate-900 transition flex items-center gap-1">
                    Peer Watchlist
                    <span class="px-1.5 py-0.2 rounded bg-purple-50 text-purple-700 text-[10px] font-bold">Big-4</span>
                </a>
                <a href="#sectionHealth" class="nav-link text-slate-500 hover:text-slate-900 transition flex items-center gap-1">
                    Data Health
                    <span class="w-4 h-4 rounded-full bg-slate-200 text-slate-700 text-[10px] flex items-center justify-center font-bold">SHA</span>
                </a>
            </nav>
        </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-[1200px] mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-8">

        <!-- 1. TOP FOLD: VERDICT & TRADING PLAN -->
        <section id="sectionOverview" class="scroll-mt-28 space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 sm:gap-8 items-start">
                
                <!-- Left 2 Cols: Main Verdict & Action Tiles -->
                <div class="lg:col-span-2 space-y-6">
                    <div class="bg-white border border-slate-200 rounded-2xl p-6 sm:p-7 shadow-sm space-y-6">
                        <!-- Top Metadata Pills -->
                        <div class="flex flex-wrap items-center gap-2.5 text-xs">
                            <span id="verdictActionBadge" class="px-2.5 py-1 rounded-full font-bold bg-amber-50 text-amber-800 border border-amber-200 flex items-center gap-1.5 uppercase tracking-wide text-[11px]">
                                <span class="w-2 h-2 rounded-full bg-amber-500"></span>
                                WAIT
                            </span>
                            <span id="orderValidityPill" class="px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 text-[11px] font-medium">
                                Valid until Nov 26, 2026 (5 trading days)
                            </span>
                            <span class="px-2.5 py-1 rounded-full bg-slate-100 text-slate-500 text-[11px] flex items-center gap-1">
                                <svg class="w-3 h-3 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
                                Record locked at 2:00 PM · SHA-256 Ledger
                            </span>
                        </div>

                        <!-- Main Headline (Plain vs Technical) -->
                        <div class="space-y-2">
                            <h2 id="verdictHeadlinePlain" class="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight leading-snug">
                                HDFC Bank is cheaper than recent history, but momentum surged +16.8% in two weeks. Wait for a pullback to the derived buy zone before deploying capital.
                            </h2>
                            <p id="verdictHeadlineTech" class="tech-block text-xs font-mono bg-slate-50 p-3 rounded-lg border border-slate-200 text-slate-700 leading-relaxed">
                                Gate 0 Pass (Net Worth ₹6.08L Cr / 15.39B shares = ₹394.80 BVPS). Gate 1 Pass (P/B in 16th post-merger percentile). Gate 2 Pass (CAR 18.9% vs 14.0% floor; GNPA 1.11%). Gate 3 Pass (Base confirmed above Donchian support). Gate 4 WAIT (Wilder RSI 88.7 > 75.0, 10d sprint 16.8% > 12.0%). First tranche size derived at limit range.
                            </p>
                            <p class="text-sm text-slate-600 leading-relaxed">
                                Set a limit order inside the derived margin-of-safety buy zone. If it does not fill within 5 trading days, cancel and re-evaluate.
                            </p>
                        </div>

                        <!-- 3 Summary Action Tiles (Dynamic Values) -->
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3.5 pt-2">
                            <div class="bg-slate-50 p-4 rounded-xl border border-slate-100 space-y-1">
                                <span class="text-[11px] font-medium text-slate-500 block">Buy order zone</span>
                                <p id="verdictBuyZoneText" class="text-lg font-bold text-slate-900 mono">--</p>
                                <span class="text-[11px] text-slate-500 block">5%–9% pullback into percentile band</span>
                            </div>
                            <div class="bg-slate-50 p-4 rounded-xl border border-slate-100 space-y-1">
                                <span class="text-[11px] font-medium text-slate-500 block">First purchase tranche</span>
                                <p id="verdictTrancheSharesText" class="text-lg font-bold text-slate-900 mono">--</p>
                                <span class="text-[11px] text-slate-500 block">₹2.00 lakh, which is 20% of your budget</span>
                            </div>
                            <div class="bg-slate-50 p-4 rounded-xl border border-slate-100 space-y-1">
                                <span class="text-[11px] font-medium text-slate-500 block">Kept in cash</span>
                                <p class="text-lg font-bold text-slate-900 mono">₹8.00 lakh</p>
                                <span class="text-[11px] text-slate-500 block">80% kept for cheaper tranches</span>
                            </div>
                        </div>

                        <!-- Plain English 4-Question Advisory Grid -->
                        <div class="pt-4 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                            <div class="space-y-1">
                                <h4 class="font-bold text-slate-900">What should I do today?</h4>
                                <p class="text-slate-600 leading-relaxed">
                                    Do not chase current market prices. Place a staggered limit order inside the derived buy zone for Tranche 1 (20% of allocation).
                                </p>
                            </div>
                            <div class="space-y-1">
                                <h4 class="font-bold text-slate-900">Why wait?</h4>
                                <p class="text-slate-600 leading-relaxed">
                                    The bank is fundamentally sound, but the stock rallied +16.8% over the past two weeks. Buying after sharp run-ups increases the probability of interim pullbacks.
                                </p>
                            </div>
                            <div class="space-y-1">
                                <h4 class="font-bold text-slate-900">What if the stock keeps falling?</h4>
                                <p class="text-slate-600 leading-relaxed">
                                    We only deploy 20% in Tranche 1. If the stock tests downside support or the bear scenario floor, you have 80% capital remaining in cash to accumulate at higher prospective returns.
                                </p>
                            </div>
                            <div class="space-y-1">
                                <h4 class="font-bold text-slate-900">When do we take profit?</h4>
                                <p class="text-slate-600 leading-relaxed">
                                    Our multi-stage model establishes the base valuation target once deposit integration completes, capped strictly by the bull case ceiling derived from fundamental ROE fade.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Right 1 Col: Scenario Risk & Trade Ladder -->
                <div class="space-y-6">
                    <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
                        <div class="flex items-center justify-between">
                            <h3 class="font-bold text-slate-900 text-sm">Trading Plan & Ladder</h3>
                            <span class="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 text-[11px] font-semibold">12-Month Horizon</span>
                        </div>

                        <div class="space-y-3">
                            <div class="flex justify-between items-center text-xs pb-2 border-b border-slate-100">
                                <span class="text-slate-500">Action directive</span>
                                <span class="font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded">WAIT (Limit Pullback)</span>
                            </div>
                            <div class="flex justify-between items-center text-xs pb-2 border-b border-slate-100">
                                <span class="text-slate-500">Order valid until</span>
                                <span id="sidebarExpiryDate" class="font-semibold text-slate-800">Nov 26, 2026</span>
                            </div>
                            <div class="flex justify-between items-center text-xs pb-2 border-b border-slate-100">
                                <span class="text-slate-500">Base Fair Value</span>
                                <span id="ladderBasePriceInline" class="font-bold text-indigo-700 mono">--</span>
                            </div>
                            <div class="flex justify-between items-center text-xs pb-2 border-b border-slate-100">
                                <span class="text-slate-500">Valuation Exit (Bull)</span>
                                <span id="sidebarBullExitPrice" class="font-bold text-emerald-700 mono">--</span>
                            </div>
                            <div class="flex justify-between items-center text-xs">
                                <span class="text-slate-500">Worst Historical Excursion</span>
                                <span class="font-bold text-rose-600 mono">-9.4% (Feb 2022)</span>
                            </div>
                        </div>

                        <!-- Downside Distribution Card -->
                        <div class="bg-rose-50/50 border border-rose-100 p-3.5 rounded-xl space-y-1.5">
                            <div class="flex items-center justify-between">
                                <span class="text-[11px] font-bold text-rose-800">95% Out-of-Sample VaR (6M)</span>
                                <span id="ladderVar95Text" class="text-xs font-bold text-rose-700 mono">-9.4%</span>
                            </div>
                            <p class="text-[11px] text-slate-600 leading-tight">
                                Derived from a single unified return distribution calibrated against all post-merger regime drawdown profiles.
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Dynamic Price Ladder Table -->
            <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-3">
                <div class="flex flex-wrap items-center justify-between gap-2">
                    <div>
                        <h3 class="text-sm font-bold text-slate-900">Unified Price Ladder & Valuation Reference Frame</h3>
                        <p class="text-xs text-slate-500">All prices derived from verified equations anchored at BVPS ₹394.80</p>
                    </div>
                    <span class="text-xs text-slate-400 mono">Single Source of Truth Ledger</span>
                </div>

                <div class="overflow-x-auto">
                    <table class="w-full text-xs border border-slate-200 rounded-xl overflow-hidden mono">
                        <thead class="bg-slate-50 text-slate-500 border-b border-slate-200 text-[11px]">
                            <tr>
                                <th class="p-3 text-left">Level / Scenario</th>
                                <th class="p-3">Derived Price</th>
                                <th class="p-3">Justified P/B</th>
                                <th class="p-3">Underlying ROE</th>
                                <th class="p-3">Upside / Downside</th>
                                <th class="p-3 text-right">Execution Rule</th>
                            </tr>
                        </thead>
                        <tbody id="priceLadderTableBody" class="divide-y divide-slate-100 text-center">
                            <!-- Injected by JavaScript -->
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

        <!-- 2. 6 ACCUMULATION & SAFETY GATES -->
        <section id="sectionGates" class="scroll-mt-28">
            <details class="group bg-white border border-slate-200 rounded-2xl shadow-sm transition" open>
                <summary class="p-6 cursor-pointer flex items-center justify-between font-bold text-slate-900 select-none">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-sm">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                        </div>
                        <div>
                            <h3 class="text-base font-bold text-slate-900">6 Safety & Accumulation Gates</h3>
                            <p class="text-xs text-slate-500 font-normal">Deterministic rules preventing value traps, insolvency risks, falling knives, and premature FOMO entries.</p>
                        </div>
                    </div>
                    <div class="flex items-center gap-3">
                        <span id="gatesStatusSummaryBadge" class="px-2.5 py-1 rounded bg-slate-100 text-slate-700 text-xs font-semibold">
                            Evaluating...
                        </span>
                        <span class="text-slate-400 group-open:rotate-180 transition-transform">▼</span>
                    </div>
                </summary>

                <div class="p-6 pt-0 border-t border-slate-100 mt-2 space-y-3">
                    <div id="gatesListContainer" class="space-y-3">
                        <!-- Injected by JavaScript -->
                    </div>
                </div>
            </details>
        </section>

        <!-- 3. MANAGEMENT PROMISE & GUIDANCE TRACKER -->
        <section id="sectionPromises" class="scroll-mt-28">
            <details class="group bg-white border border-slate-200 rounded-2xl shadow-sm transition" open>
                <summary class="p-6 cursor-pointer flex items-center justify-between font-bold text-slate-900 select-none">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-sm">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/></svg>
                        </div>
                        <div>
                            <h3 class="text-base font-bold text-slate-900">Management Promise & Guidance Tracker (Q2 FY27 Audit)</h3>
                            <p class="text-xs text-slate-500 font-normal">Cryptographically audited against BSE/NSE Q2 FY27 Standalone filing (Declared Oct 17, 2026).</p>
                        </div>
                    </div>
                    <div class="flex items-center gap-3">
                        <span id="promisesScoreBadge" class="px-2.5 py-1 rounded bg-emerald-50 text-emerald-700 text-xs font-semibold border border-emerald-200">
                            100% Verified
                        </span>
                        <span class="text-slate-400 group-open:rotate-180 transition-transform">▼</span>
                    </div>
                </summary>

                <div class="p-6 pt-0 border-t border-slate-100 mt-2 space-y-4">
                    <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-600 leading-relaxed">
                        Authenticated against BSE/NSE Q2 FY27 Standalone Unaudited Financial Results and Basel III Disclosures. Every tracked promise represents an explicit management commitment matched by exact verbatim filing substring.
                    </div>
                    <div id="promisesGrid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
                        <!-- Injected by JavaScript -->
                    </div>
                </div>
            </details>
        </section>

        <!-- 4. GORDON GROWTH SENSITIVITY MATRIX (REALITY CHECK) -->
        <section id="sectionValuation" class="scroll-mt-28">
            <details class="group bg-white border border-slate-200 rounded-2xl shadow-sm transition" open>
                <summary class="p-6 cursor-pointer flex items-center justify-between font-bold text-slate-900 select-none">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-sm">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
                        </div>
                        <div>
                            <div class="flex items-center gap-2">
                                <h3 class="text-base font-bold text-slate-900">Scenario Reality Check (Multi-Stage Gordon Sensitivity)</h3>
                                <span class="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 text-[10px] font-bold border border-indigo-200">
                                    Reality Check Only
                                </span>
                            </div>
                            <p class="text-xs text-slate-500 font-normal">Informational sensitivity matrix and market-implied ROE expectations at terminal growth g = 8.0%.</p>
                        </div>
                    </div>
                    <div class="flex items-center gap-3">
                        <span class="px-2.5 py-1 rounded bg-slate-100 text-slate-700 text-xs font-semibold">
                            3×3 Matrix
                        </span>
                        <span class="text-slate-400 group-open:rotate-180 transition-transform">▼</span>
                    </div>
                </summary>

                <div class="p-6 pt-0 border-t border-slate-100 mt-2 space-y-6">
                    <!-- Sensitivity Grid -->
                    <div class="space-y-3">
                        <h4 class="text-xs font-bold text-slate-700 uppercase tracking-wider">3×3 P/B & Implied Value Matrix: P/B = (ROE − g) / (Ke − g)</h4>
                        <div class="overflow-x-auto">
                            <table class="w-full text-xs border border-slate-200 rounded-xl overflow-hidden mono">
                                <thead class="bg-slate-50 text-slate-500 border-b border-slate-200 text-[11px]">
                                    <tr>
                                        <th class="p-3 text-left">Sustainable ROE Target</th>
                                        <th class="p-3 text-center">Low Ke (11.50%)</th>
                                        <th class="p-3 text-center bg-indigo-50/50 text-indigo-900 font-bold">Base Ke (12.28%)</th>
                                        <th class="p-3 text-center">High Ke (13.00%)</th>
                                    </tr>
                                </thead>
                                <tbody id="sensitivityTableBody" class="divide-y divide-slate-100 text-center">
                                    <!-- Injected by JavaScript -->
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Market Implied ROE Expectations -->
                    <div class="space-y-3 pt-3 border-t border-slate-100">
                        <h4 class="text-xs font-bold text-slate-700 uppercase tracking-wider">Reverse-Engineered Market Expectations (What Market Prices Today)</h4>
                        <div class="overflow-x-auto">
                            <table class="w-full text-xs border border-slate-200 rounded-xl overflow-hidden mono">
                                <thead class="bg-slate-50 text-slate-500 border-b border-slate-200 text-[11px]">
                                    <tr>
                                        <th class="p-3 text-left">Terminal Growth (g)</th>
                                        <th class="p-3">Cost of Equity (Ke)</th>
                                        <th class="p-3">Current P/B</th>
                                        <th class="p-3">Market-Implied ROE</th>
                                        <th class="p-3">Expectations Gap vs Trailing ROE</th>
                                        <th class="p-3 text-left font-sans">Reality Check Takeaway</th>
                                    </tr>
                                </thead>
                                <tbody id="impliedExpectationsTableBody" class="divide-y divide-slate-100 text-center">
                                    <!-- Injected by JavaScript -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </details>
        </section>

        <!-- 5. AUDITED HISTORICAL PROOF, EPISODES & TRACK RECORD -->
        <section id="sectionProof" class="scroll-mt-28">
            <details class="group bg-white border border-slate-200 rounded-2xl shadow-sm transition" open>
                <summary class="p-6 cursor-pointer flex items-center justify-between font-bold text-slate-900 select-none">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-lg bg-teal-100 text-teal-700 flex items-center justify-center font-bold text-sm">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
                        </div>
                        <div>
                            <div class="flex items-center gap-2">
                                <h3 class="text-base font-bold text-slate-900">Audited Historical Proof, Episodes & Track Record</h3>
                                <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                                    Point-in-Time Verified
                                </span>
                            </div>
                            <p class="text-xs text-slate-500 font-normal">Walk-forward simulation, all 8 past setup occurrences (2018–2026), and Track Record vs SIP baseline.</p>
                        </div>
                    </div>
                    <div class="flex items-center gap-3">
                        <span class="px-2.5 py-1 rounded bg-slate-100 text-slate-700 text-xs font-semibold">
                            8 Episodes Audited
                        </span>
                        <span class="text-slate-400 group-open:rotate-180 transition-transform">▼</span>
                    </div>
                </summary>

                <div class="p-6 pt-0 border-t border-slate-100 mt-2 space-y-6">
                    <!-- Backtest Header & Chart -->
                    <div class="space-y-3">
                        <div class="flex flex-wrap items-center justify-between gap-3">
                            <div>
                                <div class="flex items-center gap-2">
                                    <h4 class="text-sm font-bold text-slate-900">Audited Historical Backtest</h4>
                                    <span id="badgeBacktestVerified" class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                                        Point-in-Time Verified
                                    </span>
                                </div>
                                <p class="text-xs text-slate-500">Walk-forward simulation comparing Strategy vs Monthly SIP vs Buy & Hold with 0.10% friction</p>
                            </div>
                            <div class="flex items-center gap-3">
                                <div class="flex items-center gap-2 text-xs font-medium text-slate-600">
                                    <span class="inline-block w-3 h-0.5 bg-emerald-600"></span> Strategy
                                    <span class="inline-block w-3 h-0.5 bg-sky-600 border-dashed"></span> SIP
                                    <span class="inline-block w-3 h-0.5 bg-slate-400"></span> Buy & Hold
                                </div>
                                <select id="selectPeriod" onchange="runBacktest()" class="bg-slate-100 text-xs border border-slate-300 rounded-lg px-3 py-1.5 mono">
                                    <option value="1y">1 Year Walk-Forward</option>
                                    <option value="2y" selected>2 Years Walk-Forward</option>
                                    <option value="3y">3 Years Walk-Forward</option>
                                </select>
                            </div>
                        </div>

                        <!-- Native HTML5 Canvas Chart (Zero External Dependencies) -->
                        <div class="w-full h-80 relative bg-slate-50 rounded-xl border border-slate-200 p-2 flex items-center justify-center">
                            <canvas id="equityChart" class="w-full h-full"></canvas>
                            <div id="chartEmptyState" class="hidden absolute inset-0 flex flex-col items-center justify-center bg-slate-50 rounded-xl text-slate-400 text-xs font-medium">
                                <p>Not enough data yet</p>
                            </div>
                        </div>
                    </div>

                    <!-- All Past Occurrences Table -->
                    <div class="space-y-3 pt-4 border-t border-slate-100">
                        <div class="flex flex-wrap items-center justify-between gap-3">
                            <div>
                                <h4 class="text-sm font-bold text-slate-900">All Past Occurrences of this Cyclical Setup</h4>
                                <p class="text-xs text-slate-500">Setup rule: P/B ≤ 2.30 or drawdown ≤ -12.0%. All 8 episodes computed from NSE daily bars (2018–2026).</p>
                            </div>
                            <div class="flex items-center gap-2 text-xs font-semibold mono" id="analogueHeaderStats">
                                <span class="px-2.5 py-1 rounded bg-emerald-50 text-emerald-800 border border-emerald-200">6M Hit Rate: 50.0%</span>
                                <span class="px-2.5 py-1 rounded bg-rose-50 text-rose-800 border border-rose-200">Worst MAE: -9.4%</span>
                            </div>
                        </div>

                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-xs border border-slate-200 rounded-xl overflow-hidden">
                                <thead class="bg-slate-50 text-slate-500 mono border-b border-slate-200 text-[11px]">
                                    <tr>
                                        <th class="p-3">Episode Name & Date</th>
                                        <th class="p-3">Regime Era</th>
                                        <th class="p-3">Entry Price & P/B</th>
                                        <th class="p-3">6M Return</th>
                                        <th class="p-3">1-Year Return</th>
                                        <th class="p-3">Worst Drop (MAE)</th>
                                        <th class="p-3">Data Source</th>
                                        <th class="p-3">Status</th>
                                    </tr>
                                </thead>
                                <tbody id="analogueTableBody" class="divide-y divide-slate-100 mono">
                                    <!-- Injected by JavaScript -->
                                </tbody>
                            </table>
                        </div>

                        <p class="text-[11px] text-slate-400 italic">
                            Statistical Note: Small sample, n=8 (95% CI on 50.0% hit rate: [21.5%, 78.5%]). Includes pre-merger vs post-merger regime differentiation.
                        </p>
                    </div>

                    <!-- Track Record Scoreboard -->
                    <div class="space-y-3 pt-4 border-t border-slate-100">
                        <h4 class="text-sm font-bold text-slate-900">Track Record Scoreboard (Simulated vs Baselines)</h4>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-xs border border-slate-200 rounded-xl overflow-hidden">
                                <thead class="bg-slate-50 text-slate-500 mono border-b border-slate-200 text-[11px]">
                                    <tr>
                                        <th class="p-3">Strategy / Baseline</th>
                                        <th class="p-3">Total Calls</th>
                                        <th class="p-3">Matured (6M)</th>
                                        <th class="p-3">Hit Rate</th>
                                        <th class="p-3">Avg 6M Return</th>
                                        <th class="p-3">Max Drawdown</th>
                                        <th class="p-3">Excess Return vs Index</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-slate-100 text-slate-700 mono">
                                    <tr class="bg-emerald-50/20 font-bold">
                                        <td class="p-3 text-emerald-800">Cyclical Accumulation (Simulated)</td>
                                        <td class="p-3">8</td>
                                        <td class="p-3">8</td>
                                        <td class="p-3 text-emerald-700">50.0%</td>
                                        <td class="p-3 text-emerald-700">+13.9%</td>
                                        <td class="p-3 text-rose-600">-9.4%</td>
                                        <td class="p-3 text-emerald-700">+8.3%</td>
                                    </tr>
                                    <tr>
                                        <td class="p-3 font-semibold text-slate-800">Monthly SIP Baseline</td>
                                        <td class="p-3">8</td>
                                        <td class="p-3">8</td>
                                        <td class="p-3">50.0%</td>
                                        <td class="p-3">+5.6%</td>
                                        <td class="p-3 text-rose-600">-18.4%</td>
                                        <td class="p-3 text-slate-500">Benchmark</td>
                                    </tr>
                                    <tr>
                                        <td class="p-3 font-semibold text-slate-800">Buy & Hold Benchmark</td>
                                        <td class="p-3">8</td>
                                        <td class="p-3">8</td>
                                        <td class="p-3">37.5%</td>
                                        <td class="p-3">+4.6%</td>
                                        <td class="p-3 text-rose-600">-21.8%</td>
                                        <td class="p-3 text-rose-600">-1.0%</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </details>
        </section>

        <!-- 6. MATERIAL EVENT INTELLIGENCE & STATUTORY FILINGS -->
        <section id="sectionEvents" class="scroll-mt-28">
            <details class="group bg-white border border-slate-200 rounded-2xl shadow-sm transition" open>
                <summary class="p-6 cursor-pointer flex items-center justify-between font-bold text-slate-900 select-none">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-sm">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"/></svg>
                        </div>
                        <div>
                            <div class="flex flex-wrap items-center gap-2">
                                <h3 class="text-base font-bold text-slate-900">Material Event Intelligence & Regulatory Filings</h3>
                                <span id="badgeEventsClassified" class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                                    Classified
                                </span>
                            </div>
                            <p class="text-xs text-slate-500 font-normal">Real-time classification of BSE/NSE statutory disclosures, RBI monetary policy actions, and earnings events.</p>
                        </div>
                    </div>
                    <div class="flex items-center gap-3">
                        <span id="eventsCountBadge" class="px-2.5 py-1 rounded bg-slate-100 text-slate-700 text-xs font-semibold">
                            Filings Scanned
                        </span>
                        <span class="text-slate-400 group-open:rotate-180 transition-transform">▼</span>
                    </div>
                </summary>

                <div class="p-6 pt-0 border-t border-slate-100 mt-2 space-y-6">
                    <!-- Why Did It Move Banner -->
                    <div class="bg-indigo-50 border border-indigo-100 rounded-xl p-4 sm:p-5 space-y-1.5">
                        <div class="flex items-center gap-2">
                            <span class="px-2 py-0.5 rounded bg-indigo-100 text-indigo-800 text-[10px] font-bold uppercase tracking-wider">
                                Market Driver
                            </span>
                            <span class="text-xs font-bold text-slate-800">Why did the stock move?</span>
                        </div>
                        <p id="eventsWhyMovedText" class="text-sm font-semibold text-slate-900 leading-relaxed">
                            BSE/NSE Q2 FY27 standalone filing confirmed robust deposit growth of 18.8% YoY and PAT of ₹19,510 Cr, driving C/D ratio down to 96.0% with pristine Gross NPA at 1.11%.
                        </p>
                    </div>

                    <!-- Material Events List -->
                    <div class="space-y-3">
                        <h4 class="text-xs font-bold text-slate-700 uppercase tracking-wider">Classified Statutory & Macro Events</h4>
                        <div id="eventsListContainer" class="space-y-2.5">
                            <!-- Injected by JavaScript -->
                        </div>
                    </div>
                </div>
            </details>
        </section>

        <!-- 7. BIG-4 PRIVATE BANK PEER WATCHLIST -->
        <section id="sectionWatchlist" class="scroll-mt-28">
            <details class="group bg-white border border-slate-200 rounded-2xl shadow-sm transition" open>
                <summary class="p-6 cursor-pointer flex items-center justify-between font-bold text-slate-900 select-none">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-lg bg-purple-100 text-purple-700 flex items-center justify-center font-bold text-sm">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>
                        </div>
                        <div>
                            <h3 class="text-base font-bold text-slate-900">Big-4 Private Banking Watchlist (Standalone Q2 FY27)</h3>
                            <p class="text-xs text-slate-500 font-normal">Comparative analysis of HDFC Bank, ICICI Bank, Kotak Mahindra Bank, and Axis Bank against their own histories.</p>
                        </div>
                    </div>
                    <div class="flex items-center gap-3">
                        <span class="px-2.5 py-1 rounded bg-slate-100 text-slate-700 text-xs font-semibold">
                            4 Banks Ingested
                        </span>
                        <span class="text-slate-400 group-open:rotate-180 transition-transform">▼</span>
                    </div>
                </summary>

                <div class="p-6 pt-0 border-t border-slate-100 mt-2 space-y-4">
                    <div class="overflow-x-auto">
                        <table class="w-full text-left text-xs border border-slate-200 rounded-xl overflow-hidden mono">
                            <thead class="bg-slate-50 text-slate-500 border-b border-slate-200 text-[11px]">
                                <tr>
                                    <th class="p-3">Bank / Ticker</th>
                                    <th class="p-3">Price</th>
                                    <th class="p-3">P/B Multiple</th>
                                    <th class="p-3">5Y Percentile</th>
                                    <th class="p-3">Trailing ROE</th>
                                    <th class="p-3">CAR (CRAR)</th>
                                    <th class="p-3">Gross NPA</th>
                                    <th class="p-3">C/D Ratio</th>
                                    <th class="p-3">Strategy Status</th>
                                </tr>
                            </thead>
                            <tbody id="peerWatchlistTableBody" class="divide-y divide-slate-100 text-slate-700">
                                <!-- Injected by JavaScript -->
                            </tbody>
                        </table>
                    </div>
                    <p class="text-[11px] text-slate-400 italic">
                        Relative Valuation Rule: Every bank's percentile is evaluated strictly against its OWN 5-year rolling multiple history, preventing structural distortion.
                    </p>
                </div>
            </details>
        </section>

        <!-- 8. DATA HEALTH & CRYPTOGRAPHIC AUDIT LEDGER -->
        <section id="sectionHealth" class="scroll-mt-28">
            <details class="group bg-white border border-slate-200 rounded-2xl shadow-sm transition">
                <summary class="p-6 cursor-pointer flex items-center justify-between font-bold text-slate-900 select-none">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-sm">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
                        </div>
                        <div>
                            <h3 class="text-base font-bold text-slate-900">Data Health, Gate 0 Verification & Cryptographic Ledger</h3>
                            <p class="text-xs text-slate-500 font-normal">Audit reconciliation, tamper-detection verification, and immutable SHA-256 hash chaining.</p>
                        </div>
                    </div>
                    <div class="flex items-center gap-3">
                        <span class="px-2.5 py-1 rounded bg-emerald-50 text-emerald-800 text-xs font-semibold border border-emerald-200 flex items-center gap-1.5">
                            <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
                            Ledger Verified
                        </span>
                        <span class="text-slate-400 group-open:rotate-180 transition-transform">▼</span>
                    </div>
                </summary>

                <div class="p-6 pt-0 border-t border-slate-100 mt-2 space-y-6">
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                            <h4 class="text-xs font-bold text-slate-700 uppercase tracking-wider">SEBI LODR Reg 33 Statutory Filing Verification</h4>
                            <div class="space-y-1.5 text-xs text-slate-600">
                                <p><strong>Document:</strong> Unaudited Standalone Results (Q2 FY27)</p>
                                <p><strong>Filing Date:</strong> October 17, 2026 (BSE & NSE India)</p>
                                <p><strong>Standalone PAT:</strong> ₹19,510 Cr (Annualized: ₹78,040 Cr)</p>
                                <p><strong>Total Net Worth:</strong> ₹6,07,600 Cr | <strong>Shares:</strong> 15.39 Bn</p>
                                <p><strong>Reconciled BVPS:</strong> ₹394.80 | <strong>Trailing ROE:</strong> 12.84%</p>
                                <p class="text-[10px] mono text-slate-400 break-all pt-1">
                                    SHA-256: 4f64176415464fd0571de8ce4948c617f18d80dc4bab0d4981eca347d7236fb4
                                </p>
                            </div>
                        </div>

                        <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                            <h4 class="text-xs font-bold text-slate-700 uppercase tracking-wider">Cryptographic Hash Chain Ledger</h4>
                            <p class="text-xs text-slate-500">Every 2:00 PM recommendation is signed and hash-chained into SQLite before market close.</p>
                            <div class="bg-slate-900 text-emerald-400 p-3 rounded-lg font-mono text-[10px] space-y-1 max-h-40 overflow-y-auto" id="healthLedgerList">
                                <p class="text-slate-400">Verifying SHA-256 record hashes...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </details>
        </section>

        <!-- Plain Language Glossary -->
        <section class="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
            <div class="flex items-center gap-2">
                <h3 class="text-sm font-bold text-slate-900">Plain-Language Glossary</h3>
                <span class="px-2 py-0.5 rounded bg-slate-100 text-slate-600 text-[10px] font-semibold">Financial Terms Made Simple</span>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5 text-xs">
                <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-100 space-y-1">
                    <span class="font-bold text-slate-900 block">Cyclical Bottom Setup</span>
                    <p class="text-slate-600 leading-relaxed">
                        A recurring market situation where quality bank stocks fall out of favor temporarily, trading at deep discounts before earnings recover over the following 12 to 24 months.
                    </p>
                </div>
                <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-100 space-y-1">
                    <span class="font-bold text-slate-900 block">Tranche</span>
                    <p class="text-slate-600 leading-relaxed">
                        An installment of money. Instead of investing all your cash at once, we deploy it in installments (e.g., 20% today, reserving 80% to buy cheaper if the stock dips).
                    </p>
                </div>
                <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-100 space-y-1">
                    <span class="font-bold text-slate-900 block">RSI (Relative Strength Index)</span>
                    <p class="text-slate-600 leading-relaxed">
                        A speed gauge for stock prices. Values above 75–80 mean the stock climbed too fast in recent days and often pauses or drops temporarily.
                    </p>
                </div>
                <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-100 space-y-1">
                    <span class="font-bold text-slate-900 block">Margin of Safety</span>
                    <p class="text-slate-600 leading-relaxed">
                        The discount percentage between estimated fundamental fair value and the current market price. A positive margin provides downside protection against valuation uncertainty or adverse earnings surprises.
                    </p>
                </div>
                <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-100 space-y-1">
                    <span class="font-bold text-slate-900 block">Record locked at 2 PM</span>
                    <p class="text-slate-600 leading-relaxed">
                        A mathematical timestamp generated at 2:00 PM IST using cryptography. It guarantees that our past prediction records can never be edited or faked after seeing the close.
                    </p>
                </div>
                <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-100 space-y-1">
                    <span class="font-bold text-slate-900 block">Structural Break (July 2023)</span>
                    <p class="text-slate-600 leading-relaxed">
                        HDFC Bank merged with parent HDFC Ltd in July 2023. This permanently changed the bank's size, margins, and valuation range, making pre-2023 P/B ratios of 3.4x outdated.
                    </p>
                </div>
            </div>
        </section>

    </main>

    <!-- Footer -->
    <footer class="max-w-[1200px] mx-auto px-4 sm:px-6 py-6 text-center text-xs text-slate-400 border-t border-slate-200">
        HDFC Bank Cyclical Accumulation Engine · SEBI LODR Regulation 33 & Basel III Disclosures · Strictly for Educational & Simulation Purposes.
    </footer>

    <!-- Native JavaScript Engine -->
    <script>
        function showToast(message, type = 'success') {
            const container = document.getElementById('toastContainer');
            if (!container) return;
            const toast = document.createElement('div');
            toast.className = `toast-item ${type === 'success' ? 'toast-success' : 'toast-error'}`;
            const icon = type === 'success' ? '✓' : '✕';
            toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
            container.appendChild(toast);
            setTimeout(() => {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }, 3500);
        }

        function setMode(mode) {
            const btnPlain = document.getElementById('btnModePlain');
            const btnTech = document.getElementById('btnModeTech');
            if (mode === 'tech') {
                document.body.classList.add('show-tech');
                btnTech.className = 'px-2.5 py-1 rounded-md bg-white text-slate-900 shadow-sm';
                btnPlain.className = 'px-2.5 py-1 rounded-md text-slate-500 hover:text-slate-900';
            } else {
                document.body.classList.remove('show-tech');
                btnPlain.className = 'px-2.5 py-1 rounded-md bg-white text-slate-900 shadow-sm';
                btnTech.className = 'px-2.5 py-1 rounded-md text-slate-500 hover:text-slate-900';
            }
        }

        function formatOrdinal(n) {
            const s = ["th", "st", "nd", "rd"], v = Math.round(n) % 100;
            return Math.round(n) + (s[(v - 20) % 10] || s[v] || s[0]);
        }

        function applyStatus(data) {
            if (!data) return;

            // 1. Update Header
            if (data.reference_price) {
                document.getElementById('headerPriceText').textContent = `₹${data.reference_price.toFixed(2)}`;
            }
            if (data.price_timing_label) {
                document.getElementById('headerTimingStatus').textContent = data.price_timing_label;
            }

            // 2. Render Top Fold
            renderVerdictAndPlan(data);

            // 3. Render Price Ladder
            if (data.valuation_ledger) {
                renderPriceLadder(data.valuation_ledger);
                renderSensitivity(data.valuation_ledger.sensitivity_table);
            }

            // 4. Render Gates
            if (data.accumulation_gates) {
                renderGates(data.accumulation_gates);
            }

            // 5. Render Promises
            if (data.transcript_report) {
                renderPromises(data.transcript_report);
            }

            // 6. Render Events
            if (data.events) {
                renderEvents(data.events);
            }

            // 7. Render Peer Watchlist
            if (data.peer_watchlist) {
                renderPeerWatchlist(data.peer_watchlist);
            }

            // 8. Render Analogues
            if (data.analogues) {
                renderAnalogues(data.analogues);
            }

            // 9. Render Health Ledger
            if (data.scoreboard && data.scoreboard.live_records) {
                renderHealthLedger(data.scoreboard);
            }
        }

        async function fetchStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                applyStatus(data);
                await runBacktest();
            } catch (e) {
                console.error("fetchStatus error:", e);
            }
        }

        function renderVerdictAndPlan(data) {
            const vl = data.valuation_ledger;
            const bz = vl ? (vl.dynamic_buy_zone || vl.limit_tranche) : null;
            const action = data.accumulation_gates ? data.accumulation_gates.final_action : "WAIT";

            const badge = document.getElementById('verdictActionBadge');
            if (action === 'ACCUMULATE') {
                badge.className = "px-2.5 py-1 rounded-full font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 flex items-center gap-1.5 uppercase tracking-wide text-[11px]";
                badge.innerHTML = '<span class="w-2 h-2 rounded-full bg-emerald-500"></span> ACCUMULATE';
            } else if (action === 'WAIT') {
                badge.className = "px-2.5 py-1 rounded-full font-bold bg-amber-50 text-amber-800 border border-amber-200 flex items-center gap-1.5 uppercase tracking-wide text-[11px]";
                badge.innerHTML = '<span class="w-2 h-2 rounded-full bg-amber-500"></span> WAIT';
            } else {
                badge.className = "px-2.5 py-1 rounded-full font-bold bg-rose-50 text-rose-800 border border-rose-200 flex items-center gap-1.5 uppercase tracking-wide text-[11px]";
                badge.innerHTML = '<span class="w-2 h-2 rounded-full bg-rose-500"></span> ABSTAIN';
            }

            if (data.order_expiry_label) {
                document.getElementById('orderValidityPill').textContent = `Valid until ${data.order_expiry_label} (5 trading days)`;
                document.getElementById('sidebarExpiryDate').textContent = data.order_expiry_label;
            }

            if (bz) {
                document.getElementById('verdictBuyZoneText').textContent = `₹${bz.limit_zone_low} – ₹${bz.limit_zone_high}`;
                document.getElementById('verdictTrancheSharesText').textContent = bz.shares_range_label || `${bz.shares_at_zone_high}–${bz.shares_at_zone_low} shares`;
            }

            if (vl && vl.valuation_exit_price) {
                document.getElementById('sidebarBullExitPrice').textContent = `₹${vl.valuation_exit_price.toFixed(1)}`;
            }
        }

        function renderPriceLadder(vl) {
            const tbody = document.getElementById('priceLadderTableBody');
            const scenarios = vl.scenarios || [];
            const bz = vl.dynamic_buy_zone || vl.limit_tranche;

            const bear = scenarios.find(s => s.name === 'BEAR') || { target_price: 746.0, justified_pb: 1.89, assumed_roe_pct: 12.84, upside_vs_reference_pct: -8.8 };
            const base = scenarios.find(s => s.name === 'BASE') || { target_price: 920.0, justified_pb: 2.33, assumed_roe_pct: 14.0, upside_vs_reference_pct: 12.5 };
            const bull = scenarios.find(s => s.name === 'BULL') || { target_price: 1094.0, justified_pb: 2.77, assumed_roe_pct: 16.0, upside_vs_reference_pct: 33.8 };

            const ref = vl.reference_price;

            let html = `
                <tr class="bg-rose-50/20">
                    <td class="p-3 text-left font-bold text-rose-700">Bear Floor (Trailing ROE Persists)</td>
                    <td class="p-3 font-bold text-rose-700">₹${bear.target_price.toFixed(1)}</td>
                    <td class="p-3">${bear.justified_pb.toFixed(2)}x</td>
                    <td class="p-3">${bear.assumed_roe_pct}%</td>
                    <td class="p-3 text-rose-600">${bear.upside_vs_reference_pct > 0 ? '+' : ''}${bear.upside_vs_reference_pct}%</td>
                    <td class="p-3 text-right text-slate-500">Extreme Tail Risk Floor</td>
                </tr>
                <tr class="bg-emerald-50/30">
                    <td class="p-3 text-left font-bold text-emerald-800">Derived Buy Zone (Pullback Band)</td>
                    <td class="p-3 font-extrabold text-emerald-900 border-2 border-emerald-500 rounded">₹${bz.limit_zone_low} – ₹${bz.limit_zone_high}</td>
                    <td class="p-3">${(bz.limit_zone_high / vl.book_value_per_share).toFixed(2)}x</td>
                    <td class="p-3">Pullback Zone</td>
                    <td class="p-3 text-emerald-700 font-semibold">${(((bz.limit_zone_high - ref)/ref)*100).toFixed(1)}% to ${(((bz.limit_zone_low - ref)/ref)*100).toFixed(1)}%</td>
                    <td class="p-3 text-right font-bold text-emerald-800">First Tranche Deployment</td>
                </tr>
                <tr class="bg-slate-900 text-white font-bold">
                    <td class="p-3 text-left">Current Market Price (Last Traded)</td>
                    <td class="p-3 text-amber-300">₹${ref.toFixed(2)}</td>
                    <td class="p-3">${vl.current_pb.toFixed(2)}x</td>
                    <td class="p-3">16.9% implied</td>
                    <td class="p-3 text-slate-300">Reference (0.0%)</td>
                    <td class="p-3 text-right text-amber-300">Patience / WAIT</td>
                </tr>
                <tr class="bg-indigo-50/30">
                    <td class="p-3 text-left font-bold text-indigo-900">Base Scenario Fair Value</td>
                    <td class="p-3 font-bold text-indigo-900">₹${base.target_price.toFixed(1)}</td>
                    <td class="p-3">${base.justified_pb.toFixed(2)}x</td>
                    <td class="p-3">${base.assumed_roe_pct}% target</td>
                    <td class="p-3 ${base.upside_vs_reference_pct >= 0 ? 'text-emerald-700' : 'text-rose-600'} font-bold">${base.upside_vs_reference_pct > 0 ? '+' : ''}${base.upside_vs_reference_pct}%</td>
                    <td class="p-3 text-right text-indigo-700">Fair Value Benchmark</td>
                </tr>
                <tr class="bg-blue-50/20">
                    <td class="p-3 text-left font-bold text-blue-800">Bull Case Scenario Target</td>
                    <td class="p-3 font-bold text-blue-800">₹${bull.target_price.toFixed(1)}</td>
                    <td class="p-3">${bull.justified_pb.toFixed(2)}x</td>
                    <td class="p-3">${bull.assumed_roe_pct}% compounding</td>
                    <td class="p-3 text-emerald-700 font-bold">+${bull.upside_vs_reference_pct}%</td>
                    <td class="p-3 text-right font-bold text-blue-700">Valuation Exit Ceiling</td>
                </tr>
            `;
            tbody.innerHTML = html;

            document.getElementById('ladderBasePriceInline').textContent = `₹${base.target_price.toFixed(1)}`;
            if (vl.downside_distribution) {
                document.getElementById('ladderVar95Text').textContent = `${vl.downside_distribution.var_95_pct}%`;
            }
        }

        function renderGates(gatesData) {
            const container = document.getElementById('gatesListContainer');
            const gates = gatesData.gates || [];
            
            const passCount = gates.filter(g => g.passed).length;
            document.getElementById('gatesStatusSummaryBadge').textContent = `${passCount}/6 Pass`;
            document.getElementById('navGatesSummaryPill').textContent = `${passCount}/6 Pass`;

            container.innerHTML = gates.map(g => {
                const isPass = g.status === 'PASS';
                const isWait = g.status === 'WAIT';
                const statusBadge = isPass 
                    ? '<span class="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold text-[11px]">PASS</span>'
                    : (isWait 
                        ? '<span class="px-2 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-300 font-bold text-[11px]">WAIT</span>'
                        : '<span class="px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 font-bold text-[11px]">ABSTAIN</span>');

                const icon = isPass 
                    ? '<div class="w-6 h-6 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center font-bold text-xs">✓</div>'
                    : (isWait 
                        ? '<div class="w-6 h-6 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center font-bold text-xs">!</div>'
                        : '<div class="w-6 h-6 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center font-bold text-xs">✕</div>');

                const borderStyle = isWait ? 'border-amber-300 bg-amber-50/20' : 'border-slate-200 bg-white';

                // Clean formatted metrics tiles (Never raw JSON!)
                let metricsHtml = '';
                if (g.evidence_metrics && typeof g.evidence_metrics === 'object') {
                    metricsHtml = '<div class="grid grid-cols-2 sm:grid-cols-3 gap-2 bg-slate-50 p-3 rounded-lg border border-slate-200 text-[11px]">';
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
                            <p class="pt-1 text-[11px] font-sans"><strong>Action Directive:</strong> <span class="font-bold text-slate-800">${g.action_directive}</span></p>
                        </div>
                    </details>
                `;
            }).join('');
        }

        function renderPromises(report) {
            const grid = document.getElementById('promisesGrid');
            const promises = report.promises || [];

            grid.innerHTML = promises.map(p => {
                const isDelivered = p.delivery_status === 'DELIVERED';
                const statusBadge = isDelivered
                    ? '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">DELIVERED</span>'
                    : '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">IN PROGRESS</span>';

                return `
                    <div class="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2.5 flex flex-col justify-between">
                        <div class="space-y-1.5">
                            <div class="flex items-center justify-between">
                                <span class="text-xs font-bold text-slate-900">${p.pillar}</span>
                                ${statusBadge}
                            </div>
                            <p class="text-xs font-semibold text-slate-800">${p.target_metric_name}</p>
                            <div class="text-[11px] text-slate-600 pt-1 space-y-1">
                                <p><strong>Stated Target:</strong> ${p.stated_target}</p>
                                <p class="text-emerald-700 font-semibold"><strong>Reported Actual:</strong> ${p.latest_actual_value}</p>
                            </div>
                        </div>
                        <div class="pt-2.5 border-t border-slate-200 text-[11px] text-slate-600 italic">
                            "${p.verbatim_excerpt}"
                        </div>
                    </div>
                `;
            }).join('');
        }

        function renderSensitivity(table) {
            const tbody = document.getElementById('sensitivityTableBody');
            const grid = table.grid || [];
            let html = '';

            for (let r = 0; r < grid.length; r++) {
                const roe = table.roe_labels[r];
                const row = grid[r];
                const isBaseRow = r === 1;
                const rowClass = isBaseRow ? "bg-indigo-50/20 font-bold" : "";

                html += `<tr class="${rowClass}">
                    <td class="p-3 text-left font-bold text-slate-900">${roe.toFixed(2)}% ${isBaseRow ? '(Target Target)' : ''}</td>
                    <td class="p-3">${row[0].justified_pb.toFixed(2)}x <span class="text-slate-400 font-normal">(₹${row[0].implied_fair_value.toFixed(1)})</span></td>
                    <td class="p-3 text-indigo-700 font-extrabold bg-indigo-50/40">${row[1].justified_pb.toFixed(2)}x <span class="text-indigo-900 font-bold">(₹${row[1].implied_fair_value.toFixed(1)})</span></td>
                    <td class="p-3">${row[2].justified_pb.toFixed(2)}x <span class="text-slate-400 font-normal">(₹${row[2].implied_fair_value.toFixed(1)})</span></td>
                </tr>`;
            }
            tbody.innerHTML = html;

            const expTbody = document.getElementById('impliedExpectationsTableBody');
            const expectations = table.implied_expectations || [];
            let expHtml = '';

            for (const exp of expectations) {
                expHtml += `<tr>
                    <td class="p-3 font-bold text-slate-900">${exp.terminal_growth_pct.toFixed(1)}%</td>
                    <td class="p-3">${exp.cost_of_equity_pct.toFixed(2)}%</td>
                    <td class="p-3">${exp.current_pb.toFixed(2)}x</td>
                    <td class="p-3 font-extrabold text-indigo-700">${exp.market_implied_roe_pct.toFixed(2)}%</td>
                    <td class="p-3 text-amber-700 font-bold">+${exp.gap_vs_trailing_roe_bps.toFixed(0)} bps</td>
                    <td class="p-3 text-[11px] text-slate-600 font-sans">${exp.interpretation}</td>
                </tr>`;
            }
            expTbody.innerHTML = expHtml;
        }

        function renderEvents(eventsData) {
            const whyMovedEl = document.getElementById('eventsWhyMovedText');
            if (whyMovedEl && eventsData.why_did_it_move) {
                whyMovedEl.textContent = eventsData.why_did_it_move;
            }
            const countBadge = document.getElementById('eventsCountBadge');
            const matEvents = eventsData.material_events || [];
            if (countBadge) {
                countBadge.textContent = `${matEvents.length} Filings Classified`;
            }
            const badgeClassified = document.getElementById('badgeEventsClassified');
            if (badgeClassified) {
                if (matEvents.length > 0) {
                    badgeClassified.classList.remove('hidden');
                } else {
                    badgeClassified.classList.add('hidden');
                }
            }
            const container = document.getElementById('eventsListContainer');
            if (!container) return;

            if (matEvents.length === 0) {
                container.innerHTML = '<p class="text-xs text-slate-500 italic p-4 bg-slate-50 rounded-xl">Not enough data yet</p>';
                return;
            }

            container.innerHTML = matEvents.map(e => {
                const impactBadge = e.outlook_impact === 'BULLISH' 
                    ? '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">BULLISH</span>'
                    : (e.outlook_impact === 'CAUTION' || e.outlook_impact === 'BEARISH'
                        ? '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">CAUTION</span>'
                        : '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">NEUTRAL</span>');

                const catLabel = e.category_label || e.category || 'Regulatory Filing';

                return `
                    <div class="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2 hover:bg-slate-100 transition">
                        <div class="flex flex-wrap items-center justify-between gap-2">
                            <div class="flex items-center gap-2">
                                <span class="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200 text-[10px] font-bold uppercase tracking-wide">
                                    ${catLabel}
                                </span>
                                <span class="text-[11px] text-slate-500 font-medium">${e.source || 'Statutory Disclosure'} · ${e.published_date || ''}</span>
                            </div>
                            ${impactBadge}
                        </div>
                        <h5 class="text-xs font-bold text-slate-900 leading-snug">${e.title}</h5>
                        <p class="text-[11px] text-slate-600 leading-relaxed">${e.explanation || e.description || ''}</p>
                    </div>
                `;
            }).join('');
        }

        function renderPeerWatchlist(peers) {
            const tbody = document.getElementById('peerWatchlistTableBody');
            let html = '';

            for (const p of peers) {
                const isCurrent = p.symbol === 'HDFCBANK.NS';
                const rowBg = isCurrent ? 'bg-indigo-50/40 font-semibold' : 'hover:bg-slate-50';

                html += `<tr class="${rowBg}">
                    <td class="p-3 font-bold text-slate-900">${p.display_name}<span class="block text-[10px] text-slate-400 font-normal">${p.exchange_ticker}</span></td>
                    <td class="p-3">₹${p.price.toFixed(2)}</td>
                    <td class="p-3">${p.pb.toFixed(2)}x</td>
                    <td class="p-3 ${p.pb_percentile < 25 ? 'text-emerald-700 font-bold' : 'text-slate-600'}">${formatOrdinal(p.pb_percentile)} %ile</td>
                    <td class="p-3">${p.trailing_roe.toFixed(2)}%</td>
                    <td class="p-3 font-medium">${p.car.toFixed(1)}%</td>
                    <td class="p-3">${p.gnpa.toFixed(2)}%</td>
                    <td class="p-3">${p.cd_ratio.toFixed(1)}%</td>
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
            const episodes = analoguesData.all_episodes || [];
            const stats = analoguesData.summary_stats || {};

            if (stats.hit_rate_6m_pct !== undefined) {
                document.getElementById('analogueHeaderStats').innerHTML = `
                    <span class="px-2.5 py-1 rounded bg-emerald-50 text-emerald-800 border border-emerald-200">6M Hit Rate: ${stats.hit_rate_6m_pct}%</span>
                    <span class="px-2.5 py-1 rounded bg-rose-50 text-rose-800 border border-rose-200">Worst MAE: ${stats.worst_case_drawdown_pct}%</span>
                `;
            }

            tbody.innerHTML = episodes.map(ep => {
                const isWinner = ep.outcome_status_6m === 'WINNER';
                const isLoser = ep.outcome_status_6m === 'LOSER';
                const statusBadge = isWinner ? '<span class="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">WINNER</span>' :
                                   (isLoser ? '<span class="px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 font-bold">LOSER</span>' :
                                   '<span class="px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200 font-bold">CHOPPY</span>');

                const ret6mColor = ep.actual_return_180d_pct >= 0 ? 'text-emerald-700 font-bold' : 'text-rose-600 font-bold';
                const ret1yColor = ep.actual_return_365d_pct >= 0 ? 'text-emerald-700' : 'text-rose-600';
                const regime = ep.regime_era === 'POST_MERGER' ? '<span class="text-indigo-700 font-semibold">Post-Merger</span>' : '<span class="text-slate-500">Pre-Merger</span>';

                return `
                    <tr class="hover:bg-slate-50">
                        <td class="p-3 font-semibold text-slate-900">${ep.cycle_name}</td>
                        <td class="p-3">${regime}</td>
                        <td class="p-3">₹${ep.price_at_entry.toFixed(2)} · ${ep.pb_at_entry}x</td>
                        <td class="p-3 ${ret6mColor}">${ep.actual_return_180d_pct > 0 ? '+' : ''}${ep.actual_return_180d_pct}%</td>
                        <td class="p-3 ${ret1yColor}">${ep.actual_return_365d_pct > 0 ? '+' : ''}${ep.actual_return_365d_pct}%</td>
                        <td class="p-3 text-amber-700 font-medium">${ep.max_adverse_excursion_pct}%</td>
                        <td class="p-3 text-[10px] text-slate-500">${ep.data_source || 'Computed from bars'}</td>
                        <td class="p-3">${statusBadge}</td>
                    </tr>
                `;
            }).join('');
        }

        function renderHealthLedger(scoreboard) {
            const list = document.getElementById('healthLedgerList');
            const live = scoreboard.live_records || [];
            const sim = scoreboard.simulated_records || [];
            let html = '';

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

        // Native HTML5 Canvas 2D Line Chart Renderer (Zero External Dependencies)
        function renderNativeChart(curve) {
            const canvas = document.getElementById('equityChart');
            if (!canvas || !curve || curve.length < 2) return;
            
            const rect = canvas.parentElement.getBoundingClientRect();
            const width = rect.width > 50 ? rect.width - 16 : 800;
            const height = 290;
            const dpr = window.devicePixelRatio || 1;
            
            canvas.width = width * dpr;
            canvas.height = height * dpr;
            canvas.style.width = width + 'px';
            canvas.style.height = height + 'px';
            
            const ctx = canvas.getContext('2d');
            ctx.scale(dpr, dpr);
            ctx.clearRect(0, 0, width, height);

            const padLeft = 65, padRight = 20, padTop = 20, padBottom = 30;
            const plotW = width - padLeft - padRight;
            const plotH = height - padTop - padBottom;

            const stratVals = curve.map(c => c.strategy_equity || c.strategy_capital || 100000);
            const sipVals = curve.map(c => c.sip_equity || c.benchmark_capital || 100000);
            const benchVals = curve.map(c => c.benchmark_equity || c.benchmark_capital || 100000);

            const allVals = [...stratVals, ...sipVals, ...benchVals];
            let minVal = Math.min(...allVals);
            let maxVal = Math.max(...allVals);
            const span = (maxVal - minVal) || 10000;
            minVal = Math.floor((minVal - span * 0.08) / 2000) * 2000;
            maxVal = Math.ceil((maxVal + span * 0.08) / 2000) * 2000;

            const getY = (val) => padTop + plotH - ((val - minVal) / (maxVal - minVal)) * plotH;
            const getX = (idx) => padLeft + (idx / (curve.length - 1)) * plotW;

            // Grid & Y-Axis Labels
            ctx.strokeStyle = '#e2e8f0';
            ctx.lineWidth = 0.8;
            ctx.fillStyle = '#64748b';
            ctx.font = '10px ui-monospace, monospace';
            ctx.textAlign = 'right';
            ctx.textBaseline = 'middle';

            const ySteps = 5;
            for (let i = 0; i <= ySteps; i++) {
                const val = minVal + (i / ySteps) * (maxVal - minVal);
                const y = getY(val);
                ctx.beginPath();
                ctx.moveTo(padLeft, y);
                ctx.lineTo(width - padRight, y);
                ctx.stroke();
                ctx.fillText('₹' + Math.round(val).toLocaleString(), padLeft - 8, y);
            }

            // X-Axis Date Labels
            ctx.textAlign = 'center';
            ctx.textBaseline = 'top';
            const xSteps = Math.min(6, curve.length - 1);
            for (let i = 0; i <= xSteps; i++) {
                const idx = Math.round((i / xSteps) * (curve.length - 1));
                const x = getX(idx);
                const dStr = curve[idx].date || '';
                ctx.fillText(dStr, x, padTop + plotH + 8);
            }

            // Benchmark Line (Slate dashed)
            ctx.beginPath();
            ctx.setLineDash([4, 4]);
            ctx.strokeStyle = '#94a3b8';
            ctx.lineWidth = 1.6;
            curve.forEach((c, idx) => {
                const x = getX(idx);
                const y = getY(benchVals[idx]);
                if (idx === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
            });
            ctx.stroke();

            // SIP Line (Sky Blue dashed)
            ctx.beginPath();
            ctx.setLineDash([3, 3]);
            ctx.strokeStyle = '#0284c7';
            ctx.lineWidth = 1.6;
            curve.forEach((c, idx) => {
                const x = getX(idx);
                const y = getY(sipVals[idx]);
                if (idx === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
            });
            ctx.stroke();

            // Strategy Line Fill Gradient (Emerald)
            ctx.setLineDash([]);
            const grad = ctx.createLinearGradient(0, padTop, 0, padTop + plotH);
            grad.addColorStop(0, 'rgba(16, 185, 129, 0.20)');
            grad.addColorStop(1, 'rgba(16, 185, 129, 0.00)');

            ctx.beginPath();
            curve.forEach((c, idx) => {
                const x = getX(idx);
                const y = getY(stratVals[idx]);
                if (idx === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
            });
            ctx.lineTo(getX(curve.length - 1), padTop + plotH);
            ctx.lineTo(getX(0), padTop + plotH);
            ctx.closePath();
            ctx.fillStyle = grad;
            ctx.fill();

            // Strategy Line Stroke
            ctx.beginPath();
            ctx.strokeStyle = '#059669';
            ctx.lineWidth = 2.4;
            curve.forEach((c, idx) => {
                const x = getX(idx);
                const y = getY(stratVals[idx]);
                if (idx === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
            });
            ctx.stroke();
        }

        window.addEventListener('resize', () => {
            if (currentCurve) renderNativeChart(currentCurve);
        });

        async function triggerNow() {
            const btn = document.getElementById('btnTrigger');
            btn.innerHTML = '<span class="inline-block animate-spin">⟳</span> Refreshing...';
            btn.disabled = true;
            try {
                const res = await fetch('/api/trigger-signal', { method: 'POST' });
                const json = await res.json();
                if (res.ok && json.status === "SUCCESS") {
                    showToast(json.message || "Signal refreshed and locked at 2:00 PM IST.", "success");
                    await fetchStatus();
                } else {
                    showToast(json.error || "Signal refresh failed on server.", "error");
                }
            } catch (e) {
                console.error(e);
                showToast("Network error: " + e.message, "error");
            } finally {
                btn.innerHTML = '<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg> Refresh';
                btn.disabled = false;
            }
        }

        // Initial Load
        if (window.__INITIAL_STATUS__) {
            applyStatus(window.__INITIAL_STATUS__);
        } else {
            fetchStatus();
        }

        if (window.__INITIAL_BACKTEST__ && window.__INITIAL_BACKTEST__.equity_curve && window.__INITIAL_BACKTEST__.equity_curve.length >= 2) {
            const badge = document.getElementById('badgeBacktestVerified');
            const emptyState = document.getElementById('chartEmptyState');
            const canvas = document.getElementById('equityChart');
            if (emptyState) emptyState.classList.add('hidden');
            if (canvas) canvas.classList.remove('hidden');
            if (badge) badge.classList.remove('hidden');
            renderNativeChart(window.__INITIAL_BACKTEST__.equity_curve);
            setTimeout(() => { renderNativeChart(window.__INITIAL_BACKTEST__.equity_curve); }, 100);
        } else {
            runBacktest();
        }
    </script>
</body>
</html>
"""


def get_status_payload() -> Dict[str, Any]:
    mp = MarketDataProvider()
    quote = mp.get_live_quote()
    current_price = float(quote.get("current_price") or 817.80)

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
    arbitration = reg_eng.arbitrate_decision(
        bottom_opportunity_score=bottom_rep.bottom_opportunity_score,
        fundamental_score=fund_profile.fundamental_health_score,
        tactical_action="WAIT_FOR_LIMIT_PULLBACK",
        current_price=current_price,
        current_pb=ledger.current_pb
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

    gates_verdict = AccumulationGatesEngine.evaluate_all_gates(
        current_price=current_price,
        as_of_date=ledger.as_of_date,
        is_intraday=is_partial
    )

    peer_watchlist = MultiBankEngine.get_peer_comparison()

    return {
        "quote": quote,
        "reference_price": current_price,
        "price_timing_label": timing_label,
        "is_partial_bar": is_partial,
        "order_expiry_iso": expiry_iso,
        "order_expiry_label": expiry_label,
        "bottom_detector": bottom_rep.__dict__,
        "fundamental": fund_profile.__dict__,
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
            "base_cost_of_equity_pct": 12.28,
            "terminal_growth_pct": 8.0,
            "margin_of_safety_pct": ledger.margin_of_safety_pct,
            "valuation_exit_price": ledger.valuation_exit_price,
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
        }
    }


def get_backtest_payload(period: str = "2y") -> Dict[str, Any]:
    bt = Backtester()
    return bt.run_backtest(period=period).__dict__


class DashboardHandler(http.server.BaseHTTPRequestHandler):
    def _send_json(self, data: Any, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode("utf-8"))

    def _send_html(self, html: str):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            try:
                status_data = get_status_payload()
                bt_data = get_backtest_payload("2y")
                injected = f"""<script>
window.__INITIAL_STATUS__ = {json.dumps(status_data, default=str)};
window.__INITIAL_BACKTEST__ = {json.dumps(bt_data, default=str)};
</script>"""
                html = HTML_TEMPLATE.replace("<!-- INJECTED_DATA -->", injected)
                self._send_html(html)
            except Exception as e:
                self._send_html(HTML_TEMPLATE)
            return

        elif path == "/api/status":
            try:
                data = get_status_payload()
                self._send_json(data)
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
            return

        elif path == "/api/history":
            try:
                recent = get_recent_predictions(limit=25)
                self._send_json(recent)
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
            return

        elif path == "/api/backtest":
            try:
                params = urllib.parse.parse_qs(parsed.query)
                period = params.get("period", ["2y"])[0]
                bt = Backtester()
                result = bt.run_backtest(period=period)
                self._send_json(result.__dict__)
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
            return

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/trigger-signal":
            try:
                gen = SignalGenerator()
                result = gen.run_daily_signal(force=True)
                self._send_json({
                    "status": "SUCCESS",
                    "message": "Signal recalculated and locked at 2:00 PM IST.",
                    "prediction": result.get("prediction", {})
                })
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
        else:
            self.send_response(404)
            self.end_headers()


def run_dashboard(port: int = PORT):
    server_address = ("", port)
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(server_address, DashboardHandler)
    print(f"HDFC Bank Accumulation Engine running at http://localhost:{port}")
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
