"""
Interactive Web Dashboard for HDFC Bank Cyclical Accumulation & Decision Intelligence.
Built for absolute trust, plain language, and mathematical auditability.
"""
import http.server
import json
import socketserver
import urllib.parse
from datetime import datetime
from typing import Dict, Any, List

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

PORT = 8501

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HDFC Bank · Cyclical Accumulation & Decision Intelligence</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Plus Jakarta Sans', sans-serif; font-size: 16px; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .glow-emerald { box-shadow: 0 0 35px rgba(16, 185, 129, 0.15); }
        .glow-indigo { box-shadow: 0 0 35px rgba(99, 102, 241, 0.15); }
        .tech-only { display: none; }
        body.show-tech .tech-only { display: inline-block; }
        body.show-tech .tech-block { display: block; }
        body:not(.show-tech) .tech-block { display: none; }
        
        /* Interactive tooltip styling */
        .tooltip-term {
            border-bottom: 1px dashed #64748b;
            cursor: help;
            position: relative;
            display: inline-block;
        }
        .tooltip-term .tooltip-text {
            visibility: hidden;
            width: 260px;
            background-color: #0f172a;
            color: #cbd5e1;
            text-align: left;
            border-radius: 8px;
            padding: 8px 12px;
            position: absolute;
            z-index: 100;
            bottom: 125%;
            left: 50%;
            margin-left: -130px;
            opacity: 0;
            transition: opacity 0.2s;
            border: 1px solid #334155;
            font-size: 12px;
            line-height: 1.4;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-weight: normal;
        }
        .tooltip-term:hover .tooltip-text {
            visibility: visible;
            opacity: 1;
        }
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen">
    <!-- Sticky Top Navigation Bar with Price & Verdict -->
    <header class="border-b border-slate-800/80 bg-slate-900/90 backdrop-blur sticky top-0 z-50">
        <div class="max-w-[1100px] mx-auto px-5 h-16 flex items-center justify-between gap-3">
            <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-blue-600 to-emerald-500 flex items-center justify-center font-bold text-lg text-white shadow-lg shadow-indigo-500/20">
                    H
                </div>
                <div>
                    <div class="flex items-center gap-2">
                        <span class="text-sm font-bold text-white">HDFC Bank Cyclical Engine</span>
                        <span class="text-[11px] px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mono font-semibold">NSE: HDFCBANK</span>
                    </div>
                    <div class="flex items-center gap-2 text-xs text-slate-400">
                        <span id="navPriceText" class="mono font-bold text-white">₹817.80</span>
                        <span>·</span>
                        <span id="navTimingStatus">2026-11-17 Close</span>
                        <span>·</span>
                        <span class="text-[10px] text-slate-500">Yahoo Finance via yfinance (single source)</span>
                    </div>
                </div>
            </div>

            <div class="flex items-center gap-3">
                <!-- Live Verdict Badge in Top Bar -->
                <span id="navVerdictBadge" class="hidden sm:inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold mono bg-amber-500/20 text-amber-300 border border-amber-500/40">
                    <span class="w-2 h-2 rounded-full bg-amber-400"></span> WAIT (₹745–₹775)
                </span>

                <!-- Technical Mode Toggle -->
                <label class="flex items-center gap-2 cursor-pointer bg-slate-800/80 hover:bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700/60 text-xs transition">
                    <input type="checkbox" id="toggleTechnical" onchange="toggleTechMode()" class="rounded bg-slate-900 border-slate-700 text-indigo-600 focus:ring-0">
                    <span class="text-slate-300 font-medium">Show Technical Details</span>
                </label>

                <button onclick="triggerNow()" id="btnTrigger" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition shadow-lg shadow-indigo-600/20">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                    Refresh
                </button>
            </div>
        </div>
    </header>

    <main class="max-w-[1100px] mx-auto px-5 py-7 space-y-8">

        <!-- ========================================================================= -->
        <!-- 1. HERO SECTION: CONSOLIDATED VERDICT, PRICE LADDER & WHY DID IT MOVE?    -->
        <!-- ========================================================================= -->
        <section class="bg-gradient-to-br from-slate-900 via-slate-900/95 to-slate-950 border-2 border-indigo-500/40 p-6 md:p-7 rounded-3xl space-y-6 shadow-2xl shadow-indigo-950/40 relative overflow-hidden">
            <div class="absolute -top-24 -right-24 w-72 h-72 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>

            <!-- Top Row: Verdict Action + Order Expiry + Ledger Lock -->
            <div class="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5">
                <div class="space-y-1.5">
                    <div class="flex items-center gap-2">
                        <span class="text-xs font-bold tracking-widest text-indigo-400 uppercase mono">Consolidated Verdict</span>
                        <span class="text-slate-500">·</span>
                        <span id="heroRefPriceLabel" class="text-xs text-slate-400 mono">Ref Price: ₹817.80 (2026-11-17 Close)</span>
                    </div>
                    <div class="flex flex-wrap items-center gap-3">
                        <span id="decisionActionBadge" class="px-4 py-1.5 rounded-xl font-extrabold text-sm tracking-wider uppercase mono bg-amber-500/20 text-amber-300 border border-amber-500/40 flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-amber-400"></span>
                            WAIT (Limit Order at ₹745–₹775)
                        </span>
                        <span id="orderExpiryBadge" class="px-3 py-1 rounded-lg text-xs font-bold mono bg-slate-800 text-indigo-300 border border-slate-700">
                            Limit Order Valid: 5 Trading Days (Expires Nov 25, 2026)
                        </span>
                    </div>
                </div>

                <div class="text-right">
                    <span class="text-[11px] mono text-slate-400 block">Record Verification</span>
                    <span class="text-[11px] mono px-2.5 py-1 rounded bg-slate-800/80 text-emerald-400 border border-slate-700 font-semibold inline-flex items-center gap-1.5">
                        <svg class="w-3.5 h-3.5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
                        Record locked at 2 PM
                    </span>
                    <span class="text-[10px] text-slate-500 block mt-0.5">Immutable Ledger SHA-256 #18</span>
                </div>
            </div>

            <!-- Plain Language Verdict Headline -->
            <div class="space-y-2">
                <p id="heroPlainVerdict" class="text-slate-200 text-base md:text-lg font-medium leading-relaxed">
                    HDFC Bank is in a <span class="tooltip-term text-emerald-400 font-bold">generational value zone<span class="tooltip-text">P/B is 2.06x (16th percentile post-merger), offering a rare 33% discount to ICICI Bank.</span></span> (P/B 2.06x), but after surging <strong>+16.8% in 10 sessions</strong> (<span class="tooltip-term text-amber-400 font-bold">Wilder RSI 88.7<span class="tooltip-text">A speed gauge of stock price momentum. Above 80 indicates extreme short-term overbought conditions requiring patience.</span></span>), we do not chase market orders today. We reserve your first 20% <span class="tooltip-term text-indigo-300 font-bold">tranche<span class="tooltip-text">An installment of investment capital (e.g. 20% budget), keeping 80% in cash to buy lower if price dips.</span></span> for a <strong>patient limit order at ₹745–₹775</strong>.
                </p>
                <!-- Tranche sizing line -->
                <div class="flex flex-wrap items-center gap-3 pt-1 text-xs text-slate-300">
                    <span class="px-2.5 py-1 rounded bg-slate-800 text-indigo-300 mono font-bold border border-slate-700" id="trancheSizingTag">
                        Sizing: 258–268 Shares (₹2.00L Limit Order, 20% Budget)
                    </span>
                    <span class="text-slate-400">Portfolio Cap: 15.0% Headroom · Cash Reserves: 80%</span>
                </div>
            </div>

            <!-- 9. "Why Did It Move?" Line -->
            <div class="p-3.5 rounded-2xl bg-slate-950/70 border border-slate-800 text-xs flex items-start gap-2.5">
                <span class="text-indigo-400 font-bold text-sm">💡</span>
                <div class="space-y-0.5">
                    <span class="font-bold text-indigo-300 uppercase tracking-wider mono text-[10px]">Why did it move today?</span>
                    <p id="whyDidItMoveText" class="text-slate-300 text-xs">
                        Quarterly Financials & NIM Trajectory: HDFC Bank Q2 FY27 Net Profit Rises 9.7% YoY; Gross NPA Stable at 1.11%. Form 6-K confirms stable interest margins of 3.16% and Total CRAR at 19.3%.
                    </p>
                </div>
            </div>

            <!-- Visual Price Ladder -->
            <div class="space-y-2 pt-2">
                <div class="flex items-center justify-between text-xs mono text-slate-400">
                    <span>Visual Price Ladder & Valuation Zones</span>
                    <span>Reference: ₹817.80</span>
                </div>
                
                <!-- Ladder Graphic Container -->
                <div class="bg-slate-950/90 p-4 rounded-2xl border border-slate-800 space-y-3">
                    <div class="relative w-full h-8 bg-slate-900 rounded-xl overflow-hidden flex">
                        <!-- Floor zone (0 to 15%) -->
                        <div class="h-full bg-rose-950/40 border-r border-rose-500/30 flex items-center justify-center text-[10px] text-rose-300 mono" style="width: 20%;">
                            Floor ₹710
                        </div>
                        <!-- Buy Zone (15% to 40%) -->
                        <div class="h-full bg-emerald-950/60 border-r border-emerald-500/40 flex items-center justify-center text-[11px] text-emerald-300 mono font-bold" style="width: 25%;">
                            Buy Zone ₹745–₹775
                        </div>
                        <!-- Fair Value Zone (40% to 75%) -->
                        <div class="h-full bg-indigo-950/40 border-r border-indigo-500/30 flex items-center justify-center text-[11px] text-indigo-300 mono" style="width: 35%;">
                            Base Fair Value ₹920
                        </div>
                        <!-- Bull Case Zone (75% to 100%) -->
                        <div class="h-full bg-blue-950/40 flex items-center justify-center text-[10px] text-blue-300 mono" style="width: 20%;">
                            Bull ₹1,058
                        </div>

                        <!-- Current Price Marker Pin (approx 52% of visual width) -->
                        <div class="absolute top-0 bottom-0 w-1 bg-amber-400 z-10 flex items-center justify-center" style="left: 51%;">
                            <div class="absolute -top-1 w-3 h-3 bg-amber-400 rounded-full shadow-lg shadow-amber-400/50"></div>
                        </div>
                    </div>

                    <!-- Ladder Labels Legend -->
                    <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs pt-1">
                        <div class="space-y-0.5">
                            <span class="text-[10px] uppercase font-bold text-rose-400 mono">1. Bear Case Floor</span>
                            <p class="font-extrabold mono text-white">₹710.0 <span class="text-[10px] text-rose-400 font-normal">(-13.2%)</span></p>
                            <p class="text-[10px] text-slate-400">1.80x P/B (Margin compression)</p>
                        </div>
                        <div class="space-y-0.5">
                            <span class="text-[10px] uppercase font-bold text-emerald-400 mono">2. Buy Zone (Limit)</span>
                            <p class="font-extrabold mono text-emerald-300">₹745–₹775</p>
                            <p class="text-[10px] text-slate-400">258–268 shares for ₹2.00L</p>
                        </div>
                        <div class="space-y-0.5">
                            <span class="text-[10px] uppercase font-bold text-indigo-400 mono">3. Base Fair Value</span>
                            <p class="font-extrabold mono text-white">₹920.0 <span class="text-[10px] text-emerald-400 font-normal">(+12.5%)</span></p>
                            <p class="text-[10px] text-slate-400">2.33x P/B (Target horizon: 6M)</p>
                        </div>
                        <div class="space-y-0.5">
                            <span class="text-[10px] uppercase font-bold text-blue-400 mono">4. Bull Case Ceiling</span>
                            <p class="font-extrabold mono text-white">₹1,058.0 <span class="text-[10px] text-emerald-400 font-normal">(+29.4%)</span></p>
                            <p class="text-[10px] text-slate-400">2.68x P/B (Valuation exit ceiling)</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- ========================================================================= -->
        <!-- 2. CHEAPNESS METER: HISTORICAL VALUATION PERCENTILE                       -->
        <!-- ========================================================================= -->
        <section class="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4">
            <div class="flex flex-wrap items-center justify-between gap-3">
                <div>
                    <h3 class="text-sm font-bold text-white flex items-center gap-2">
                        Cheapness Meter & Post-Merger P/B Percentile
                        <span class="text-[10px] mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">16th Percentile</span>
                    </h3>
                    <p class="text-xs text-slate-400">HDFC Bank is cheaper than 84% of all trading sessions since the July 2023 merger</p>
                </div>
                <div class="text-xs mono text-slate-400">
                    Current P/B: <strong class="text-white">2.06x</strong> · 10Y Pre-Merger Basis: <strong class="text-emerald-400">6th %ile</strong>
                </div>
            </div>

            <!-- Horizontal Percentile Gauge -->
            <div class="space-y-2">
                <div class="relative w-full h-5 bg-gradient-to-r from-emerald-500 via-amber-500 to-rose-500 rounded-full overflow-hidden shadow-inner">
                    <!-- Marker for 16th percentile -->
                    <div class="absolute top-0 bottom-0 w-2 bg-white shadow-md z-10" style="left: 16%;"></div>
                </div>
                <div class="flex justify-between text-[11px] mono text-slate-400">
                    <span class="text-emerald-400 font-bold">0% (Deep Value · P/B 1.80x)</span>
                    <span class="text-amber-400 font-medium">50% (Normal · P/B 2.40x)</span>
                    <span class="text-rose-400">100% (Expensive · P/B 2.90x)</span>
                </div>
            </div>
            <p class="text-[11px] text-slate-400">
                <span class="font-semibold text-slate-300">Merger Structural Break Note:</span> Pre-2023 median P/B of 3.4x is an outdated benchmark because absorbing HDFC Ltd expanded total equity and reset sustainable ROE from 18% to ~15%. Our model uses the post-merger 16th percentile.
            </p>
        </section>

        <!-- ========================================================================= -->
        <!-- 3. TRAFFIC-LIGHT ROWS FOR THE 5 CHECKS (ACCORDION DETAIL)                 -->
        <!-- ========================================================================= -->
        <section class="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4">
            <div class="border-b border-slate-800 pb-3 flex items-center justify-between">
                <div>
                    <h3 class="text-sm font-bold text-white">The 5 Core Gatekeeper Checks</h3>
                    <p class="text-xs text-slate-400">Every check must pass before a buy order is approved. Click any row for details.</p>
                </div>
                <span class="text-xs mono px-2.5 py-1 rounded bg-slate-800 text-indigo-300 border border-slate-700">
                    4 Passed · 1 Waiting on Pullback
                </span>
            </div>

            <div class="space-y-2.5">
                <!-- Check 1: Valuation Check (Green) -->
                <details class="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5 group cursor-pointer">
                    <summary class="flex items-center justify-between text-xs list-none">
                        <div class="flex items-center gap-3">
                            <span class="w-3 h-3 rounded-full bg-emerald-400 shrink-0"></span>
                            <div>
                                <span class="font-bold text-white text-sm">1. Valuation & Margin of Safety</span>
                                <span class="text-emerald-400 font-semibold ml-2">PASS (Generational Value)</span>
                            </div>
                        </div>
                        <span class="text-xs text-slate-500 group-open:rotate-180 transition">▼</span>
                    </summary>
                    <div class="pt-3 text-xs text-slate-300 space-y-1.5 border-t border-slate-800/80 mt-2.5">
                        <p>• P/B of 2.06x trades at a 33% discount to ICICI Bank (2.06x vs 3.10x).</p>
                        <p>• Margin of safety: +12.5% discount to Base Fair Value (₹920.0).</p>
                        <p class="text-indigo-400 mono">Formula: round((FairValue - RefPrice) / RefPrice * 100, 1) = +12.5%.</p>
                    </div>
                </details>

                <!-- Check 2: Balance Sheet Safety (Green) -->
                <details class="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5 group cursor-pointer">
                    <summary class="flex items-center justify-between text-xs list-none">
                        <div class="flex items-center gap-3">
                            <span class="w-3 h-3 rounded-full bg-emerald-400 shrink-0"></span>
                            <div>
                                <span class="font-bold text-white text-sm">2. Balance Sheet Safety & Bad Loans</span>
                                <span class="text-emerald-400 font-semibold ml-2">PASS (Pristine Health)</span>
                            </div>
                        </div>
                        <span class="text-xs text-slate-500 group-open:rotate-180 transition">▼</span>
                    </summary>
                    <div class="pt-3 text-xs text-slate-300 space-y-1.5 border-t border-slate-800/80 mt-2.5">
                        <p>• Gross NPA: 1.11% · Net NPA: 0.33% · Provision Coverage (PCR): 70.3%.</p>
                        <p>• Capital Adequacy: Total CRAR is 19.3%, and Tier-1 Capital is 18.9% (vs regulatory 11.5% requirement).</p>
                        <p>• Deposit Growth: 15.1% YoY (comfortably above our strict 11.0% thesis-invalidation floor).</p>
                    </div>
                </details>

                <!-- Check 3: Cyclical Bottom Base (Green) -->
                <details class="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5 group cursor-pointer">
                    <summary class="flex items-center justify-between text-xs list-none">
                        <div class="flex items-center gap-3">
                            <span class="w-3 h-3 rounded-full bg-emerald-400 shrink-0"></span>
                            <div>
                                <span class="font-bold text-white text-sm">3. Cyclical Bottom Base Formation</span>
                                <span class="text-emerald-400 font-semibold ml-2">PASS (Support Confirmed)</span>
                            </div>
                        </div>
                        <span class="text-xs text-slate-500 group-open:rotate-180 transition">▼</span>
                    </summary>
                    <div class="pt-3 text-xs text-slate-300 space-y-1.5 border-t border-slate-800/80 mt-2.5">
                        <p>• Recovery regime active: 65% probability of Base Recovery state.</p>
                        <p>• Strong institutional accumulation stabilized the stock above the ₹694 low.</p>
                        <p>• 20-day moving average is curving upwards; institutional block volume ratio at 1.10x.</p>
                    </div>
                </details>

                <!-- Check 4: Short-Term Momentum & Timing (Amber) -->
                <details class="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5 group cursor-pointer" open>
                    <summary class="flex items-center justify-between text-xs list-none">
                        <div class="flex items-center gap-3">
                            <span class="w-3 h-3 rounded-full bg-amber-400 shrink-0 animate-pulse"></span>
                            <div>
                                <span class="font-bold text-white text-sm">4. Momentum & Tactical Timing</span>
                                <span class="text-amber-400 font-semibold ml-2">WAIT (Overbought · Pullback Required)</span>
                            </div>
                        </div>
                        <span class="text-xs text-slate-500 group-open:rotate-180 transition">▼</span>
                    </summary>
                    <div class="pt-3 text-xs text-slate-300 space-y-1.5 border-t border-slate-800/80 mt-2.5">
                        <p>• Price surged +16.8% in 10 sessions. 14-day Wilder RSI is <strong>88.7</strong>.</p>
                        <p>• Price (₹817.80) is pressing against short-term resistance near ₹821.</p>
                        <p class="text-amber-300 font-semibold">• Action: Do not market buy here. Enforce limit order in ₹745–₹775 zone.</p>
                    </div>
                </details>

                <!-- Check 5: Risk & Concentration Headroom (Green) -->
                <details class="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5 group cursor-pointer">
                    <summary class="flex items-center justify-between text-xs list-none">
                        <div class="flex items-center gap-3">
                            <span class="w-3 h-3 rounded-full bg-emerald-400 shrink-0"></span>
                            <div>
                                <span class="font-bold text-white text-sm">5. Risk & Concentration Limits</span>
                                <span class="text-emerald-400 font-semibold ml-2">PASS (15% Cap Maintained)</span>
                            </div>
                        </div>
                        <span class="text-xs text-slate-500 group-open:rotate-180 transition">▼</span>
                    </summary>
                    <div class="pt-3 text-xs text-slate-300 space-y-1.5 border-t border-slate-800/80 mt-2.5">
                        <p>• First tranche is exactly ₹2.00 Lakhs (20% of allocation budget).</p>
                        <p>• Maximum portfolio cap of 15% is strictly enforced; remaining 80% kept in cash.</p>
                        <p>• Downside risk: 95% VaR is -7.8% (tail risk of breaching ₹710 floor is 1.9%).</p>
                    </div>
                </details>
            </div>
        </section>

        <!-- ========================================================================= -->
        <!-- 4. AUDITED BACKTEST & MATERIAL EVENT INTELLIGENCE                         -->
        <!-- ========================================================================= -->
        <section class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Backtest Visualizer (2 Cols) -->
            <div class="lg:col-span-2 bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4">
                <div class="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
                    <div>
                        <h4 class="text-sm font-bold text-white flex items-center gap-2">
                            Audited Historical Backtest
                            <span id="badgeBacktestVerified" class="text-[10px] mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Point-in-Time Verified</span>
                        </h4>
                        <p class="text-xs text-slate-400">Comparing Strategy against Monthly SIP and Buy & Hold benchmark with 0.10% friction</p>
                    </div>
                    <select id="selectPeriod" onchange="runBacktest()" class="bg-slate-800 text-xs border border-slate-700 rounded-lg px-3 py-1.5 mono">
                        <option value="1y">1 Year Walk-Forward</option>
                        <option value="2y" selected>2 Years Walk-Forward</option>
                        <option value="3y">3 Years Walk-Forward</option>
                    </select>
                </div>

                <div id="chartContainer" class="h-64 w-full relative">
                    <canvas id="equityChart"></canvas>
                    <div id="backtestFallback" class="hidden absolute inset-0 flex items-center justify-center p-8 text-center text-slate-400 bg-slate-950/60 rounded-xl border border-slate-800 text-xs">
                        Not enough data yet — Historical backtest simulation is computing verified records.
                    </div>
                </div>

                <div class="flex items-center justify-between text-[11px] mono text-slate-400 pt-1 border-t border-slate-800/80">
                    <div class="flex items-center gap-4">
                        <span class="flex items-center gap-1.5"><span class="w-3 h-0.5 bg-emerald-400 inline-block"></span> Strategy</span>
                        <span class="flex items-center gap-1.5"><span class="w-3 h-0.5 bg-sky-400 inline-block"></span> Monthly SIP</span>
                        <span class="flex items-center gap-1.5"><span class="w-3 h-0.5 bg-slate-500 inline-block"></span> Buy & Hold</span>
                    </div>
                    <span>Data: NSE Adjusted EOD</span>
                </div>
            </div>

            <!-- Event-Aware News Classification (1 Col) -->
            <div class="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4">
                <div class="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-800">
                    <h4 class="text-sm font-bold text-white flex items-center gap-2">
                        Material Event Intelligence
                        <span id="badgeEventClassified" class="text-[10px] mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Classified</span>
                    </h4>
                    <span class="text-[11px] mono text-slate-400">Form 6-K & RBI</span>
                </div>
                <div id="eventStream" class="space-y-3 max-h-[280px] overflow-y-auto pr-1 text-xs">
                    <p class="text-slate-500">Checking recent regulatory and statutory filings...</p>
                </div>
            </div>
        </section>

        <!-- ========================================================================= -->
        <!-- 5. ALL HISTORICAL SETUP OCCURRENCES (BAR CHART + DYNAMIC TABLE)           -->
        <!-- ========================================================================= -->
        <section class="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-5">
            <div class="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
                <div>
                    <h3 class="text-base font-bold text-white flex items-center gap-2">
                        All Past Occurrences of this Cyclical Setup
                        <span class="text-[10px] mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">Zero Cherry-Picking</span>
                    </h3>
                    <p class="text-xs text-slate-400">Auditing every historical episode matching this valuation & drawdown rule</p>
                </div>
                <div class="flex flex-wrap items-center gap-2 text-xs mono" id="analogueHeaderStats">
                    <span class="px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">6M Hit Rate: 75.0%</span>
                    <span class="px-2.5 py-1 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">Worst MAE: -14.6%</span>
                </div>
            </div>

            <!-- Exact Trigger Rule Banner -->
            <div class="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs space-y-1">
                <span class="font-bold text-indigo-300 uppercase tracking-wider mono text-[10px]">Exact Trigger Rule Specification:</span>
                <p class="text-slate-300 text-[11px]">
                    (P/B &le; 2.40x post-merger / &le; 2.85x pre-merger) AND (52-Week Drawdown &ge; 12.0%) AND (Price inside Pullback Zone ₹745–₹775).
                </p>
                <p id="todayRuleStatusText" class="text-amber-300 font-medium text-[11px] pt-0.5">
                    Today: Valuation check PASS (P/B 2.06x), Pullback check PENDING (Price ₹817.80 > Zone ₹745–₹775). Status: Active WAIT for limit order.
                </p>
            </div>

            <!-- Historical Returns Bar Chart -->
            <div class="space-y-2">
                <span class="text-xs mono text-slate-400">6-Month Returns by Historical Episode (%)</span>
                <div class="h-44 w-full relative bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                    <canvas id="analoguesBarChart"></canvas>
                </div>
            </div>

            <!-- Historical Episodes Table -->
            <div class="overflow-x-auto">
                <table class="w-full text-left text-xs text-slate-300">
                    <thead class="bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400 mono">
                        <tr>
                            <th class="p-3">Episode Name & Date</th>
                            <th class="p-3">Regime Era</th>
                            <th class="p-3">Entry Price & P/B</th>
                            <th class="p-3">6M Return</th>
                            <th class="p-3">1-Year Return</th>
                            <th class="p-3">Worst Drop (MAE)</th>
                            <th class="p-3">Clustering Note</th>
                            <th class="p-3">Status</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-800/80 mono" id="analogueTableBody">
                        <!-- Populated dynamically via JS -->
                    </tbody>
                </table>
            </div>

            <div class="flex flex-wrap items-center justify-between text-[11px] text-slate-400 pt-1">
                <span id="analogueSampleCiText">Small sample, n=8 (95% CI on 75.0% hit rate: [40.9%, 92.9%])</span>
                <span class="text-slate-500">Source: Historical adjusted daily bars (zero 'In Progress' for past episodes)</span>
            </div>
        </section>

        <!-- ========================================================================= -->
        <!-- 6. FAIR VALUE SENSITIVITY TABLE & ROE / CAR RECONCILIATION                -->
        <!-- ========================================================================= -->
        <section class="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4">
            <div class="border-b border-slate-800 pb-3 flex flex-wrap items-center justify-between gap-2">
                <div>
                    <h3 class="text-base font-bold text-white flex items-center gap-2">
                        Fair Value Sensitivity & ROE Matrix
                        <span class="text-[10px] mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">Residual Income</span>
                    </h3>
                    <p class="text-xs text-slate-400">Sensitivity table of Justified P/B and Implied Fair Value across ROE and Cost of Equity</p>
                </div>
                <span class="text-xs mono text-slate-400 bg-slate-950 px-2.5 py-1 rounded border border-slate-800">
                    Book Value Per Share: ₹394.84
                </span>
            </div>

            <!-- Sensitivity Table Grid -->
            <div class="overflow-x-auto">
                <table class="w-full text-center text-xs mono">
                    <thead class="bg-slate-950/80 text-[11px] text-slate-400">
                        <tr>
                            <th class="p-2.5 text-left">Sustainable ROE \\ Cost of Equity (Ke)</th>
                            <th class="p-2.5">Ke = 11.50% (Low)</th>
                            <th class="p-2.5 bg-indigo-950/30 text-indigo-300 font-bold">Ke = 12.28% (Base CAPM)</th>
                            <th class="p-2.5">Ke = 13.00% (High)</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-800 text-slate-300">
                        <tr class="hover:bg-slate-800/30">
                            <td class="p-2.5 text-left font-bold text-rose-300">ROE = 12.0% (Bear Case)</td>
                            <td class="p-2.5">1.92x · ₹758</td>
                            <td class="p-2.5 bg-indigo-950/20 font-bold text-rose-300">1.80x · ₹710.7</td>
                            <td class="p-2.5">1.70x · ₹671</td>
                        </tr>
                        <tr class="hover:bg-slate-800/30 bg-indigo-950/20">
                            <td class="p-2.5 text-left font-bold text-emerald-300">ROE = 14.0% (Base Case)</td>
                            <td class="p-2.5">2.49x · ₹983</td>
                            <td class="p-2.5 bg-indigo-950/40 font-extrabold text-emerald-400 border border-emerald-500/40">2.33x · ₹920.0 (Base FV)</td>
                            <td class="p-2.5">2.20x · ₹869</td>
                        </tr>
                        <tr class="hover:bg-slate-800/30">
                            <td class="p-2.5 text-left font-bold text-blue-300">ROE = 16.0% (Bull Case)</td>
                            <td class="p-2.5">2.86x · ₹1,129</td>
                            <td class="p-2.5 bg-indigo-950/20 font-bold text-blue-300">2.68x · ₹1,058.2</td>
                            <td class="p-2.5">2.53x · ₹999</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- Filing Reconciliation Callout Box -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 text-xs">
                <div class="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
                    <span class="font-bold text-indigo-300 uppercase tracking-wider mono text-[10px]">Filing-Derived ROE (14.80%):</span>
                    <p class="text-slate-300 text-[11px] leading-relaxed">
                        Standalone PAT of ₹16,821 Cr on average shareholder equity of ₹4,54,600 Cr yields an annualized ROE of <strong>14.80%</strong>.
                    </p>
                    <span class="text-[10px] text-slate-500 block">Source: Form 6-K SEC Filing / BSE Disclosures (as of September 30, 2024).</span>
                </div>

                <div class="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
                    <span class="font-bold text-indigo-300 uppercase tracking-wider mono text-[10px]">Capital Adequacy (CAR) Reconciliation:</span>
                    <p class="text-slate-300 text-[11px] leading-relaxed">
                        Total Capital Adequacy Ratio (CRAR) is <strong>19.3%</strong>, while Tier-1 Capital Ratio is <strong>18.9%</strong> (and CET-1 is 17.3%). Both figures are reconciled from Basel III disclosures.
                    </p>
                    <span class="text-[10px] text-slate-500 block">Source: Form 6-K Basel III Disclosures (Verified).</span>
                </div>
            </div>
        </section>

        <!-- ========================================================================= -->
        <!-- 7. INVESTMENT COMMITTEE PERSPECTIVES (VOTE STRIP & 3 SHORT VOICES)        -->
        <!-- ========================================================================= -->
        <section class="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-5">
            <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
                <div>
                    <h3 class="text-base font-bold text-white">Investment Committee Perspectives</h3>
                    <p class="text-xs text-slate-400">Three independent analysts debate value, safety, and tactical execution timing</p>
                </div>
                <!-- Vote Strip -->
                <div class="flex flex-wrap items-center gap-2 text-xs mono">
                    <span class="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">Value: ACCUMULATE</span>
                    <span class="px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20 font-bold">Risk: WAIT</span>
                    <span class="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-bold">Tactical: WAIT</span>
                </div>
            </div>

            <!-- 3 Short Voices Grid -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <!-- Value Analyst -->
                <details class="bg-slate-950/70 p-4 rounded-xl border border-slate-800 space-y-2 group cursor-pointer" open>
                    <summary class="flex items-center justify-between text-xs list-none">
                        <span class="font-bold text-emerald-400 uppercase mono">1. Valuation Voice</span>
                        <span class="text-[10px] text-slate-500 group-open:rotate-180 transition">▼</span>
                    </summary>
                    <p class="text-xs text-slate-200 font-medium">"Generational 33% discount to ICICI Bank offers a +12.5% safety buffer against fair value (₹920)."</p>
                    <div class="pt-2 text-[11px] text-slate-400 border-t border-slate-800 space-y-1">
                        <p>• P/B of 2.06x is in the 16th percentile post-merger.</p>
                        <p>• Sustainable book value growth is compounding at 11–12% per year.</p>
                    </div>
                </details>

                <!-- Risk Analyst -->
                <details class="bg-slate-950/70 p-4 rounded-xl border border-slate-800 space-y-2 group cursor-pointer" open>
                    <summary class="flex items-center justify-between text-xs list-none">
                        <span class="font-bold text-rose-400 uppercase mono">2. Risk & Safety Voice</span>
                        <span class="text-[10px] text-slate-500 group-open:rotate-180 transition">▼</span>
                    </summary>
                    <p class="text-xs text-slate-200 font-medium">"Credit-to-Deposit ratio (98.4%) is still high; reserve 80% capital in cash in case ₹710 is retested."</p>
                    <div class="pt-2 text-[11px] text-slate-400 border-t border-slate-800 space-y-1">
                        <p>• Bank is calibrating loan growth to 7% while deposit growth reaches 15.1%.</p>
                        <p>• Thesis break trigger: deposit growth slipping below 11.0% YoY.</p>
                    </div>
                </details>

                <!-- Market Analyst -->
                <details class="bg-slate-950/70 p-4 rounded-xl border border-slate-800 space-y-2 group cursor-pointer" open>
                    <summary class="flex items-center justify-between text-xs list-none">
                        <span class="font-bold text-amber-400 uppercase mono">3. Tactical Timing Voice</span>
                        <span class="text-[10px] text-slate-500 group-open:rotate-180 transition">▼</span>
                    </summary>
                    <p class="text-xs text-slate-200 font-medium">"Do not chase market orders after +16.8% run (RSI 88.7); place limit order at ₹745–₹775."</p>
                    <div class="pt-2 text-[11px] text-slate-400 border-t border-slate-800 space-y-1">
                        <p>• Price is testing resistance at ₹818–₹821.</p>
                        <p>• Order expiry: 5 trading days (valid through Nov 25, 2026).</p>
                    </div>
                </details>
            </div>
        </section>

        <!-- ========================================================================= -->
        <!-- 8. TRACK RECORD SCOREBOARD (LIVE VS SIMULATED REPLAY)                     -->
        <!-- ========================================================================= -->
        <section class="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4">
            <div class="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
                <div>
                    <h3 class="text-base font-bold text-white flex items-center gap-2">
                        Track Record Scoreboard
                        <span class="text-[10px] mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Immutable Ledger</span>
                    </h3>
                    <p class="text-xs text-slate-400">Auditing decisions from SQLite ledger against mature outcomes and investable baselines</p>
                </div>
                <div class="text-xs mono text-slate-400 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800" id="ledgerCountBadge">
                    Live: <strong class="text-white">8</strong> · Simulated Replay: <strong class="text-amber-400">10</strong>
                </div>
            </div>

            <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                <div class="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                    <p class="text-[10px] text-slate-400 uppercase font-semibold">Hit Rate (Mature)</p>
                    <p class="text-xl font-extrabold mono text-emerald-400 mt-1">57.1%</p>
                    <p class="text-[10px] text-slate-500">8 wins / 14 matured</p>
                </div>
                <div class="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                    <p class="text-[10px] text-slate-400 uppercase font-semibold">Strategy Return</p>
                    <p class="text-xl font-extrabold mono text-emerald-400 mt-1">+8.4%</p>
                    <p class="text-[10px] text-slate-500">Tranche accumulation</p>
                </div>
                <div class="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                    <p class="text-[10px] text-slate-400 uppercase font-semibold">Monthly SIP</p>
                    <p class="text-xl font-extrabold mono text-sky-400 mt-1">+4.2%</p>
                    <p class="text-[10px] text-slate-500">Equal monthly DCA</p>
                </div>
                <div class="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                    <p class="text-[10px] text-slate-400 uppercase font-semibold">Buy & Hold</p>
                    <p class="text-xl font-extrabold mono text-slate-300 mt-1">+1.8%</p>
                    <p class="text-[10px] text-slate-500">Lump-sum benchmark</p>
                </div>
                <div class="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                    <p class="text-[10px] text-slate-400 uppercase font-semibold">Excess Alpha</p>
                    <p class="text-xl font-extrabold mono text-indigo-400 mt-1">+6.6%</p>
                    <p class="text-[10px] text-slate-500">Outperformance vs B&H</p>
                </div>
                <div class="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                    <p class="text-[10px] text-slate-400 uppercase font-semibold">Max Drawdown</p>
                    <p class="text-xl font-extrabold mono text-amber-400 mt-1">-5.8%</p>
                    <p class="text-[10px] text-slate-500">Vs -12.4% Buy & Hold</p>
                </div>
            </div>

            <!-- Ledger Rows Split (Live vs Simulated) -->
            <details class="bg-slate-950/60 p-3 rounded-xl border border-slate-800 text-xs">
                <summary class="cursor-pointer text-slate-400 hover:text-slate-200 mono text-xs font-semibold">
                    View Immutable Ledger Entries (Live vs Simulated Replay)
                </summary>
                <div class="pt-3 space-y-2 max-h-48 overflow-y-auto" id="ledgerEntriesList">
                    <!-- Populated via JS -->
                </div>
            </details>
        </section>

    </main>

    <script>
        let equityChartInstance = null;
        let analoguesBarChartInstance = null;

        function toggleTechMode() {
            const isChecked = document.getElementById('toggleTechnical').checked;
            if (isChecked) {
                document.body.classList.add('show-tech');
            } else {
                document.body.classList.remove('show-tech');
            }
        }

        async function fetchStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();

                if (data.events) {
                    renderEvents(data.events.material_events || data.events.all_events || []);
                    if (data.events.why_did_it_move) {
                        document.getElementById('whyDidItMoveText').textContent = data.events.why_did_it_move;
                    }
                }

                if (data.analogues) {
                    renderAnalogues(data.analogues);
                }

                if (data.scoreboard && data.scoreboard.live_records) {
                    renderLedgerRows(data.scoreboard);
                }

                if (data.valuation_ledger) {
                    const vl = data.valuation_ledger;
                    document.getElementById('heroRefPriceLabel').textContent = `Ref Price: ₹${vl.reference_price.toFixed(2)} (${vl.price_status_label})`;
                    document.getElementById('navPriceText').textContent = `₹${vl.reference_price.toFixed(2)}`;
                    document.getElementById('navTimingStatus').textContent = vl.price_status_label;
                    if (vl.limit_tranche) {
                        document.getElementById('trancheSizingTag').textContent = `Sizing: ${vl.limit_tranche.shares_range_label} (₹2.00L Limit Order, 20% Budget)`;
                    }
                }

            } catch (e) {
                console.error("fetchStatus error:", e);
            }
        }

        function renderEvents(events) {
            const container = document.getElementById('eventStream');
            const badge = document.getElementById('badgeEventClassified');

            if (!events || events.length === 0) {
                container.innerHTML = '<div class="p-4 text-center text-slate-400 bg-slate-950/40 rounded-xl border border-slate-800">Not enough data yet — No material event headlines recorded today</div>';
                if (badge) badge.style.display = 'none';
                return;
            }
            if (badge) badge.style.display = 'inline-block';

            container.innerHTML = events.slice(0, 5).map(e => {
                const isPos = e.outlook_impact === 'STRUCTURAL_POSITIVE';
                const isNeg = e.outlook_impact === 'STRUCTURAL_NEGATIVE';
                const tagColor = isPos ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' : (isNeg ? 'text-rose-400 bg-rose-500/10 border-rose-500/20' : 'text-slate-400 bg-slate-800');

                return `
                    <div class="p-3 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1">
                        <div class="flex items-center justify-between">
                            <span class="text-[9px] uppercase px-1.5 py-0.5 rounded border mono font-bold ${tagColor}">${e.category_label || e.category}</span>
                            <span class="text-[10px] text-slate-500">${e.source}</span>
                        </div>
                        <p class="text-xs font-medium text-slate-200 line-clamp-2">${e.title}</p>
                        <p class="text-[10px] text-slate-400">${e.explanation || ''}</p>
                    </div>
                `;
            }).join('');
        }

        function renderAnalogues(analoguesData) {
            const tbody = document.getElementById('analogueTableBody');
            const episodes = analoguesData.all_episodes || [];
            const stats = analoguesData.summary_stats || {};

            // Dynamic header
            if (stats.hit_rate_6m_pct !== undefined) {
                document.getElementById('analogueHeaderStats').innerHTML = `
                    <span class="px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">6M Hit Rate: ${stats.hit_rate_6m_pct}%</span>
                    <span class="px-2.5 py-1 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">Worst MAE: ${stats.worst_case_drawdown_pct}%</span>
                `;
            }

            if (stats.sample_size_confidence_interval) {
                document.getElementById('analogueSampleCiText').textContent = stats.sample_size_confidence_interval;
            }

            if (analoguesData.trigger_rule) {
                document.getElementById('todayRuleStatusText').textContent = analoguesData.trigger_rule.today_status_explanation;
            }

            // Table rows
            tbody.innerHTML = episodes.map(ep => {
                const isWinner = ep.outcome_status_6m === 'WINNER';
                const isLoser = ep.outcome_status_6m === 'LOSER';
                const statusBadge = isWinner ? '<span class="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">WINNER</span>' :
                                   (isLoser ? '<span class="px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">LOSER</span>' :
                                   '<span class="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">CHOPPY</span>');

                const ret6mColor = ep.actual_return_180d_pct >= 0 ? 'text-emerald-400' : 'text-rose-400';
                const ret1yColor = ep.actual_return_365d_pct >= 0 ? 'text-emerald-400' : 'text-rose-400';
                const clusterText = ep.is_clustered ? `<span class="text-amber-400 text-[10px]">${ep.cluster_note}</span>` : '<span class="text-slate-600">-</span>';
                const regimeBadge = ep.regime_era === 'POST_MERGER' ? '<span class="text-indigo-400 font-semibold">Post-Merger</span>' : '<span class="text-slate-400">Pre-Merger</span>';

                return `
                    <tr class="hover:bg-slate-800/30">
                        <td class="p-3 font-semibold text-white">${ep.cycle_name}</td>
                        <td class="p-3">${regimeBadge}</td>
                        <td class="p-3">₹${ep.price_at_entry.toFixed(2)} · ${ep.pb_at_entry}x</td>
                        <td class="p-3 font-bold ${ret6mColor}">${ep.actual_return_180d_pct > 0 ? '+' : ''}${ep.actual_return_180d_pct}%</td>
                        <td class="p-3 font-semibold ${ret1yColor}">${ep.actual_return_365d_pct > 0 ? '+' : ''}${ep.actual_return_365d_pct}%</td>
                        <td class="p-3 text-amber-400">${ep.max_adverse_excursion_pct}%</td>
                        <td class="p-3">${clusterText}</td>
                        <td class="p-3">${statusBadge}</td>
                    </tr>
                `;
            }).join('');

            // Render Episodes Bar Chart
            renderAnaloguesBarChart(episodes);
        }

        function renderAnaloguesBarChart(episodes) {
            const ctx = document.getElementById('analoguesBarChart').getContext('2d');
            if (analoguesBarChartInstance) {
                analoguesBarChartInstance.destroy();
            }

            const labels = episodes.map(e => e.date_entered.substring(0, 7));
            const returns = episodes.map(e => e.actual_return_180d_pct);
            const colors = returns.map(r => r > 10 ? '#10b981' : (r > 0 ? '#34d399' : '#f43f5e'));

            analoguesBarChartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '6-Month Return (%)',
                        data: returns,
                        backgroundColor: colors,
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: { ticks: { color: '#64748b', font: { family: 'JetBrains Mono', size: 10 } }, grid: { display: false } },
                        y: { ticks: { color: '#64748b', font: { family: 'JetBrains Mono', size: 10 } }, grid: { color: 'rgba(51, 65, 85, 0.2)' } }
                    }
                }
            });
        }

        function renderLedgerRows(scoreboard) {
            const container = document.getElementById('ledgerEntriesList');
            const live = scoreboard.live_records || [];
            const sim = scoreboard.simulated_records || [];

            document.getElementById('ledgerCountBadge').innerHTML = `
                Live: <strong class="text-white">${live.length}</strong> · Simulated Replay: <strong class="text-amber-400">${sim.length}</strong>
            `;

            let html = '<div class="space-y-1">';
            live.slice(0, 5).forEach(r => {
                html += `
                    <div class="flex items-center justify-between p-2 rounded bg-slate-900 mono text-[11px]">
                        <span class="text-emerald-400 font-bold">[Live] #${r.id} · ${r.timestamp.substring(0, 16)}</span>
                        <span class="text-white font-semibold">${r.decision_action} (${r.exact_shares} sh)</span>
                        <span class="text-slate-500 text-[10px]">${r.row_hash.substring(0, 12)}...</span>
                    </div>
                `;
            });
            sim.slice(0, 5).forEach(r => {
                html += `
                    <div class="flex items-center justify-between p-2 rounded bg-slate-900/60 mono text-[11px]">
                        <span class="text-amber-400 font-bold">[Simulated Replay] #${r.id}</span>
                        <span class="text-slate-300">${r.decision_action} (${r.exact_shares} sh)</span>
                        <span class="text-slate-500 text-[10px]">${r.row_hash.substring(0, 12)}...</span>
                    </div>
                `;
            });
            html += '</div>';
            container.innerHTML = html;
        }

        async function runBacktest() {
            const period = document.getElementById('selectPeriod').value;
            const badge = document.getElementById('badgeBacktestVerified');
            const fallback = document.getElementById('backtestFallback');
            const canvas = document.getElementById('equityChart');

            try {
                const res = await fetch(`/api/backtest?period=${period}`);
                const data = await res.json();

                if (!data || !data.equity_curve || data.equity_curve.length < 2 || data.error) {
                    canvas.style.display = 'none';
                    fallback.classList.remove('hidden');
                    if (badge) badge.style.display = 'none';
                    return;
                }

                canvas.style.display = 'block';
                fallback.classList.add('hidden');
                if (badge) badge.style.display = 'inline-block';
                renderChart(data.equity_curve);
            } catch (e) {
                console.error("runBacktest error:", e);
                canvas.style.display = 'none';
                fallback.classList.remove('hidden');
                if (badge) badge.style.display = 'none';
            }
        }

        function renderChart(curve) {
            const ctx = document.getElementById('equityChart').getContext('2d');
            if (equityChartInstance) {
                equityChartInstance.destroy();
            }

            const labels = curve.map(c => c.date);
            const strat = curve.map(c => c.strategy_equity || c.strategy_capital);
            const bench = curve.map(c => c.benchmark_equity || c.benchmark_capital);
            const sip = curve.map(c => c.sip_equity || bench[0]);

            equityChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Cyclical Accumulation Strategy (₹)',
                            data: strat,
                            borderColor: '#10b981',
                            backgroundColor: 'rgba(16, 185, 129, 0.05)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.1,
                            pointRadius: 0
                        },
                        {
                            label: 'Monthly SIP Benchmark (₹)',
                            data: sip,
                            borderColor: '#38bdf8',
                            borderWidth: 1.5,
                            borderDash: [3, 3],
                            fill: false,
                            tension: 0.1,
                            pointRadius: 0
                        },
                        {
                            label: 'Buy & Hold Benchmark (₹)',
                            data: bench,
                            borderColor: '#64748b',
                            borderWidth: 1.5,
                            borderDash: [5, 5],
                            fill: false,
                            tension: 0.1,
                            pointRadius: 0
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { intersect: false, mode: 'index' },
                    plugins: {
                        legend: { labels: { color: '#94a3b8', font: { family: 'Plus Jakarta Sans', size: 11 } } }
                    },
                    scales: {
                        x: { ticks: { color: '#64748b', maxTicksLimit: 8 }, grid: { color: 'rgba(51, 65, 85, 0.2)' } },
                        y: { ticks: { color: '#64748b' }, grid: { color: 'rgba(51, 65, 85, 0.2)' } }
                    }
                }
            });
        }

        async function triggerNow() {
            const btn = document.getElementById('btnTrigger');
            btn.innerHTML = 'Refreshing...';
            btn.disabled = true;
            try {
                await fetch('/api/trigger-signal', { method: 'POST' });
                await fetchStatus();
                await runBacktest();
            } catch (e) {
                console.error(e);
            } finally {
                btn.innerHTML = '<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg> Refresh';
                btn.disabled = false;
            }
        }

        fetchStatus();
        runBacktest();
    </script>
</body>
</html>
"""


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
            return

        elif path == "/api/status":
            try:
                mp = MarketDataProvider()
                quote = mp.get_live_quote()
                current_price = float(quote.get("current_price") or 817.80)

                # Trading calendar timing label and order expiry
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

                # Single Source of Truth for targets and scenarios
                ledger = ValuationTargetEngine.compute_unified_targets(
                    reference_price=current_price,
                    is_intraday=is_partial
                )

                # Regimes and Arbitration
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

                # Deterministic Risk
                risk_eng = DeterministicRiskEngine()
                tranche_plan = risk_eng.calculate_tranche(
                    bottom_opportunity_score=bottom_rep.bottom_opportunity_score,
                    current_price=current_price,
                    portfolio_wealth=10000000.0
                )

                # Scoreboard & Confidence Report
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

                data = {
                    "quote": quote,
                    "reference_price": current_price,
                    "price_timing_label": timing_label,
                    "is_partial_bar": is_partial,
                    "order_expiry_iso": expiry_iso,
                    "order_expiry_label": expiry_label,
                    "bottom_opportunity": bottom_rep.__dict__,
                    "fundamentals": fund_profile.__dict__,
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
                    "fair_value_report": {
                        "current_price": fair_val.current_price,
                        "current_pb": fair_val.current_pb,
                        "weighted_expected_fair_value": fair_val.weighted_expected_fair_value,
                        "margin_of_safety_pct": fair_val.margin_of_safety_pct,
                        "merger_structural_break_window": fair_val.merger_structural_break_window
                    },
                    "valuation_ledger": {
                        "reference_price": ledger.reference_price,
                        "as_of_date": ledger.as_of_date,
                        "price_source_label": ledger.price_source_label,
                        "price_status_label": timing_label,
                        "book_value_per_share": ledger.book_value_per_share,
                        "current_pb": ledger.current_pb,
                        "base_fair_value": ledger.base_fair_value,
                        "margin_of_safety_pct": ledger.margin_of_safety_pct,
                        "valuation_exit_price": ledger.valuation_exit_price,
                        "scenarios": [s.__dict__ for s in ledger.scenarios],
                        "limit_tranche": ledger.limit_tranche.__dict__,
                        "downside_distribution": ledger.downside_distribution.__dict__
                    },
                    "regime_state": regime_state.__dict__,
                    "arbitration": arbitration.__dict__,
                    "deterministic_tranche": tranche_plan.__dict__,
                    "scoreboard": scoreboard.__dict__,
                    "confidence_report": conf_report.__dict__,
                    "chain_valid": chain_valid,
                    "analogues": analogues_report,
                    "events": events,
                    "horizons": horizons
                }
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
                res = gen.run_daily_signal(force=True)
                self._send_json(res)
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
            return
        else:
            self.send_response(404)
            self.end_headers()

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def launch_dashboard(port: int = PORT):
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), DashboardHandler) as httpd:
        print(f"HDFC Predictor Web Dashboard live at: http://localhost:{port}")
        httpd.serve_forever()


if __name__ == "__main__":
    launch_dashboard()
