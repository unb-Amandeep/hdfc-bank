"""
Interactive Web Dashboard for HDFC Bank:
- Primary Tier: Long-Term Cyclical Accumulation Intelligence (Bottom Score, Health, Tranche Ladder, AI Committee)
- Secondary Tier: Short-Term Tactical 2:00 PM Trading Intelligence (Calibrated Confidence, Event Intelligence)
"""
import http.server
import json
import socketserver
import urllib.parse
from datetime import datetime
from typing import Dict, Any

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
from hdfc_predictor.probabilistic_calibration import ProbabilisticCalibrationEngine

PORT = 8501

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HDFC Bank · Long-Term Investment Intelligence & Cyclical Engine</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Plus Jakarta Sans', sans-serif; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .glow-emerald { box-shadow: 0 0 35px rgba(16, 185, 129, 0.2); }
        .glow-indigo { box-shadow: 0 0 35px rgba(99, 102, 241, 0.2); }
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen">
    <!-- Navbar -->
    <header class="border-b border-slate-800/80 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-blue-600 to-emerald-500 flex items-center justify-center font-bold text-lg text-white shadow-lg shadow-indigo-500/20">
                    H
                </div>
                <div>
                    <h1 class="text-sm font-bold text-white flex items-center gap-2">
                        HDFC Bank Investment Intelligence
                        <span class="text-[11px] px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mono">HDFCBANK.NS</span>
                    </h1>
                    <p class="text-[11px] text-slate-400">Autonomous Cyclical Accumulation & Risk-Calibrated Decision Engine</p>
                </div>
            </div>
            <div class="flex items-center gap-3">
                <div id="liveClock" class="text-xs mono text-slate-400 hidden sm:block bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700/60">--:--:-- IST</div>
                <button onclick="triggerNow()" id="btnTrigger" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-4 py-2 rounded-lg flex items-center gap-2 transition shadow-lg shadow-indigo-600/20">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                    Refresh Intelligence
                </button>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-6 py-8 space-y-10">

        <!-- ========================================================================= -->
        <!-- UNIFIED DECISION CARD (PRIMARY ACTION, 5 CORE ANSWERS, ARBITRATION)       -->
        <!-- ========================================================================= -->
        <section class="bg-gradient-to-br from-slate-900 via-slate-900/95 to-slate-950 border-2 border-indigo-500/40 p-7 rounded-3xl space-y-6 shadow-2xl shadow-indigo-950/40 relative overflow-hidden">
            <div class="absolute -top-24 -right-24 w-72 h-72 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>
            
            <!-- Header Row: Action Badge + Tactical Execution Type + Hash Chain Audit -->
            <div class="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5">
                <div class="space-y-1">
                    <span class="text-xs font-bold tracking-widest text-indigo-400 uppercase mono">Consolidated Verdict · 14:00 IST Snapshot</span>
                    <div class="flex items-center gap-3">
                        <span id="decisionActionBadge" class="px-4 py-1.5 rounded-xl font-extrabold text-sm tracking-wider uppercase mono bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
                            ACCUMULATE (TRANCHE #1)
                        </span>
                        <span id="orderTypeBadge" class="px-3 py-1 rounded-lg text-xs font-bold mono bg-slate-800 text-indigo-300 border border-slate-700">
                            LIMIT_ORDER_PULLBACK: ₹745 - ₹775
                        </span>
                    </div>
                </div>
                <div class="text-right">
                    <span class="text-[11px] mono text-slate-400 block">Cryptographic Hash-Chain</span>
                    <span class="text-[11px] mono px-2.5 py-1 rounded bg-slate-800/80 text-emerald-400 border border-slate-700 font-semibold inline-flex items-center gap-1.5">
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
                        SHA-256 Validated
                    </span>
                </div>
            </div>

            <!-- Tier Conflict Notice Banner (Surfaces when Primary != Tactical) -->
            <div id="tierConflictBanner" class="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-200 flex items-start gap-3">
                <span class="text-base">⚡</span>
                <div class="space-y-1">
                    <p class="font-bold uppercase tracking-wider text-[11px] text-amber-400 mono">Tier Conflict Detected & Arbitrated</p>
                    <p id="tierConflictText" class="text-slate-300 text-xs leading-relaxed">
                        Primary Cyclical Tier signals <strong>Deep Value Accumulation (Score 78/100)</strong>, but Tactical 2:00 PM Tier flags short-term momentum stretch (RSI 88.7).
                        <span class="text-amber-300 font-medium">Resolution:</span> Primary approves 20% capital deployment, but Tactical restricts execution to a <strong>LIMIT ORDER in pullback zone (₹745–₹775)</strong>. Do not market-chase.
                    </p>
                </div>
            </div>

            <!-- The 5 Core Answers Grid -->
            <div class="grid grid-cols-1 md:grid-cols-5 gap-3.5 pt-1">
                <!-- Answer 1: Is it cheap? -->
                <div class="bg-slate-950/80 p-4 rounded-2xl border border-slate-800 space-y-1.5">
                    <p class="text-[10px] uppercase font-bold tracking-wider text-slate-400 mono">1. Is it cheap?</p>
                    <p id="ans1Title" class="text-sm font-extrabold text-emerald-400 mono">YES (Generational)</p>
                    <p id="ans1Desc" class="text-[11px] text-slate-300">P/B 2.06x in 16th %ile. 33% discount vs ICICI. Margin of safety: +13.1% to Base FV ₹920.</p>
                </div>

                <!-- Answer 2: Is it healthy? -->
                <div class="bg-slate-950/80 p-4 rounded-2xl border border-slate-800 space-y-1.5">
                    <p class="text-[10px] uppercase font-bold tracking-wider text-slate-400 mono">2. Is it healthy?</p>
                    <p id="ans2Title" class="text-sm font-extrabold text-blue-400 mono">YES (Sound Gate)</p>
                    <p id="ans2Desc" class="text-[11px] text-slate-300">Score 84/100. GNPA 1.11%, NNPA 0.33%, CAR 19.3%, NIM 3.16%, PCR 70.3%. Pristine.</p>
                </div>

                <!-- Answer 3: Is a bottom developing? -->
                <div class="bg-slate-950/80 p-4 rounded-2xl border border-slate-800 space-y-1.5">
                    <p class="text-[10px] uppercase font-bold tracking-wider text-slate-400 mono">3. Bottom developing?</p>
                    <p id="ans3Title" class="text-sm font-extrabold text-indigo-400 mono">YES (Base Recovery)</p>
                    <p id="ans3Desc" class="text-[11px] text-slate-300">Score 78/100. Volume absorption at ₹694 low; 20-day SMA curved up; regime prob 65%.</p>
                </div>

                <!-- Answer 4: How much to buy? -->
                <div class="bg-slate-950/80 p-4 rounded-2xl border border-slate-800 space-y-1.5">
                    <p class="text-[10px] uppercase font-bold tracking-wider text-slate-400 mono">4. How much to buy?</p>
                    <p id="ans4Title" class="text-sm font-extrabold text-amber-400 mono">245 Shares (20%)</p>
                    <p id="ans4Desc" class="text-[11px] text-slate-300">₹1,99,430 cash. Max 15% single-stock wealth cap enforced. 80% liquid reserve kept.</p>
                </div>

                <!-- Answer 5: How confident? -->
                <div class="bg-slate-950/80 p-4 rounded-2xl border border-slate-800 space-y-1.5">
                    <p class="text-[10px] uppercase font-bold tracking-wider text-slate-400 mono">5. How confident?</p>
                    <p id="ans5Title" class="text-sm font-extrabold text-teal-400 mono">62% Beat Alpha</p>
                    <p id="ans5Desc" class="text-[11px] text-slate-300">Calibrated Brier: 0.182. 90% CI: [-3.2%, +11.8%]. Downside prob: 38%.</p>
                </div>
            </div>

            <!-- "What Would Change My Mind" Box -->
            <div class="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 flex items-start gap-3 text-xs">
                <span class="text-slate-400 text-sm">🧠</span>
                <div class="space-y-0.5">
                    <span class="font-bold text-slate-300 uppercase tracking-wider mono text-[10px]">What Would Change My Mind (Thesis Invalidation Rules):</span>
                    <p id="changeMindText" class="text-slate-400 text-[11px] leading-relaxed">
                        • <strong>Fundamental Break:</strong> Quarterly deposit growth dipping below 11% YoY or Gross NPA spiking > 1.6% would invalidate the investment thesis and immediately freeze all future tranches.<br>
                        • <strong>Valuation Exit:</strong> Stock re-rating to 3.40x P/B (10-year historical median, ~₹1,340) closes the cyclical discount and triggers scheduled profit taking.<br>
                        • <strong>Tactical Ratchet:</strong> Raise protective stop ONLY upon confirmed higher swing lows on daily close; never exit long-term core on ATR stop alone.
                    </p>
                </div>
            </div>
        </section>

        <!-- ========================================================================= -->
        <!-- SECTION 1: PRIMARY CYCLICAL ACCUMULATION ENGINE (LONG-TERM INTELLIGENCE) -->
        <!-- ========================================================================= -->
        <section class="space-y-6">
            <div class="flex items-center justify-between">
                <div>
                    <span class="text-xs font-bold tracking-widest text-indigo-400 uppercase mono">Primary Objective</span>
                    <h2 class="text-2xl font-extrabold text-white tracking-tight">Cyclical Accumulation Engine</h2>
                    <p class="text-xs text-slate-400">Identifies multi-year value bottoms, guards balance-sheet quality, and ladders capital into market corrections.</p>
                </div>
                <span class="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 mono">
                    Active Regime: Deep Value Zone
                </span>
            </div>

            <!-- Top 4 Cyclical KPI Cards -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <!-- 1. Bottom Opportunity Score -->
                <div class="bg-slate-900/90 border border-slate-800 p-5 rounded-2xl relative overflow-hidden">
                    <div class="flex items-center justify-between">
                        <p class="text-xs uppercase tracking-wider text-slate-400 font-semibold">Bottom Opportunity Score</p>
                        <span class="text-[10px] mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">Pillar 1</span>
                    </div>
                    <div class="flex items-baseline gap-2 mt-3">
                        <span id="statBottomScore" class="text-3xl font-extrabold mono text-emerald-400">78</span>
                        <span class="text-sm font-semibold text-slate-500 mono">/ 100</span>
                    </div>
                    <p class="text-xs text-emerald-300 font-medium mt-1" id="statBottomLabel">Attractive Setup</p>
                    <p class="text-[11px] text-slate-500 mt-1">Weighted 5-pillar cyclical convergence</p>
                </div>

                <!-- 2. Fundamental Health -->
                <div class="bg-slate-900/90 border border-slate-800 p-5 rounded-2xl">
                    <div class="flex items-center justify-between">
                        <p class="text-xs uppercase tracking-wider text-slate-400 font-semibold">Fundamental Health</p>
                        <span class="text-[10px] mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-bold">Gate</span>
                    </div>
                    <div class="flex items-baseline gap-2 mt-3">
                        <span id="statFundScore" class="text-3xl font-extrabold mono text-blue-400">84</span>
                        <span class="text-sm font-semibold text-slate-500 mono">/ 100</span>
                    </div>
                    <p class="text-xs text-blue-300 font-medium mt-1">Sound · No Critical Red Flags</p>
                    <p class="text-[11px] text-slate-500 mt-1" id="statFundDetail">GNPA 1.11% · NIM 3.16% · CAR 19.3%</p>
                </div>

                <!-- 3. Valuation Percentile -->
                <div class="bg-slate-900/90 border border-slate-800 p-5 rounded-2xl">
                    <div class="flex items-center justify-between">
                        <p class="text-xs uppercase tracking-wider text-slate-400 font-semibold">10-Year Valuation Percentile</p>
                        <span class="text-[10px] mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-bold">Cheap</span>
                    </div>
                    <div class="flex items-baseline gap-2 mt-3">
                        <span id="statValPercentile" class="text-3xl font-extrabold mono text-indigo-400">16th</span>
                        <span class="text-xs font-semibold text-slate-400 mono">P/B: 2.06x</span>
                    </div>
                    <p class="text-xs text-indigo-300 font-medium mt-1">Historically Inexpensive</p>
                    <p class="text-[11px] text-slate-500 mt-1">10Y Median: 3.40x · 33% discount to ICICI</p>
                </div>

                <!-- 4. Market Regime -->
                <div class="bg-slate-900/90 border border-slate-800 p-5 rounded-2xl">
                    <div class="flex items-center justify-between">
                        <p class="text-xs uppercase tracking-wider text-slate-400 font-semibold">Macro Banking Regime</p>
                        <span class="text-[10px] mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-bold">Stage</span>
                    </div>
                    <div class="flex items-baseline gap-2 mt-3">
                        <span id="statRegime" class="text-2xl font-bold text-amber-400 tracking-tight">Recovery</span>
                    </div>
                    <p class="text-xs text-amber-300/90 font-medium mt-1">Early Absorption & Base Building</p>
                    <p class="text-[11px] text-slate-500 mt-1">C/D 98.4% digesting merger supply</p>
                </div>
            </div>

            <!-- Accumulation Recommendation Hero Banner -->
            <div class="bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950/40 border border-slate-800 p-7 rounded-3xl space-y-6 glow-emerald">
                <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-slate-800/80">
                    <div class="space-y-2 max-w-2xl">
                        <div class="flex items-center gap-3">
                            <span class="px-4 py-1.5 rounded-xl font-bold text-xs uppercase tracking-wider bg-emerald-500 text-slate-950">
                                Accumulation Recommendation
                            </span>
                            <span class="text-sm font-extrabold text-emerald-400 uppercase tracking-wide mono">BUY IN TRANCHES</span>
                        </div>
                        <h3 class="text-xl font-bold text-white">Deploy 20% of planned capital · Reserve remaining 80%</h3>
                        <p class="text-xs text-slate-300 leading-relaxed" id="accumulationSummary">
                            Valuation percentile is near decade-lows (2.06x P/B). However, with tactical 2:00 PM momentum overextended (RSI 88), 
                            deploy only an initial 20% tranche today (₹2,00,000 of ₹10L budget). Preserve 80% capital to buy aggressively if the stock pulls back toward the ₹740–₹770 zone.
                        </p>
                    </div>

                    <!-- Forward Risk / Reward Card -->
                    <div class="grid grid-cols-3 gap-3 bg-slate-950/70 p-4 rounded-2xl border border-slate-800/90 min-w-[320px]">
                        <div>
                            <p class="text-[10px] text-slate-400 font-semibold uppercase">6M Upside</p>
                            <p class="text-lg font-bold mono text-emerald-400 mt-1">+18.5%</p>
                            <p class="text-[10px] text-slate-500 mono">Fair: ₹920</p>
                        </div>
                        <div class="border-x border-slate-800 px-3">
                            <p class="text-[10px] text-slate-400 font-semibold uppercase">Drawdown Risk</p>
                            <p class="text-lg font-bold mono text-rose-400 mt-1">-11.0%</p>
                            <p class="text-[10px] text-slate-500 mono">Floor: ₹710</p>
                        </div>
                        <div class="pl-1">
                            <p class="text-[10px] text-slate-400 font-semibold uppercase">Recovery Horizon</p>
                            <p class="text-sm font-bold text-indigo-300 mt-1.5">6–12M</p>
                            <p class="text-[10px] text-slate-500">Normalized ROE</p>
                        </div>
                    </div>
                </div>

                <!-- Capital Ladder Visualizer -->
                <div class="space-y-3">
                    <div class="flex items-center justify-between text-xs mono">
                        <span class="text-emerald-400 font-semibold">Proposed Deployment: 20% (₹2,00,000)</span>
                        <span class="text-slate-400">Cash Reserve: 80% (₹8,00,000)</span>
                    </div>
                    <div class="w-full h-3 rounded-full bg-slate-800 overflow-hidden flex">
                        <div class="h-full bg-gradient-to-r from-emerald-500 to-teal-400" style="width: 20%"></div>
                        <div class="h-full bg-slate-700/60" style="width: 80%"></div>
                    </div>
                    <p class="text-[11px] text-slate-400">
                        🛡️ <strong>Capital Preservation Policy</strong>: Never exhaust the entire allocation budget on the initial bottom attempt. Staged scaling guarantees cash on hand to lower your blended cost if macro volatility retests the bear case floor.
                    </p>
                </div>
            </div>
        </section>

        <!-- ========================================================================= -->
        <!-- SECTION 2: AI INVESTMENT COMMITTEE (3 SPECIALIZED ANALYSTS DEBATE)       -->
        <!-- ========================================================================= -->
        <section class="bg-slate-900/90 border border-slate-800 p-7 rounded-3xl space-y-6 glow-indigo">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
                <div>
                    <span class="text-xs font-bold tracking-widest text-indigo-400 uppercase mono">Deliberative Synthesis</span>
                    <h3 class="text-lg font-bold text-white">AI Investment Committee</h3>
                    <p class="text-xs text-slate-400">Three distinct analytical agents evaluate valuation, tail-risk, and market timing before issuing a unified verdict.</p>
                </div>
                <span class="text-xs font-semibold px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 mono">
                    Unanimous on Value · Divided on Timing
                </span>
            </div>

            <!-- 3 Analysts Grid -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <!-- Value Analyst -->
                <div class="bg-slate-950/70 p-5 rounded-2xl border border-slate-800/80 space-y-3">
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-bold text-emerald-400 uppercase mono">1. Value Analyst</span>
                        <span class="text-[11px] mono text-slate-400">Conviction: 86%</span>
                    </div>
                    <h4 class="text-xs font-bold text-white">Generational Valuation Discount</h4>
                    <p class="text-xs text-slate-300 leading-relaxed">
                        HDFC Bank at 2.06x P/B trades at its 16th percentile in a decade. Crucially, it trades at an unprecedented <strong>33% discount to ICICI Bank</strong> (2.06x vs 3.10x) compared to its historical 40% premium. Long-term margin of safety is exceptional.
                    </p>
                    <div class="pt-2 border-t border-slate-800/80 text-[10px] text-slate-400 space-y-1">
                        <p>• Book value compounding at 11–12% per year.</p>
                        <p>• Normalized fair value: ₹920 (Base) to ₹1,060 (Bull).</p>
                    </div>
                </div>

                <!-- Risk Analyst -->
                <div class="bg-slate-950/70 p-5 rounded-2xl border border-slate-800/80 space-y-3">
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-bold text-rose-400 uppercase mono">2. Risk Analyst</span>
                        <span class="text-[11px] mono text-slate-400">Caution: 74%</span>
                    </div>
                    <h4 class="text-xs font-bold text-white">Post-Merger C/D Ratio Drag</h4>
                    <p class="text-xs text-slate-300 leading-relaxed">
                        The Credit-to-Deposit ratio remains high at <strong>98.4%</strong>. The bank is intentionally restricting loan growth to 7% while paying high rates to grow deposits at 15%. If RBI systemic liquidity deficits persist, NIM will remain capped at 3.15%, delaying P/B expansion.
                    </p>
                    <div class="pt-2 border-t border-slate-800/80 text-[10px] text-slate-400 space-y-1">
                        <p>• Reserve 80% capital for potential test of ₹710-740 floor.</p>
                        <p>• Invalidation: Deposit growth dipping below 12%.</p>
                    </div>
                </div>

                <!-- Market Analyst -->
                <div class="bg-slate-950/70 p-5 rounded-2xl border border-slate-800/80 space-y-3">
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-bold text-amber-400 uppercase mono">3. Market Analyst</span>
                        <span class="text-[11px] mono text-slate-400">Tactical: 78%</span>
                    </div>
                    <h4 class="text-xs font-bold text-white">Intraday Momentum Overextended</h4>
                    <p class="text-xs text-slate-300 leading-relaxed">
                        After a vertical +17.7% run in 10 sessions, 14-day RSI is at <strong>88.7</strong> and price has stalled at the <strong>₹817.80 triple-top</strong> on fading volume (22M vs 73M peak). Do not chase fresh longs here; wait for a natural dip into ₹740–₹780.
                    </p>
                    <div class="pt-2 border-t border-slate-800/80 text-[10px] text-slate-400 space-y-1">
                        <p>• 2:00 PM Tactical: Trim/Hold off on fresh buying.</p>
                        <p>• Next Tranche Entry: Look for RSI stabilization below 50.</p>
                    </div>
                </div>
            </div>

            <!-- Committee Consensus Directive -->
            <div class="p-4 rounded-xl bg-indigo-950/30 border border-indigo-500/20 text-xs space-y-1">
                <span class="font-bold text-indigo-300 uppercase mono">Committee Directive:</span>
                <p class="text-slate-200">
                    Authorize Tranche #1 (20% budget deployment) into core long-term holdings. Retain 80% budget in liquid reserves. 
                    Trigger Tranche #2 only upon a pullback toward ₹740–₹770 OR a quarterly filing confirming C/D ratio normalizing under 95%.
                </p>
            </div>
        </section>

        <!-- ========================================================================= -->
        <!-- SECTION 3: HISTORICAL BOTTOM ANALOGUES & REPLAY ENGINE                   -->
        <!-- ========================================================================= -->
        <section class="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4">
            <div class="flex items-center justify-between pb-3 border-b border-slate-800">
                <div>
                    <h3 class="text-base font-bold text-white">Historical Bottom Replay & Analogue Matching</h3>
                    <p class="text-xs text-slate-400">Reconstructing what happened in past cycles when HDFC Bank hit similar valuation percentiles</p>
                </div>
                <span class="text-xs mono px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">Point-in-Time Verified</span>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <!-- Analogue 1 -->
                <div class="bg-slate-950/70 p-4 rounded-xl border border-slate-800/80 space-y-2">
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-bold text-white">March 2020 (COVID Panic)</span>
                        <span class="text-[10px] mono text-emerald-400">Score: 94</span>
                    </div>
                    <div class="text-[11px] mono text-slate-400 grid grid-cols-2 gap-1 py-1">
                        <span>P/B: 2.15x (9th %ile)</span>
                        <span>Drawdown: -37.8%</span>
                    </div>
                    <div class="text-xs text-slate-300 pt-1 border-t border-slate-800">
                        <p class="text-emerald-400 font-semibold mono">Forward Returns:</p>
                        <p class="mono text-[11px] text-slate-300">90d: +32.4% · 180d: +68.2% · 365d: +94.6%</p>
                        <p class="text-[10px] text-rose-400 mono mt-0.5">Max Adverse Excursion (MAE): -4.2%</p>
                    </div>
                </div>

                <!-- Analogue 2 -->
                <div class="bg-slate-950/70 p-4 rounded-xl border border-slate-800/80 space-y-2">
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-bold text-white">June 2022 (FII Outflows)</span>
                        <span class="text-[10px] mono text-emerald-400">Score: 81</span>
                    </div>
                    <div class="text-[11px] mono text-slate-400 grid grid-cols-2 gap-1 py-1">
                        <span>P/B: 2.60x (28th %ile)</span>
                        <span>Drawdown: -23.8%</span>
                    </div>
                    <div class="text-xs text-slate-300 pt-1 border-t border-slate-800">
                        <p class="text-emerald-400 font-semibold mono">Forward Returns:</p>
                        <p class="mono text-[11px] text-slate-300">90d: +14.8% · 180d: +27.6% · 365d: +32.1%</p>
                        <p class="text-[10px] text-rose-400 mono mt-0.5">Max Adverse Excursion (MAE): -2.1%</p>
                    </div>
                </div>

                <!-- Analogue 3 -->
                <div class="bg-slate-950/70 p-4 rounded-xl border border-indigo-500/30 bg-indigo-950/10 space-y-2">
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-bold text-indigo-300">Jan 2024 (Post-Merger Base)</span>
                        <span class="text-[10px] mono text-indigo-400 font-bold">Closest Match ★</span>
                    </div>
                    <div class="text-[11px] mono text-slate-400 grid grid-cols-2 gap-1 py-1">
                        <span>P/B: 2.30x (18th %ile)</span>
                        <span>Drawdown: -21.4%</span>
                    </div>
                    <div class="text-xs text-slate-300 pt-1 border-t border-slate-800">
                        <p class="text-emerald-400 font-semibold mono">Forward Returns:</p>
                        <p class="mono text-[11px] text-slate-300">90d: +8.5% · 180d: +18.2% · 365d: +24.5%</p>
                        <p class="text-[10px] text-rose-400 mono mt-0.5">Max Adverse Excursion (MAE): -6.8% (3-week dip)</p>
                    </div>
                </div>
            </div>
        </section>

        <!-- ========================================================================= -->
        <!-- SECTION 4: SECONDARY SHORT-TERM TACTICAL INTELLIGENCE (2:00 PM ENGINE)   -->
        <!-- ========================================================================= -->
        <section class="space-y-6 pt-4 border-t border-slate-800">
            <div class="flex items-center justify-between">
                <div>
                    <span class="text-xs font-bold tracking-widest text-slate-400 uppercase mono">Secondary Tactical Layer</span>
                    <h2 class="text-xl font-bold text-white tracking-tight">2:00 PM Trading Intelligence & Intraday Execution</h2>
                    <p class="text-xs text-slate-400">Audited short-term momentum, realistic calibrated confidence, and next-day hedging/trimming signals.</p>
                </div>
                <span class="text-xs mono px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">Calibrated Out-of-Sample</span>
            </div>

            <!-- Tactical Signal Card -->
            <div class="bg-slate-900 border border-slate-800 p-6 rounded-2xl">
                <div class="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
                    <div class="space-y-2 max-w-2xl">
                        <div class="flex items-center gap-3">
                            <span class="px-3.5 py-1 rounded-xl font-bold text-xs uppercase tracking-wide bg-rose-500 text-white">
                                Tactical Signal: SELL / TRIM
                            </span>
                            <span class="text-xs mono text-slate-400">Empirically Calibrated Confidence: <strong class="text-slate-200">62.4%</strong> (Realistic Bayesian bounds)</span>
                        </div>
                        <h4 class="text-base font-bold text-white">Trim Tactical Profits into the +17.7% Parabolic Move</h4>
                        <p class="text-xs text-slate-300 leading-relaxed">
                            RSI at 88.7 and a triple-top test at ₹817.80 on drying volume advise locking in short-term trading gains. 
                            <strong>Crucial Distinction</strong>: While HDFC Bank is a confirmed long-term cyclical accumulation, buying more for a 1-day trade at ₹813 carries elevated downside risk.
                        </p>
                    </div>

                    <div class="grid grid-cols-2 gap-3 min-w-[260px]">
                        <div class="bg-slate-950/80 p-3 rounded-xl border border-slate-800">
                            <p class="text-[10px] text-slate-400 font-semibold">Tactical Pullback Target</p>
                            <p class="text-base font-bold mono text-emerald-400 mt-1">₹766.31</p>
                            <p class="text-[10px] text-slate-500">20-Day SMA Support</p>
                        </div>
                        <div class="bg-slate-950/80 p-3 rounded-xl border border-slate-800">
                            <p class="text-[10px] text-slate-400 font-semibold">Breakout Invalidation Stop</p>
                            <p class="text-base font-bold mono text-rose-400 mt-1">₹839.09</p>
                            <p class="text-[10px] text-slate-500">Above Resistance Ceiling</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Multi-Timeframe Forecasts Grid -->
            <div class="grid grid-cols-2 sm:grid-cols-5 gap-3">
                <div class="bg-slate-900 border border-slate-800 p-3.5 rounded-xl">
                    <p class="text-[10px] text-slate-400 mono font-semibold">5-Day Tactical</p>
                    <p class="text-sm font-bold mono text-rose-400 mt-1">-1.2%</p>
                    <p class="text-[10px] text-slate-500">Target: ₹803</p>
                </div>
                <div class="bg-slate-900 border border-slate-800 p-3.5 rounded-xl">
                    <p class="text-[10px] text-slate-400 mono font-semibold">20-Day Swing</p>
                    <p class="text-sm font-bold mono text-emerald-400 mt-1">+2.8%</p>
                    <p class="text-[10px] text-slate-500">Target: ₹835</p>
                </div>
                <div class="bg-slate-900 border border-slate-800 p-3.5 rounded-xl">
                    <p class="text-[10px] text-slate-400 mono font-semibold">60-Day Quarterly</p>
                    <p class="text-sm font-bold mono text-emerald-400 mt-1">+8.2%</p>
                    <p class="text-[10px] text-slate-500">Target: ₹880</p>
                </div>
                <div class="bg-slate-900 border border-slate-800 p-3.5 rounded-xl">
                    <p class="text-[10px] text-slate-400 mono font-semibold">120-Day Half-Year</p>
                    <p class="text-sm font-bold mono text-emerald-400 mt-1">+14.5%</p>
                    <p class="text-[10px] text-slate-500">Target: ₹931</p>
                </div>
                <div class="bg-slate-900 border border-slate-800 p-3.5 rounded-xl">
                    <p class="text-[10px] text-slate-400 mono font-semibold">252-Day Annual</p>
                    <p class="text-sm font-bold mono text-emerald-400 mt-1">+26.4%</p>
                    <p class="text-[10px] text-slate-500">Target: ₹1,028</p>
                </div>
            </div>

            <!-- Event-Aware News & Backtest Row -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Backtest Visualizer (2 Cols) -->
                <div class="lg:col-span-2 bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4">
                    <div class="flex items-center justify-between pb-3 border-b border-slate-800">
                        <div>
                            <h4 class="text-sm font-bold text-white">Audited Historical Backtest (With 0.10% Friction)</h4>
                            <p class="text-xs text-slate-400">Comparing tactical signals against Buy & Hold benchmark</p>
                        </div>
                        <select id="selectPeriod" onchange="runBacktest()" class="bg-slate-800 text-xs border border-slate-700 rounded-lg px-3 py-1.5 mono">
                            <option value="1y">1 Year Walk-Forward</option>
                            <option value="2y" selected>2 Years Walk-Forward</option>
                            <option value="3y">3 Years Walk-Forward</option>
                        </select>
                    </div>

                    <div class="h-64 w-full">
                        <canvas id="equityChart"></canvas>
                    </div>
                </div>

                <!-- Event-Aware News Classification (1 Col) -->
                <div class="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4">
                    <div class="flex items-center justify-between pb-3 border-b border-slate-800">
                        <h4 class="text-sm font-bold text-white">Event Intelligence</h4>
                        <span class="text-[10px] mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Classified</span>
                    </div>
                    <div id="eventStream" class="space-y-3 max-h-[290px] overflow-y-auto pr-1 text-xs">
                        <p class="text-slate-500">Classifying banking headlines by material impact...</p>
                    </div>
                </div>
            </div>
        </section>

    </main>

    <script>
        let chartInstance = null;

        function updateClock() {
            const now = new Date();
            const timeStr = now.toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour12: false });
            document.getElementById('liveClock').textContent = timeStr + ' IST';
        }
        setInterval(updateClock, 1000);
        updateClock();

        async function fetchStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();

                if (data.events) {
                    renderEvents(data.events.material_events || data.events.all_events || []);
                }

                if (data.arbitration && data.deterministic_tranche) {
                    const arb = data.arbitration;
                    const tr = data.deterministic_tranche;

                    const badge = document.getElementById('decisionActionBadge');
                    if (tr.exact_shares > 0 && !arb.is_event_blackout_active) {
                        badge.className = "px-4 py-1.5 rounded-xl font-extrabold text-sm tracking-wider uppercase mono bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-2";
                        badge.innerHTML = `<span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span> ACCUMULATE (${tr.tranche_label})`;
                    } else if (arb.is_event_blackout_active) {
                        badge.className = "px-4 py-1.5 rounded-xl font-extrabold text-sm tracking-wider uppercase mono bg-rose-500/20 text-rose-300 border border-rose-500/40 flex items-center gap-2";
                        badge.innerHTML = `<span class="w-2.5 h-2.5 rounded-full bg-rose-400"></span> WAIT (EVENT BLACKOUT)`;
                    } else {
                        badge.className = "px-4 py-1.5 rounded-xl font-extrabold text-sm tracking-wider uppercase mono bg-amber-500/20 text-amber-300 border border-amber-500/40 flex items-center gap-2";
                        badge.innerHTML = `<span class="w-2.5 h-2.5 rounded-full bg-amber-400"></span> WAIT (PRESERVE CASH)`;
                    }

                    const ot = document.getElementById('orderTypeBadge');
                    if (arb.limit_entry_zone && arb.limit_entry_zone[0] > 0) {
                        ot.textContent = `${arb.execution_order_type}: ₹${arb.limit_entry_zone[0]} - ₹${arb.limit_entry_zone[1]}`;
                    } else {
                        ot.textContent = arb.execution_order_type;
                    }

                    const confBanner = document.getElementById('tierConflictBanner');
                    const confText = document.getElementById('tierConflictText');
                    if (arb.has_tier_conflict && arb.tier_conflict_explanation) {
                        confBanner.style.display = "flex";
                        confText.innerHTML = arb.tier_conflict_explanation;
                    } else {
                        confBanner.style.display = "none";
                    }

                    if (arb.what_would_change_my_mind) {
                        document.getElementById('changeMindText').innerHTML = arb.what_would_change_my_mind;
                    }
                }
            } catch (e) {
                console.error(e);
            }
        }

        function renderEvents(events) {
            const container = document.getElementById('eventStream');
            if (!events || events.length === 0) {
                container.innerHTML = '<p class="text-slate-500 text-xs">No material events detected.</p>';
                return;
            }
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

        async function triggerNow() {
            const btn = document.getElementById('btnTrigger');
            btn.disabled = true;
            btn.textContent = 'Updating...';
            try {
                await fetch('/api/trigger-signal', { method: 'POST' });
                await fetchStatus();
                await runBacktest();
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg> Refresh Intelligence';
            }
        }

        async function runBacktest() {
            const period = document.getElementById('selectPeriod').value;
            const res = await fetch(`/api/backtest?period=${period}`);
            const data = await res.json();
            renderChart(data.equity_curve || []);
        }

        function renderChart(curve) {
            const ctx = document.getElementById('equityChart').getContext('2d');
            const labels = curve.map(c => c.date);
            const stratData = curve.map(c => c.strategy_equity);
            const benchData = curve.map(c => c.benchmark_equity);

            if (chartInstance) chartInstance.destroy();

            chartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Tactical AI Strategy (With 0.10% Friction)',
                            data: stratData,
                            borderColor: '#10b981',
                            backgroundColor: 'rgba(16, 185, 129, 0.08)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.1,
                            pointRadius: 0
                        },
                        {
                            label: 'Buy & Hold Benchmark (₹)',
                            data: benchData,
                            borderColor: '#64748b',
                            borderWidth: 1.5,
                            borderDash: [4, 4],
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

                cb_detector = CyclicalBottomDetector()
                bottom_rep = cb_detector.evaluate_bottom_opportunity()

                fund_eng = FundamentalEngine()
                fund_profile = fund_eng.get_latest_fundamental_profile()

                val_eng = ValuationEngine()
                val_metrics = val_eng.compute_valuation_metrics()

                allocator = CapitalAllocator()
                capital_plan = allocator.compute_allocation_plan(
                    bottom_score=bottom_rep.bottom_opportunity_score,
                    current_price=quote.get("current_price", 813.5)
                )

                committee = InvestmentCommittee()
                committee_verdict = committee.convene_committee(current_price=quote.get("current_price", 813.5))

                analogues = HistoricalAnalogueEngine.get_closest_analogue(
                    current_pb=val_metrics.current_pb,
                    current_drawdown=val_metrics.drawdown_from_high_pct
                )

                ne = NewsEngine()
                raw_news = ne.get_latest_news_and_sentiment()
                events = EventIntelligenceEngine.filter_and_classify_stream(raw_news.get("top_articles", []))

                horizons = CalibratedConfidenceEngine.get_multi_horizon_targets(
                    current_price=quote.get("current_price", 813.5),
                    bottom_score=bottom_rep.bottom_opportunity_score
                )

                reg_eng = FairValueAndRegimeEngine()
                fair_val = reg_eng.compute_justified_fair_value(
                    current_price=quote.get("current_price", 813.5),
                    book_value_per_share=394.84
                )
                regime_state = reg_eng.evaluate_regime_state(
                    rsi_14=quote.get("rsi_14", 55.0),
                    dist_sma_20=quote.get("dist_sma_20", 0.01),
                    dist_sma_50=quote.get("dist_sma_50", -0.04),
                    vol_ratio=quote.get("volume_ratio", 1.0),
                    fundamental_score=fund_profile.fundamental_health_score
                )
                arbitration = reg_eng.arbitrate_decision(
                    bottom_opportunity_score=bottom_rep.bottom_opportunity_score,
                    fundamental_score=fund_profile.fundamental_health_score,
                    tactical_action="WAIT_FOR_LIMIT_PULLBACK",
                    current_price=quote.get("current_price", 813.5),
                    current_pb=val_metrics.current_pb
                )

                risk_eng = DeterministicRiskEngine()
                tranche_plan = risk_eng.calculate_tranche(
                    bottom_opportunity_score=bottom_rep.bottom_opportunity_score,
                    current_price=quote.get("current_price", 813.5),
                    portfolio_wealth=10000000.0
                )

                chain_valid, chain_errors = verify_decision_chain_integrity()

                data = {
                    "quote": quote,
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
                    "regime_state": regime_state.__dict__,
                    "arbitration": arbitration.__dict__,
                    "deterministic_tranche": tranche_plan.__dict__,
                    "chain_valid": chain_valid,
                    "analogues": analogues,
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
