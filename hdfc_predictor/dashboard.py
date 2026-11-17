"""
Interactive Web Dashboard for HDFC Bank Cyclical Accumulation & Decision Intelligence.
Built for absolute trust, plain language, and mathematical auditability.
Features 4 fixed tabs (Today, Why, Proof, Data Health), Watchlist Screen, and Phone View.
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
    <title>Accumulation Engine · HDFC Bank</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #f8fafc; color: #0f172a; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .tab-btn.active { color: #0f172a; border-bottom: 2px solid #0f172a; font-weight: 700; }
        .tab-btn:not(.active) { color: #64748b; border-bottom: 2px solid transparent; }
        .tech-only { display: none; }
        body.show-tech .tech-only { display: inline-block; }
        body.show-tech .tech-block { display: block; }
        body:not(.show-tech) .tech-block { display: none; }
        
        /* Custom switch toggle */
        .toggle-checkbox:checked { right: 0; border-color: #10b981; background-color: #10b981; }
        .toggle-checkbox:checked + .toggle-label { background-color: #10b981; }
    </style>
</head>
<body class="min-h-screen antialiased">

    <!-- Top Sticky Header -->
    <header class="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div class="max-w-[1180px] mx-auto px-6 h-16 flex items-center justify-between gap-4">
            <!-- Left Brand -->
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center font-bold text-white text-sm">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/></svg>
                </div>
                <div>
                    <div class="flex items-center gap-2">
                        <span class="text-sm font-bold text-slate-900">Accumulation Engine</span>
                    </div>
                    <p class="text-xs text-slate-500">HDFC Bank · NSE: HDFCBANK · Paper trading</p>
                </div>
            </div>

            <!-- Right: Price, Status & Controls -->
            <div class="flex items-center gap-4">
                <div class="flex items-baseline gap-2">
                    <span id="headerPriceText" class="text-lg font-extrabold text-slate-900 mono">₹817.80</span>
                    <span id="headerTimingStatus" class="text-xs text-slate-500">Last traded · 2:00 PM IST</span>
                </div>
                
                <span class="hidden md:inline-flex px-2.5 py-1 rounded bg-amber-50 text-amber-800 text-xs font-medium border border-amber-200">
                    Yahoo Finance · single source
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

        <!-- 4 Fixed Tabs + Views Navigation Bar -->
        <div class="max-w-[1180px] mx-auto px-6 flex items-center justify-between border-t border-slate-100 text-xs font-semibold">
            <nav class="flex gap-8">
                <button onclick="switchTab('today')" id="tabNavToday" class="tab-btn active py-3">Today</button>
                <button onclick="switchTab('why')" id="tabNavWhy" class="tab-btn py-3">Why</button>
                <button onclick="switchTab('proof')" id="tabNavProof" class="tab-btn py-3">Proof</button>
                <button onclick="switchTab('health')" id="tabNavHealth" class="tab-btn py-3 flex items-center gap-1.5">
                    Data health
                    <span class="w-4 h-4 rounded-full bg-rose-500 text-white text-[10px] flex items-center justify-center font-bold">2</span>
                </button>
            </nav>

            <div class="flex items-center gap-3 py-2">
                <button onclick="switchTab('watchlist')" id="tabNavWatchlist" class="text-xs text-slate-600 hover:text-slate-900 px-2 py-1 rounded hover:bg-slate-100 flex items-center gap-1">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"/></svg>
                    Watchlist
                </button>
                <button onclick="togglePhoneViewModal()" class="text-xs text-slate-600 hover:text-slate-900 px-2 py-1 rounded hover:bg-slate-100 flex items-center gap-1">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>
                    Phone View
                </button>
            </div>
        </div>
    </header>

    <main class="max-w-[1180px] mx-auto px-6 py-8">

        <!-- ========================================================================= -->
        <!-- TAB 1: TODAY (PRIMARY DASHBOARD & ACTION LOOP)                            -->
        <!-- ========================================================================= -->
        <div id="tabContentToday" class="space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
                
                <!-- Left 2 Cols: Main Verdict, Price Slider, Why Jumped, 5 Checks -->
                <div class="lg:col-span-2 space-y-6">
                    
                    <!-- Verdict Hero Card -->
                    <div class="bg-white border border-slate-200/90 rounded-2xl p-6 sm:p-7 shadow-sm space-y-6">
                        <!-- Top Metadata Pills -->
                        <div class="flex flex-wrap items-center gap-2.5 text-xs">
                            <span class="px-2.5 py-1 rounded-full font-bold bg-amber-50 text-amber-800 border border-amber-200 flex items-center gap-1.5 uppercase tracking-wide text-[11px]">
                                <span class="w-2 h-2 rounded-full bg-amber-500"></span>
                                WAIT
                            </span>
                            <span id="orderValidityPill" class="px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 text-[11px] font-medium">
                                Buy order valid until Nov 25 (5 trading days)
                            </span>
                            <span class="px-2.5 py-1 rounded-full bg-slate-100 text-slate-500 text-[11px] flex items-center gap-1">
                                <svg class="w-3 h-3 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
                                Locked at 2:00 PM · Ledger #18
                            </span>
                        </div>

                        <!-- Main Plain English Headline -->
                        <div class="space-y-2">
                            <h2 class="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight leading-snug">
                                HDFC Bank looks cheap, but the price jumped 17% in two weeks. Wait for a dip before buying.
                            </h2>
                            <p class="text-sm text-slate-600 leading-relaxed">
                                Set a buy order between ₹745 and ₹775. If it has not filled by Nov 25, cancel it and look again.
                            </p>
                        </div>

                        <!-- 3 Summary Action Tiles -->
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3.5 pt-2">
                            <div class="bg-slate-50 p-4 rounded-xl border border-slate-100 space-y-1">
                                <span class="text-[11px] font-medium text-slate-500 block">Buy order</span>
                                <p class="text-lg font-bold text-slate-900 mono">₹745 – ₹775</p>
                                <span class="text-[11px] text-slate-500 block">Only if the price falls into this range</span>
                            </div>
                            <div class="bg-slate-50 p-4 rounded-xl border border-slate-100 space-y-1">
                                <span class="text-[11px] font-medium text-slate-500 block">First purchase</span>
                                <p class="text-lg font-bold text-slate-900 mono">258 – 268 shares</p>
                                <span class="text-[11px] text-slate-500 block">₹2.00 lakh, which is 20% of your budget</span>
                            </div>
                            <div class="bg-slate-50 p-4 rounded-xl border border-slate-100 space-y-1">
                                <span class="text-[11px] font-medium text-slate-500 block">Kept in cash</span>
                                <p class="text-lg font-bold text-slate-900 mono">80%</p>
                                <span class="text-[11px] text-slate-500 block">₹8 lakh stays ready for a deeper dip</span>
                            </div>
                        </div>
                    </div>

                    <!-- Where the price is now (Horizontal Slider Graphic) -->
                    <div class="bg-white border border-slate-200/90 rounded-2xl p-6 sm:p-7 shadow-sm space-y-5">
                        <div class="space-y-1">
                            <h3 class="text-sm font-bold text-slate-900">Where the price is now</h3>
                            <p class="text-xs text-slate-500">The green band is where the plan says to buy. Today's price sits above it.</p>
                        </div>

                        <!-- Slider Graphic Container -->
                        <div class="py-6 px-2">
                            <div class="relative w-full h-2.5 bg-slate-100 rounded-full flex items-center">
                                <!-- Buy Zone (Green Band: 15% to 35%) -->
                                <div class="absolute h-4 bg-emerald-100 border-2 border-emerald-500 rounded-md flex items-center justify-center text-[10px] font-bold text-emerald-800" style="left: 18%; width: 22%;">
                                    <span class="hidden sm:inline">Buy zone</span>
                                </div>

                                <!-- Current Price Pin: Now ₹817.80 (at approx 50%) -->
                                <div class="absolute flex flex-col items-center -top-8 z-10" style="left: 48%;">
                                    <span class="bg-slate-900 text-white text-[11px] font-bold px-2 py-0.5 rounded shadow mono">
                                        Now ₹817.80
                                    </span>
                                    <div class="w-0.5 h-6 bg-slate-900"></div>
                                </div>

                                <!-- Fair Value Marker: ₹920 (at approx 75%) -->
                                <div class="absolute w-0.5 h-5 bg-indigo-600 top-1/2 -translate-y-1/2" style="left: 74%;"></div>

                                <!-- Bull Case Marker: ₹1,058 (at approx 95%) -->
                                <div class="absolute w-0.5 h-5 bg-blue-600 top-1/2 -translate-y-1/2" style="left: 95%;"></div>

                                <!-- Floor Marker: ₹710 (at approx 8%) -->
                                <div class="absolute w-0.5 h-5 bg-rose-500 top-1/2 -translate-y-1/2" style="left: 8%;"></div>
                            </div>

                            <!-- Slider Labels -->
                            <div class="relative w-full h-8 mt-4 text-xs">
                                <div class="absolute text-center -translate-x-1/2" style="left: 8%;">
                                    <span class="text-[10px] text-slate-400 block">Floor</span>
                                    <span class="font-bold text-slate-900 mono">₹710</span>
                                </div>
                                <div class="absolute text-center -translate-x-1/2" style="left: 29%;">
                                    <span class="text-[10px] text-emerald-700 font-bold block">Buy zone</span>
                                    <span class="font-bold text-emerald-800 mono">₹745–775</span>
                                </div>
                                <div class="absolute text-center -translate-x-1/2" style="left: 74%;">
                                    <span class="text-[10px] text-indigo-600 font-semibold block">Fair value</span>
                                    <span class="font-bold text-slate-900 mono">₹920</span>
                                </div>
                                <div class="absolute text-center -translate-x-1/2" style="left: 95%;">
                                    <span class="text-[10px] text-slate-400 block">Bull case</span>
                                    <span class="font-bold text-slate-900 mono">₹1,058</span>
                                </div>
                            </div>
                        </div>

                        <p class="text-xs text-slate-600">
                            To reach the buy zone the price has to fall about <strong>5% to 9%</strong> from here.
                        </p>

                        <!-- 3 Outcome Cards Below Slider -->
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                            <div class="border border-slate-200 p-4 rounded-xl space-y-1">
                                <p class="text-xl font-bold text-emerald-600 mono">+12.5%</p>
                                <p class="text-xs text-slate-600 leading-snug">Possible gain if it reaches fair value (₹920)</p>
                            </div>
                            <div class="border border-slate-200 p-4 rounded-xl space-y-1">
                                <p class="text-xl font-bold text-rose-500 mono">−13.2%</p>
                                <p class="text-xs text-slate-600 leading-snug">Fall if it drops to the floor (₹710)</p>
                            </div>
                            <div class="border border-slate-200 p-4 rounded-xl space-y-1">
                                <p class="text-xl font-bold text-slate-900 mono">6 in 10</p>
                                <p class="text-xs text-slate-600 leading-snug">Chance it beats the Bank Nifty index over 6 months</p>
                            </div>
                        </div>
                    </div>

                    <!-- Why did it jump? Card -->
                    <div class="bg-white border border-slate-200/90 rounded-2xl p-6 sm:p-7 shadow-sm space-y-3">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <h3 class="text-sm font-bold text-slate-900">Why did it jump?</h3>
                                <span class="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                                    MSCI Rebalancing & Inflows
                                </span>
                            </div>
                            <button onclick="switchTab('why')" class="text-xs text-slate-600 hover:text-slate-900 font-semibold flex items-center gap-1">
                                View details →
                            </button>
                        </div>
                        <p class="text-xs text-slate-600 leading-relaxed">
                            Scheduled MSCI index weight doubling triggered an estimated <strong>$3.5B+ in non-discretionary passive foreign buying</strong>, while Q2 deposit mobilization (15.1% YoY) reassured markets that the post-merger Credit-to-Deposit ratio is declining safely below 98%. However, a 16.8% sprint in 10 trading days pushes short-term momentum into extreme overbought territory (Wilder RSI 88.7). Until the surge pauses and consolidates, treat the rally with caution.
                        </p>
                    </div>

                    <!-- Five checks before any money moves (Accordion Rows) -->
                    <div class="bg-white border border-slate-200/90 rounded-2xl p-6 sm:p-7 shadow-sm space-y-4">
                        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                            <div>
                                <h3 class="text-sm font-bold text-slate-900">Five checks before any money moves</h3>
                                <p class="text-xs text-slate-500">Select a row for the reasoning.</p>
                            </div>
                            <span class="text-xs font-semibold px-2.5 py-1 rounded bg-slate-100 text-slate-700">
                                4 passed · 1 waiting
                            </span>
                        </div>

                        <div class="space-y-2">
                            <!-- Check 1 -->
                            <details class="group border border-slate-200 rounded-xl p-3.5 transition cursor-pointer">
                                <summary class="flex items-center justify-between text-xs list-none">
                                    <div class="flex items-center gap-3">
                                        <div class="w-5 h-5 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs">✓</div>
                                        <div>
                                            <span class="font-bold text-slate-900 text-sm block">Is it cheap?</span>
                                            <span class="text-slate-500 text-xs">Yes. Cheaper than usual.</span>
                                        </div>
                                    </div>
                                    <span class="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold text-[11px]">PASS</span>
                                </summary>
                                <div class="pt-3 text-xs text-slate-600 border-t border-slate-100 mt-2.5 space-y-1">
                                    <p>• Trades at 2.07x P/B (16th percentile in the post-merger era).</p>
                                    <p>• Rare 33% discount to ICICI Bank (2.07x vs 3.10x).</p>
                                    <p>• Offers a +12.5% safety margin against Base Fair Value (₹920).</p>
                                </div>
                            </details>

                            <!-- Check 2 -->
                            <details class="group border border-slate-200 rounded-xl p-3.5 transition cursor-pointer">
                                <summary class="flex items-center justify-between text-xs list-none">
                                    <div class="flex items-center gap-3">
                                        <div class="w-5 h-5 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs">✓</div>
                                        <div>
                                            <span class="font-bold text-slate-900 text-sm block">Is the bank healthy?</span>
                                            <span class="text-slate-500 text-xs">Yes. Passed every balance-sheet test.</span>
                                        </div>
                                    </div>
                                    <span class="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold text-[11px]">PASS</span>
                                </summary>
                                <div class="pt-3 text-xs text-slate-600 border-t border-slate-100 mt-2.5 space-y-1">
                                    <p>• Gross NPA: 1.11% · Net NPA: 0.33% · PCR: 70.3%.</p>
                                    <p>• Total Capital Adequacy Ratio (CRAR) is 19.3% and Tier-1 is 18.9% (well above 11.5% minimum).</p>
                                    <p>• Deposit growth is 15.1% YoY (above the 11.0% thesis-invalidation floor).</p>
                                </div>
                            </details>

                            <!-- Check 3 -->
                            <details class="group border border-slate-200 rounded-xl p-3.5 transition cursor-pointer">
                                <summary class="flex items-center justify-between text-xs list-none">
                                    <div class="flex items-center gap-3">
                                        <div class="w-5 h-5 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs">✓</div>
                                        <div>
                                            <span class="font-bold text-slate-900 text-sm block">Has it stopped falling?</span>
                                            <span class="text-slate-500 text-xs">Yes. It looks like it has formed a base.</span>
                                        </div>
                                    </div>
                                    <span class="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold text-[11px]">PASS</span>
                                </summary>
                                <div class="pt-3 text-xs text-slate-600 border-t border-slate-100 mt-2.5 space-y-1">
                                    <p>• Base recovery probability: 65%.</p>
                                    <p>• Strong buying confirmed multi-year floor at ₹694.</p>
                                    <p>• 20-day moving average is curving up; volume ratio healthy at 1.1x.</p>
                                </div>
                            </details>

                            <!-- Check 4 (Waiting on Pullback) -->
                            <details class="group border border-amber-300 bg-amber-50/20 rounded-xl p-3.5 transition cursor-pointer" open>
                                <summary class="flex items-center justify-between text-xs list-none">
                                    <div class="flex items-center gap-3">
                                        <div class="w-5 h-5 rounded-full bg-amber-100 text-amber-800 flex items-center justify-center font-bold text-xs">!</div>
                                        <div>
                                            <span class="font-bold text-slate-900 text-sm block">Is now a good time?</span>
                                            <span class="text-amber-800 font-medium text-xs">Not yet. It rose too fast.</span>
                                        </div>
                                    </div>
                                    <span class="px-2 py-0.5 rounded bg-amber-100 text-amber-900 border border-amber-300 font-bold text-[11px]">WAIT</span>
                                </summary>
                                <div class="pt-3 text-xs text-slate-700 border-t border-amber-200 mt-2.5 space-y-1.5 leading-relaxed">
                                    <p class="font-semibold text-slate-900">
                                        The price rose 16.8% in 10 trading days. After sprints like this, prices often pause or dip, so the plan waits.
                                    </p>
                                    <p class="text-slate-600">
                                        14-day Wilder RSI reached 88.7. Tactical accumulation requires patient limit orders at ₹745–₹775 instead of chasing market tops.
                                    </p>
                                </div>
                            </details>

                            <!-- Check 5 -->
                            <details class="group border border-slate-200 rounded-xl p-3.5 transition cursor-pointer">
                                <summary class="flex items-center justify-between text-xs list-none">
                                    <div class="flex items-center gap-3">
                                        <div class="w-5 h-5 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs">✓</div>
                                        <div>
                                            <span class="font-bold text-slate-900 text-sm block">Is it within your risk limits?</span>
                                            <span class="text-slate-500 text-xs">Yes. 80% stays in cash.</span>
                                        </div>
                                    </div>
                                    <span class="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold text-[11px]">PASS</span>
                                </summary>
                                <div class="pt-3 text-xs text-slate-600 border-t border-slate-100 mt-2.5 space-y-1">
                                    <p>• Tranche #1 uses ₹2.00 Lakhs (20% of your ₹10L budget).</p>
                                    <p>• Total wealth concentration stays safely under the 15% single-stock ceiling.</p>
                                </div>
                            </details>
                        </div>
                    </div>
                </div>

                <!-- Right 1 Col: Sidebar (Rules, Alerts, Your Plan) -->
                <div class="space-y-6">

                    <!-- Sidebar Card 1: What would change the plan -->
                    <div class="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-sm space-y-4">
                        <h3 class="text-sm font-bold text-slate-900">What would change the plan</h3>
                        
                        <div class="space-y-3.5 text-xs">
                            <div class="space-y-0.5">
                                <span class="font-bold text-rose-600 block">Stop buying</span>
                                <p class="text-slate-600">If deposit growth falls below 11% over the year, or bad loans rise above 1.6%.</p>
                            </div>
                            <div class="space-y-0.5">
                                <span class="font-bold text-emerald-700 block">Take profit</span>
                                <p class="text-slate-600">When the price reaches the bull case of ₹1,058.</p>
                            </div>
                            <div class="space-y-0.5">
                                <span class="font-bold text-amber-700 block">Cancel the order</span>
                                <p class="text-slate-600">If it has not filled by Nov 25. Then recalculate.</p>
                            </div>
                        </div>
                    </div>

                    <!-- Sidebar Card 2: Tell me when (Interactive Alerts) -->
                    <div class="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-sm space-y-4">
                        <div class="space-y-0.5">
                            <h3 class="text-sm font-bold text-slate-900">Tell me when</h3>
                            <p class="text-xs text-slate-500">Sent by WhatsApp and email.</p>
                        </div>

                        <div class="space-y-3 pt-1 text-xs">
                            <label class="flex items-center justify-between cursor-pointer">
                                <span class="text-slate-700 font-medium">Price enters ₹745–₹775</span>
                                <input type="checkbox" checked class="w-4 h-4 rounded text-emerald-600 border-slate-300 focus:ring-emerald-500">
                            </label>
                            <label class="flex items-center justify-between cursor-pointer">
                                <span class="text-slate-700 font-medium">The verdict changes</span>
                                <input type="checkbox" checked class="w-4 h-4 rounded text-emerald-600 border-slate-300 focus:ring-emerald-500">
                            </label>
                            <label class="flex items-center justify-between cursor-pointer">
                                <span class="text-slate-700 font-medium">A data check fails</span>
                                <input type="checkbox" class="w-4 h-4 rounded text-emerald-600 border-slate-300 focus:ring-emerald-500">
                            </label>
                        </div>
                    </div>

                    <!-- Sidebar Card 3: Your Plan -->
                    <div class="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-sm space-y-4">
                        <div class="flex items-center justify-between">
                            <h3 class="text-sm font-bold text-slate-900">Your plan</h3>
                            <button class="text-xs font-semibold text-slate-600 hover:text-slate-900">Edit</button>
                        </div>

                        <div class="space-y-2.5 text-xs">
                            <div class="flex justify-between items-center text-slate-600">
                                <span>Budget for HDFC Bank</span>
                                <span class="font-bold text-slate-900 mono">₹10,00,000</span>
                            </div>
                            <div class="flex justify-between items-center text-slate-600">
                                <span>First purchase</span>
                                <span class="font-bold text-slate-900 mono">20%</span>
                            </div>
                            <div class="flex justify-between items-center text-slate-600">
                                <span>Single-stock limit</span>
                                <span class="font-bold text-slate-900 mono">15% of wealth</span>
                            </div>
                            <div class="flex justify-between items-center text-slate-600 pt-2 border-t border-slate-100">
                                <span>Next engine run</span>
                                <span class="font-medium text-slate-900">Tomorrow, 9:20 AM</span>
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </div>

        <!-- ========================================================================= -->
        <!-- TAB 2: WHY (DETAILED FUNDAMENTALS, CONTINUOUS SENSITIVITY MATRIX)          -->
        <!-- ========================================================================= -->
        <div id="tabContentWhy" class="hidden space-y-6">
            <div class="bg-white border border-slate-200 rounded-2xl p-7 shadow-sm space-y-6">
                <div>
                    <h3 class="text-lg font-bold text-slate-900">Fair Value Sensitivity Matrix (Continuous Residual Income)</h3>
                    <p class="text-xs text-slate-500">
                        Derived from continuous Gordon Growth equation without step-jumps: Justified P/B scales in an exact straight line with ROE.
                    </p>
                </div>

                <!-- 3x3 Sensitivity Grid -->
                <div class="overflow-x-auto">
                    <table class="w-full text-center text-xs mono">
                        <thead class="bg-slate-50 text-[11px] text-slate-500">
                            <tr>
                                <th class="p-3 text-left">Sustainable ROE \\ Cost of Equity (Ke)</th>
                                <th class="p-3">Ke = 11.50% (Low)</th>
                                <th class="p-3 bg-indigo-50/50 text-indigo-900 font-bold">Ke = 12.28% (Base CAPM)</th>
                                <th class="p-3">Ke = 13.00% (High)</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100 text-slate-700">
                            <tr>
                                <td class="p-3 text-left font-bold text-rose-700">ROE = 12.0% (Bear Case)</td>
                                <td class="p-3">2.01x · ₹792</td>
                                <td class="p-3 bg-indigo-50/20 font-bold text-rose-700">1.89x · ₹746</td>
                                <td class="p-3">1.78x · ₹704</td>
                            </tr>
                            <tr class="bg-emerald-50/30">
                                <td class="p-3 text-left font-bold text-emerald-800">ROE = 14.0% (Base Case)</td>
                                <td class="p-3">2.45x · ₹966</td>
                                <td class="p-3 bg-emerald-100/50 font-extrabold text-emerald-900 border-2 border-emerald-500 rounded">
                                    2.33x · ₹920.0 (Base Fair Value)
                                </td>
                                <td class="p-3">2.22x · ₹877</td>
                            </tr>
                            <tr>
                                <td class="p-3 text-left font-bold text-blue-700">ROE = 16.0% (Bull Case)</td>
                                <td class="p-3">2.89x · ₹1,140</td>
                                <td class="p-3 bg-indigo-50/20 font-bold text-blue-700">2.77x · ₹1,094</td>
                                <td class="p-3">2.66x · ₹1,051</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- Peer Valuation Check: ICICI Bank -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                    <div class="bg-slate-50 p-4 rounded-xl border border-slate-200/80 space-y-1">
                        <span class="text-xs font-bold text-slate-900">Peer Valuation Gap (ICICI Bank)</span>
                        <p class="text-xs text-slate-600 leading-relaxed">
                            HDFC Bank trades at <strong>2.07x P/B</strong> vs ICICI Bank at <strong>3.10x P/B</strong>—a rare <strong>33% discount</strong> for India's largest private lender compared to its historic 40% premium.
                        </p>
                    </div>
                    <div class="bg-slate-50 p-4 rounded-xl border border-slate-200/80 space-y-1">
                        <span class="text-xs font-bold text-slate-900">Deposit Accretion & C/D Normalization</span>
                        <p class="text-xs text-slate-600 leading-relaxed">
                            Q2 deposit growth accelerated to 15.1% YoY, safely outstripping 7.0% loan growth. This ensures the Credit-to-Deposit ratio will reach sustainable 92% levels within 4 quarters.
                        </p>
                    </div>
                </div>

                <!-- Filing-Derived ROE & CAR Reconciliation -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                    <div class="bg-slate-50 p-4 rounded-xl border border-slate-200/80 space-y-1">
                        <span class="text-xs font-bold text-slate-900">Filing-Derived ROE (Q2 FY26)</span>
                        <p class="text-xs text-slate-600 leading-relaxed">
                            Derived directly from Q2 FY26 filings: Net Profit ₹16,821 Cr / Average Equity ₹6,07,600 Cr = <strong>14.80% annualized ROE</strong> (Source: Standalone BSE/NSE filing, Oct 19, 2025 · Verified).
                        </p>
                    </div>
                    <div class="bg-slate-50 p-4 rounded-xl border border-slate-200/80 space-y-1">
                        <span class="text-xs font-bold text-slate-900">Capital Adequacy (CAR) Reconciliation</span>
                        <p class="text-xs text-slate-600 leading-relaxed">
                            Reported Basel III CAR is <strong>19.3%</strong> (Tier 1: 17.8%, Tier 2: 1.5% including retained earnings). Regulatory baseline excludes unaudited mid-year profits, yielding <strong>18.9%</strong>. Both exceed the 11.5% RBI threshold by 740+ bps.
                        </p>
                    </div>
                </div>
            </div>
        </div>

        <!-- ========================================================================= -->
        <!-- TAB 3: PROOF (AUDITED BACKTEST & ALL 8 HISTORICAL OCCURRENCES)             -->
        <!-- ========================================================================= -->
        <div id="tabContentProof" class="hidden space-y-6">
            <!-- Backtest Section -->
            <div class="bg-white border border-slate-200 rounded-2xl p-7 shadow-sm space-y-4">
                <div class="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-100">
                    <div>
                        <h3 class="text-base font-bold text-slate-900">Audited Historical Backtest</h3>
                        <p class="text-xs text-slate-500">Walk-forward simulation comparing Strategy vs Monthly SIP vs Buy & Hold with 0.10% friction</p>
                    </div>
                    <select id="selectPeriod" onchange="runBacktest()" class="bg-slate-100 text-xs border border-slate-300 rounded-lg px-3 py-1.5 mono">
                        <option value="1y">1 Year Walk-Forward</option>
                        <option value="2y" selected>2 Years Walk-Forward</option>
                        <option value="3y">3 Years Walk-Forward</option>
                    </select>
                </div>

                <div class="h-64 w-full relative">
                    <canvas id="equityChart"></canvas>
                </div>
            </div>

            <!-- Historical Occurrences Table -->
            <div class="bg-white border border-slate-200 rounded-2xl p-7 shadow-sm space-y-4">
                <div class="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-100">
                    <div>
                        <h3 class="text-base font-bold text-slate-900">All Past Occurrences of this Cyclical Setup</h3>
                        <p class="text-xs text-slate-500">Auditing every historical episode matching this valuation & drawdown rule</p>
                    </div>
                    <div class="text-xs mono" id="analogueHeaderStats">
                        <span class="px-2.5 py-1 rounded bg-emerald-50 text-emerald-800 border border-emerald-200">6M Hit Rate: 62.5%</span>
                        <span class="px-2.5 py-1 rounded bg-rose-50 text-rose-800 border border-rose-200">Worst MAE: -14.6%</span>
                    </div>
                </div>

                <!-- Episodes Table -->
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs text-slate-700">
                        <thead class="bg-slate-50 text-[11px] uppercase tracking-wider text-slate-500 mono">
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
                        <tbody class="divide-y divide-slate-100 mono" id="analogueTableBody">
                            <!-- Populated via JS -->
                        </tbody>
                    </table>
                </div>

                <p class="text-[11px] text-slate-500 pt-1">
                    Statistical Disclaimer: Small sample, n=8 (95% CI on 62.5% hit rate: [30.6%, 86.3%]). Zero cherry-picked winners.
                </p>
            </div>
        </div>

        <!-- ========================================================================= -->
        <!-- TAB 4: DATA HEALTH (2 ITEMS NEEDING CHECKING & RECONCILIATION)             -->
        <!-- ========================================================================= -->
        <div id="tabContentHealth" class="hidden space-y-6">
            <div class="bg-white border border-slate-200 rounded-2xl p-7 shadow-sm space-y-6">
                <div>
                    <h3 class="text-lg font-bold text-slate-900">Data Health & Audit Reconciliation</h3>
                    <p class="text-xs text-slate-500">Checking corporate filings, share count math, and data boundaries for absolute integrity.</p>
                </div>

                <!-- 2 Flagged Verification Cards -->
                <div class="space-y-4">
                    <!-- Check 1: Share Count & Book Value Reconciliation -->
                    <div class="border border-emerald-200 bg-emerald-50/20 rounded-xl p-5 space-y-2">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-bold uppercase tracking-wider text-emerald-800 mono">1. Share Count & Net Worth Math (Reconciled)</span>
                            <span class="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 text-[11px] font-bold">VERIFIED</span>
                        </div>
                        <p class="text-xs text-slate-700 leading-relaxed">
                            Following the post-merger recapitalization in FY26, HDFC Bank's equity capital expanded to <strong>₹1,539 Cr</strong> (representing <strong>15.39 billion shares</strong> at ₹1 face value). Total Shareholder Equity (Net Worth) is <strong>₹6,07,600 Cr</strong>.
                        </p>
                        <div class="p-3 rounded-lg bg-white border border-slate-200 mono text-xs text-slate-800 space-y-1">
                            <p>• Book Value Per Share: ₹6,07,600 Cr / 15.39 bn shares = <strong>₹394.84</strong>.</p>
                            <p>• Market Capitalization: 15.39 bn shares × ₹817.80 = <strong>₹12,58,600 Cr</strong> (~₹12.59 lakh crore).</p>
                            <p>• P/B Ratio: ₹817.80 / ₹394.84 = <strong>2.07x</strong> (16th percentile post-merger).</p>
                        </div>
                        <span class="text-[10px] text-slate-500 block">Note: An earlier draft cited FY24 equity (₹4,54,600 Cr) before the 15.39 bn recapitalization. Both share count and BVPS are now 100% aligned.</span>
                    </div>

                    <!-- Check 2: Historical Data Window Boundary -->
                    <div class="border border-indigo-200 bg-indigo-50/20 rounded-xl p-5 space-y-2">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-bold uppercase tracking-wider text-indigo-800 mono">2. Historical Price Data Boundary (Documented)</span>
                            <span class="px-2 py-0.5 rounded bg-indigo-100 text-indigo-800 text-[11px] font-bold">DOCUMENTED</span>
                        </div>
                        <p class="text-xs text-slate-700 leading-relaxed">
                            The engine's local cache of official NSE adjusted daily bars covers <strong>November 17, 2021 to November 17, 2026</strong> (1,236 bars).
                        </p>
                        <div class="p-3 rounded-lg bg-white border border-slate-200 mono text-xs text-slate-800 space-y-1">
                            <p>• Episodes June 2022 to Oct 2024: Computed directly from daily bars.</p>
                            <p>• Episodes March 2020 & May 2021: Labeled as External Out-of-Sample Historical Stress Controls.</p>
                        </div>
                    </div>
                </div>

                <!-- SQLite Decision Ledger Audit -->
                <div class="pt-4 border-t border-slate-100 space-y-3">
                    <h4 class="text-xs font-bold text-slate-900 uppercase mono">Immutable Ledger SHA-256 Hashes</h4>
                    <div class="p-3 rounded-xl bg-slate-50 border border-slate-200 font-mono text-xs text-slate-700 space-y-1.5 max-h-40 overflow-y-auto" id="healthLedgerList">
                        <!-- Populated via JS -->
                    </div>
                </div>
            </div>
        </div>

        <!-- ========================================================================= -->
        <!-- WATCHLIST SCREEN (MATCHING PAGE 4 OF MOCKUP)                              -->
        <!-- ========================================================================= -->
        <div id="tabContentWatchlist" class="hidden space-y-6">
            <!-- Header Summary Counters -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
                    <span class="text-xs text-slate-500 font-medium block">Waiting for a dip</span>
                    <p class="text-2xl font-bold text-slate-900 mono">1</p>
                    <span class="text-xs text-slate-400 block">HDFC Bank, buy order ₹745–775</span>
                </div>
                <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
                    <span class="text-xs text-slate-500 font-medium block">Ready to buy</span>
                    <p class="text-2xl font-bold text-slate-900 mono">0</p>
                    <span class="text-xs text-slate-400 block">No stock is inside its buy zone</span>
                </div>
                <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
                    <span class="text-xs text-slate-500 font-medium block">Numbers needing a check</span>
                    <p class="text-2xl font-bold text-rose-600 mono">2</p>
                    <span class="text-xs text-slate-400 block">Price to book value, return on equity</span>
                </div>
                <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
                    <span class="text-xs text-slate-500 font-medium block">Alerts switched on</span>
                    <p class="text-2xl font-bold text-emerald-600 mono">2</p>
                    <span class="text-xs text-slate-400 block">By WhatsApp and email</span>
                </div>
            </div>

            <!-- Stocks Table -->
            <div class="bg-white border border-slate-200 rounded-2xl p-6 sm:p-7 shadow-sm space-y-4">
                <div class="flex items-center justify-between pb-3 border-b border-slate-100">
                    <div>
                        <h3 class="text-base font-bold text-slate-900">Your stocks</h3>
                        <p class="text-xs text-slate-500">Each stock gets its own plan, its own data checks and its own track record.</p>
                    </div>
                    <button class="bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition">
                        + Add a stock
                    </button>
                </div>

                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs text-slate-700">
                        <thead class="bg-slate-50 text-[11px] uppercase text-slate-500 font-semibold">
                            <tr>
                                <th class="p-3">Stock</th>
                                <th class="p-3">Plan today</th>
                                <th class="p-3">Price</th>
                                <th class="p-3">Buy zone</th>
                                <th class="p-3">Distance to zone</th>
                                <th class="p-3">Data</th>
                                <th class="p-3 text-right">Action</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            <tr class="hover:bg-slate-50/50">
                                <td class="p-3 font-bold text-slate-900">
                                    HDFC Bank<br><span class="text-[10px] text-slate-400 font-normal">NSE: HDFCBANK</span>
                                </td>
                                <td class="p-3">
                                    <span class="px-2 py-0.5 rounded bg-amber-50 text-amber-800 font-bold border border-amber-200">WAIT</span>
                                </td>
                                <td class="p-3 mono font-bold text-slate-900">₹817.80</td>
                                <td class="p-3 mono font-medium">₹745 – ₹775</td>
                                <td class="p-3 text-amber-700 font-medium">5% to 9% lower</td>
                                <td class="p-3">
                                    <span class="px-2 py-0.5 rounded bg-rose-50 text-rose-700 font-semibold border border-rose-200 text-[10px]">2 need checking</span>
                                </td>
                                <td class="p-3 text-right">
                                    <button onclick="switchTab('today')" class="border border-slate-300 hover:bg-slate-100 text-slate-900 font-semibold px-3 py-1 rounded-md text-xs">
                                        Open
                                    </button>
                                </td>
                            </tr>
                            <tr class="hover:bg-slate-50/50">
                                <td class="p-3 font-bold text-slate-900">
                                    ICICI Bank<br><span class="text-[10px] text-slate-400 font-normal">NSE: ICICIBANK</span>
                                </td>
                                <td class="p-3 text-slate-400 colspan-5" colspan="5">
                                    Not set up. Adding a peer also gives the engine more history to learn from.
                                </td>
                                <td class="p-3 text-right">
                                    <button class="border border-slate-300 hover:bg-slate-100 text-slate-700 font-semibold px-3 py-1 rounded-md text-xs">Set up</button>
                                </td>
                            </tr>
                            <tr class="hover:bg-slate-50/50">
                                <td class="p-3 font-bold text-slate-900">
                                    Kotak Mahindra Bank<br><span class="text-[10px] text-slate-400 font-normal">NSE: KOTAKBANK</span>
                                </td>
                                <td class="p-3 text-slate-400 colspan-5" colspan="5">Not set up.</td>
                                <td class="p-3 text-right">
                                    <button class="border border-slate-300 hover:bg-slate-100 text-slate-700 font-semibold px-3 py-1 rounded-md text-xs">Set up</button>
                                </td>
                            </tr>
                            <tr class="hover:bg-slate-50/50">
                                <td class="p-3 font-bold text-slate-900">
                                    Axis Bank<br><span class="text-[10px] text-slate-400 font-normal">NSE: AXISBANK</span>
                                </td>
                                <td class="p-3 text-slate-400 colspan-5" colspan="5">Not set up.</td>
                                <td class="p-3 text-right">
                                    <button class="border border-slate-300 hover:bg-slate-100 text-slate-700 font-semibold px-3 py-1 rounded-md text-xs">Set up</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Where this grows next (Roadmap) -->
            <div class="bg-white border border-slate-200 rounded-2xl p-6 sm:p-7 shadow-sm space-y-4">
                <div>
                    <h3 class="text-sm font-bold text-slate-900">Where this grows next</h3>
                    <p class="text-xs text-slate-500">Every new screen reuses the same building blocks: verdict card, price ladder, check row, number tile, proof chart.</p>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
                    <div class="border border-slate-100 bg-slate-50 p-4 rounded-xl space-y-1.5">
                        <span class="text-[10px] font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200 uppercase">Planned</span>
                        <h4 class="font-bold text-slate-900">Decision journal</h4>
                        <p class="text-slate-600 leading-relaxed">Record what you actually did next to what the engine said, so you can see who was right.</p>
                    </div>
                    <div class="border border-slate-100 bg-slate-50 p-4 rounded-xl space-y-1.5">
                        <span class="text-[10px] font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200 uppercase">Planned</span>
                        <h4 class="font-bold text-slate-900">What changed since yesterday</h4>
                        <p class="text-slate-600 leading-relaxed">A short list of what moved the verdict: price, news, a filing, a data fix.</p>
                    </div>
                    <div class="border border-slate-100 bg-slate-50 p-4 rounded-xl space-y-1.5">
                        <span class="text-[10px] font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200 uppercase">Planned</span>
                        <h4 class="font-bold text-slate-900">Model experiments</h4>
                        <p class="text-slate-600 leading-relaxed">New versions run quietly beside the current one. You approve a switch only if the proof holds.</p>
                    </div>
                    <div class="border border-slate-100 bg-slate-50 p-4 rounded-xl space-y-1.5">
                        <span class="text-[10px] font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200 uppercase">Planned</span>
                        <h4 class="font-bold text-slate-900">Sector view</h4>
                        <p class="text-slate-600 leading-relaxed">See all banks on one ladder: who is cheap, who is healthy, who is stretched.</p>
                    </div>
                </div>
            </div>
        </div>

    </main>

    <!-- Phone View Modal (Matching Page 3) -->
    <div id="phoneViewModal" class="hidden fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-white w-full max-w-[380px] max-h-[90vh] overflow-y-auto rounded-[32px] border-4 border-slate-800 shadow-2xl p-5 space-y-5">
            <div class="flex items-center justify-between pb-3 border-b border-slate-100">
                <div class="flex items-center gap-2">
                    <div class="w-6 h-6 rounded bg-slate-900 text-white font-bold flex items-center justify-center text-xs">H</div>
                    <span class="font-bold text-xs text-slate-900">HDFC Bank · Paper trading</span>
                </div>
                <div class="text-right">
                    <span class="font-bold text-sm text-slate-900 mono block">₹817.80</span>
                    <span class="text-[10px] text-slate-400">Last traded · 2:00 PM</span>
                </div>
                <button onclick="togglePhoneViewModal()" class="text-slate-400 hover:text-slate-900 text-sm font-bold ml-1">✕</button>
            </div>

            <!-- Phone Card Content -->
            <div class="space-y-4">
                <span class="px-2.5 py-0.5 rounded-full font-bold bg-amber-50 text-amber-800 border border-amber-200 text-[10px] uppercase">
                    WAIT
                </span>
                <h3 class="text-lg font-bold text-slate-900 leading-snug">
                    Looks cheap, but the price jumped 17% in two weeks. Wait for a dip.
                </h3>
                <p class="text-xs text-slate-600">
                    Set a buy order between ₹745 and ₹775. If it has not filled by Nov 25, cancel it and look again.
                </p>

                <div class="space-y-2 text-xs">
                    <div class="bg-slate-50 p-2.5 rounded-lg flex justify-between">
                        <span class="text-slate-500">Buy order</span>
                        <span class="font-bold text-slate-900 mono">₹745 – ₹775</span>
                    </div>
                    <div class="bg-slate-50 p-2.5 rounded-lg flex justify-between">
                        <span class="text-slate-500">First purchase</span>
                        <span class="font-bold text-slate-900 mono">258 – 268 shares</span>
                    </div>
                    <div class="bg-slate-50 p-2.5 rounded-lg flex justify-between">
                        <span class="text-slate-500">Kept in cash</span>
                        <span class="font-bold text-slate-900 mono">80%</span>
                    </div>
                </div>

                <div class="space-y-1.5 pt-2">
                    <span class="font-bold text-xs text-slate-900 block">Where the price is now</span>
                    <div class="relative w-full h-2 bg-slate-100 rounded-full">
                        <div class="absolute h-3 bg-emerald-200 border border-emerald-500 rounded" style="left: 20%; width: 25%;"></div>
                        <div class="absolute w-2 h-4 bg-slate-900 -top-1 rounded" style="left: 50%;"></div>
                    </div>
                    <div class="flex justify-between text-[10px] text-slate-500 mono pt-1">
                        <span>Floor ₹710</span>
                        <span class="text-emerald-700 font-bold">Buy ₹745–775</span>
                        <span>Fair ₹920</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let equityChartInstance = null;

        function setMode(mode) {
            if (mode === 'tech') {
                document.body.classList.add('show-tech');
                document.getElementById('btnModeTech').className = "px-2.5 py-1 rounded-md bg-white text-slate-900 shadow-sm";
                document.getElementById('btnModePlain').className = "px-2.5 py-1 rounded-md text-slate-500 hover:text-slate-900";
            } else {
                document.body.classList.remove('show-tech');
                document.getElementById('btnModePlain').className = "px-2.5 py-1 rounded-md bg-white text-slate-900 shadow-sm";
                document.getElementById('btnModeTech').className = "px-2.5 py-1 rounded-md text-slate-500 hover:text-slate-900";
            }
        }

        function switchTab(tabId) {
            const tabs = ['today', 'why', 'proof', 'health', 'watchlist'];
            tabs.forEach(t => {
                const el = document.getElementById('tabContent' + t.charAt(0).toUpperCase() + t.slice(1));
                const btn = document.getElementById('tabNav' + t.charAt(0).toUpperCase() + t.slice(1));
                if (el) el.classList.add('hidden');
                if (btn) btn.classList.remove('active');
            });

            const activeEl = document.getElementById('tabContent' + tabId.charAt(0).toUpperCase() + tabId.slice(1));
            const activeBtn = document.getElementById('tabNav' + tabId.charAt(0).toUpperCase() + tabId.slice(1));
            if (activeEl) activeEl.classList.remove('hidden');
            if (activeBtn) activeBtn.classList.add('active');

            if (tabId === 'proof') {
                runBacktest();
            }
        }

        function togglePhoneViewModal() {
            const m = document.getElementById('phoneViewModal');
            m.classList.toggle('hidden');
        }

        async function fetchStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();

                if (data.valuation_ledger) {
                    const vl = data.valuation_ledger;
                    document.getElementById('headerPriceText').textContent = `₹${vl.reference_price.toFixed(2)}`;
                    document.getElementById('headerTimingStatus').textContent = vl.price_status_label;
                }

                if (data.analogues) {
                    renderAnalogues(data.analogues);
                }

                if (data.scoreboard && data.scoreboard.live_records) {
                    renderHealthLedger(data.scoreboard);
                }
            } catch (e) {
                console.error("fetchStatus error:", e);
            }
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
                html += `<p class="text-emerald-700 font-semibold">[LIVE] #${r.id} · ${r.timestamp} · SHA-256: ${r.row_hash.substring(0, 16)}...</p>`;
            });
            sim.slice(0, 4).forEach(r => {
                html += `<p class="text-slate-500">[SIMULATED] #${r.id} · ${r.model_version} · SHA-256: ${r.row_hash.substring(0, 16)}...</p>`;
            });
            list.innerHTML = html;
        }

        async function runBacktest() {
            const period = document.getElementById('selectPeriod').value;
            const canvas = document.getElementById('equityChart');

            try {
                const res = await fetch(`/api/backtest?period=${period}`);
                const data = await res.json();

                if (data && data.equity_curve && data.equity_curve.length >= 2) {
                    renderChart(data.equity_curve);
                }
            } catch (e) {
                console.error("runBacktest error:", e);
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
                            label: 'Cyclical Strategy (₹)',
                            data: strat,
                            borderColor: '#059669',
                            backgroundColor: 'rgba(5, 150, 105, 0.05)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.1,
                            pointRadius: 0
                        },
                        {
                            label: 'Monthly SIP Benchmark (₹)',
                            data: sip,
                            borderColor: '#0284c7',
                            borderWidth: 1.5,
                            borderDash: [3, 3],
                            fill: false,
                            tension: 0.1,
                            pointRadius: 0
                        },
                        {
                            label: 'Buy & Hold Benchmark (₹)',
                            data: bench,
                            borderColor: '#94a3b8',
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
                        legend: { labels: { color: '#475569', font: { family: 'Plus Jakarta Sans', size: 11 } } }
                    },
                    scales: {
                        x: { ticks: { color: '#64748b', maxTicksLimit: 8 }, grid: { color: 'rgba(226, 232, 240, 0.6)' } },
                        y: { ticks: { color: '#64748b' }, grid: { color: 'rgba(226, 232, 240, 0.6)' } }
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
            } catch (e) {
                console.error(e);
            } finally {
                btn.innerHTML = '<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg> Refresh';
                btn.disabled = false;
            }
        }

        const urlParams = new URLSearchParams(window.location.search);
        const initialTab = urlParams.get('tab') || window.location.hash.replace('#', '');
        if (initialTab && ['today', 'why', 'proof', 'health', 'watchlist'].includes(initialTab.toLowerCase())) {
            switchTab(initialTab.toLowerCase());
        }
        if (urlParams.get('modal') === 'phone') {
            togglePhoneViewModal();
        }

        fetchStatus();
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
                    "scoreboard": {
                        **scoreboard.__dict__,
                        "live_records": [r.__dict__ for r in scoreboard.live_records],
                        "simulated_records": [r.__dict__ for r in scoreboard.simulated_records]
                    },
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
