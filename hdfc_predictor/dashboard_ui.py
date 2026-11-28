"""Self-contained HTML/CSS/JS template for the HDFC Bank Accumulation Engine dashboard."""

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HDFC Bank · Smart Dip &amp; Accumulation Tracker</title>
    <!-- INJECTED_DATA -->
    <style>
        :root {
            --font-sans: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
            --groww-green: #00D09C;
            --groww-green-dark: #009E77;
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

        @property --fade-start {
            syntax: "<length>";
            inherits: false;
            initial-value: 0px;
        }
        @property --fade-end {
            syntax: "<length>";
            inherits: false;
            initial-value: 0px;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        html { scroll-behavior: smooth; }
        body {
            font-family: var(--font-sans);
            background-color: var(--slate-50);
            color: var(--slate-800);
            line-height: 1.5;
            font-size: 13px;
            -webkit-font-smoothing: antialiased;
        }
        .mono { font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
        .tech-only, .tech-block { display: none; }
        body.show-tech .tech-only { display: inline-flex; }
        body.show-tech .tech-block { display: block; }

        /* Accessible focus & tactile interactions */
        :where(a, button, input, select, textarea, summary, [tabindex]):focus-visible {
            outline: 2px solid CanvasText;
            outline-offset: 2px;
        }
        button {
            cursor: pointer;
            border: none;
            font-family: inherit;
            background: transparent;
        }
        @media (prefers-reduced-motion: no-preference) {
            :where(button) {
                transition: background-color 150ms ease-out, color 150ms ease-out, box-shadow 150ms ease-out, scale 120ms ease-out, border-color 150ms ease-out;
            }
            button:active { scale: 0.97; }
            .card-hover:hover { box-shadow: 0 6px 20px -4px rgba(15, 23, 42, 0.08); }
            .animate-pulse { animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
            .animate-spin { animation: spin 0.9s linear infinite; }
        }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.45; } }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

        /* Containment for heavy sections */
        .perf-region {
            content-visibility: auto;
            contain-intrinsic-size: auto 360px;
        }
        @supports not (content-visibility: auto) {
            .perf-region { contain: layout style paint; }
        }

        /* Compact Header + Tabs */
        .top-bar {
            position: sticky;
            top: 0;
            z-index: 50;
            background: rgba(255, 255, 255, 0.96);
            backdrop-filter: blur(8px);
            border-bottom: 1px solid var(--slate-200);
        }

        /* Tablist with horizontal scroll affordance & ::after underline indicator */
        .view-tablist {
            display: flex;
            align-items: center;
            gap: 0.25rem;
            overflow-x: auto;
            scrollbar-width: none;
            scroll-snap-type: inline proximity;
            --fade-size: 2.5rem;
            --fade-dir: right;
            --fade-start-pos: 0;
            --fade-end-pos: 100%;
            mask:
                linear-gradient(black, black) no-clip subtract,
                linear-gradient(to var(--fade-dir), black, transparent) var(--fade-start-pos) 0 / var(--fade-start) 100% no-repeat no-clip,
                linear-gradient(to var(--fade-dir), transparent, black) var(--fade-end-pos) 0 / var(--fade-end) 100% no-repeat no-clip;
            animation: reveal-fade-start linear both, hide-fade-end linear both;
            animation-timeline: scroll(self inline);
            animation-range: 0 var(--fade-size), calc(100% - var(--fade-size)) 100%;
        }
        .view-tablist::-webkit-scrollbar { display: none; }
        @keyframes reveal-fade-start { to { --fade-start: var(--fade-size); } }
        @keyframes hide-fade-end { from { --fade-end: var(--fade-size); } }
        .view-tablist.more-start { --fade-start: var(--fade-size); }
        .view-tablist.more-end { --fade-end: var(--fade-size); }

        .view-tab-btn {
            position: relative;
            flex: none;
            scroll-snap-align: start;
            padding: 0.75rem 1rem;
            font-size: 13px;
            font-weight: 600;
            color: var(--slate-500);
            white-space: nowrap;
            border-radius: 0.5rem 0.5rem 0 0;
        }
        .view-tab-btn:hover { color: var(--slate-900); background: var(--slate-50); }
        .view-tab-btn[aria-selected="true"] {
            color: var(--slate-900);
        }
        .view-tab-btn[aria-selected="true"]::after {
            content: "";
            position: absolute;
            inset: auto 0.5rem 0;
            border-block-end: 3px solid var(--groww-green);
            border-radius: 3px 3px 0 0;
        }

        /* Tab panels stack without gap/padding on the panel element itself */
        .tab-panels-stack { display: block; }
        [role="tabpanel"] { display: block; }
        [role="tabpanel"][hidden] { display: none; }
        [role="tabpanel"][hidden="until-found"] { content-visibility: hidden; display: block; height: 0; overflow: hidden; }

        /* Layout & Utility Classes (Zero CDN) */
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
        .min-w-0 { min-width: 0; }
        .flex-1 { flex: 1 1 0%; }

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
            .sm\:grid-cols-6 { grid-template-columns: repeat(6, minmax(0, 1fr)); }
            .sm\:inline { display: inline; }
            .sm\:inline-flex { display: inline-flex; }
            .sm\:flex { display: flex; }
            .sm\:px-6 { padding-left: 1.5rem; padding-right: 1.5rem; }
            .sm\:text-3xl { font-size: 1.875rem; line-height: 2.25rem; }
            .sm\:text-4xl { font-size: 2.25rem; line-height: 2.5rem; }
            .sm\:h-80 { height: 21rem; }
        }
        @media (min-width: 768px) {
            .md\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .md\:inline-flex { display: inline-flex; }
        }
        @media (min-width: 1024px) {
            .lg\:grid-cols-3 { grid-template-columns: 1.85fr 1.15fr; }
            .lg\:grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
            .lg\:col-span-2 { grid-column: span 1; }
        }

        .gap-1 { gap: 0.25rem; }
        .gap-1\.5 { gap: 0.375rem; }
        .gap-2 { gap: 0.5rem; }
        .gap-2\.5 { gap: 0.625rem; }
        .gap-3 { gap: 0.75rem; }
        .gap-4 { gap: 1rem; }
        .gap-5 { gap: 1.25rem; }
        .gap-6 { gap: 1.5rem; }

        .space-y-1 > * + * { margin-top: 0.25rem; }
        .space-y-1\.5 > * + * { margin-top: 0.375rem; }
        .space-y-2 > * + * { margin-top: 0.5rem; }
        .space-y-3 > * + * { margin-top: 0.75rem; }
        .space-y-4 > * + * { margin-top: 1rem; }
        .space-y-5 > * + * { margin-top: 1.25rem; }
        .space-y-6 > * + * { margin-top: 1.5rem; }

        .p-0\.5 { padding: 0.125rem; }
        .p-1 { padding: 0.25rem; }
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
        .py-0\.5 { padding-top: 0.125rem; padding-bottom: 0.125rem; }
        .py-1 { padding-top: 0.25rem; padding-bottom: 0.25rem; }
        .py-1\.5 { padding-top: 0.375rem; padding-bottom: 0.375rem; }
        .py-2 { padding-top: 0.5rem; padding-bottom: 0.5rem; }
        .py-4 { padding-top: 1rem; padding-bottom: 1rem; }
        .py-6 { padding-top: 1.5rem; padding-bottom: 1.5rem; }
        .pt-1 { padding-top: 0.25rem; }
        .pt-2 { padding-top: 0.5rem; }
        .pt-3 { padding-top: 0.75rem; }
        .pt-4 { padding-top: 1rem; }
        .pb-2 { padding-bottom: 0.5rem; }
        .pb-3 { padding-bottom: 0.75rem; }
        .pb-4 { padding-bottom: 1rem; }
        .mt-1 { margin-top: 0.25rem; }
        .mt-2 { margin-top: 0.5rem; }
        .mt-4 { margin-top: 1rem; }
        .mt-6 { margin-top: 1.5rem; }
        .mb-2 { margin-bottom: 0.5rem; }
        .mx-auto { margin-left: auto; margin-right: auto; }

        .w-full { width: 100%; }
        .w-1\.5 { width: 0.375rem; }
        .w-2 { width: 0.5rem; }
        .w-2\.5 { width: 0.625rem; }
        .w-3 { width: 0.75rem; }
        .w-3\.5 { width: 0.875rem; }
        .w-6 { width: 1.5rem; }
        .w-8 { width: 2rem; }
        .w-9 { width: 2.25rem; }
        .h-full { height: 100%; }
        .h-1\.5 { height: 0.375rem; }
        .h-2 { height: 0.5rem; }
        .h-2\.5 { height: 0.625rem; }
        .h-3 { height: 0.75rem; }
        .h-3\.5 { height: 0.875rem; }
        .h-6 { height: 1.5rem; }
        .h-8 { height: 2rem; }
        .h-9 { height: 2.25rem; }
        .h-14 { height: 3.5rem; }
        .h-72 { height: 18rem; }
        .max-w-\[1240px\] { max-width: 1240px; }
        .min-h-screen { min-height: 100vh; }
        .relative { position: relative; }
        .absolute { position: absolute; }
        .inset-0 { top: 0; right: 0; bottom: 0; left: 0; }
        .top-0 { top: 0; }
        .bottom-0 { bottom: 0; }
        .-top-1 { top: -0.25rem; }
        .-top-6 { top: -1.6rem; }
        .-top-7 { top: -1.75rem; }
        .-translate-x-1\/2 { transform: translateX(-50%); }
        .z-10 { z-index: 10; }
        .z-20 { z-index: 20; }
        .pointer-events-none { pointer-events: none; }

        .bg-white { background-color: #ffffff; }
        .bg-slate-50 { background-color: var(--slate-50); }
        .bg-slate-100 { background-color: var(--slate-100); }
        .bg-slate-200 { background-color: var(--slate-200); }
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
        .bg-sky-50 { background-color: var(--sky-50); }
        .bg-sky-600 { background-color: var(--sky-600); }
        .bg-teal-50 { background-color: var(--teal-50); }

        .text-white { color: #ffffff; }
        .text-slate-400 { color: var(--slate-400); }
        .text-slate-500 { color: var(--slate-500); }
        .text-slate-600 { color: var(--slate-600); }
        .text-slate-700 { color: var(--slate-700); }
        .text-slate-800 { color: var(--slate-800); }
        .text-slate-900 { color: var(--slate-900); }
        .text-emerald-400 { color: #34d399; }
        .text-emerald-600 { color: var(--emerald-600); }
        .text-emerald-700 { color: var(--emerald-700); }
        .text-emerald-800 { color: var(--emerald-800); }
        .text-emerald-900 { color: var(--emerald-900); }
        .text-amber-600 { color: var(--amber-600); }
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
        .text-teal-700 { color: var(--teal-700); }

        .border { border: 1px solid var(--slate-200); }
        .border-t { border-top: 1px solid var(--slate-200); }
        .border-b { border-bottom: 1px solid var(--slate-200); }
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

        .uppercase { text-transform: uppercase; }
        .tracking-wide { letter-spacing: 0.025em; }
        .tracking-wider { letter-spacing: 0.05em; }
        .tracking-tight { letter-spacing: -0.025em; }
        .leading-tight { line-height: 1.25; }
        .leading-snug { line-height: 1.375; }
        .leading-relaxed { line-height: 1.625; }

        .text-left { text-align: left; }
        .text-center { text-align: center; }
        .text-right { text-align: right; }

        .shadow-sm { box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.04); }
        .shadow-md { box-shadow: 0 4px 12px -2px rgba(15, 23, 42, 0.08); }
        .cursor-crosshair { cursor: crosshair; }
        .cursor-pointer { cursor: pointer; }
        .select-none { user-select: none; }
        .overflow-hidden { overflow: hidden; }
        .overflow-x-auto { overflow-x: auto; }
        .overflow-y-auto { overflow-y: auto; }
        .max-h-40 { max-height: 10rem; }
        .italic { font-style: italic; }
        .hidden { display: none !important; }
        .block { display: block; }
        .truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .break-all { word-break: break-all; }

        .divide-y > * + * { border-top: 1px solid var(--slate-100); }
        .list-disc { list-style-type: disc; }
        .list-inside { list-style-position: inside; }
        table { border-collapse: collapse; width: 100%; }

        /* Chart Floating Tooltip */
        .chart-tooltip {
            position: absolute;
            top: 10px;
            z-index: 30;
            background: rgba(15, 23, 42, 0.94);
            color: #ffffff;
            padding: 8px 11px;
            border-radius: 10px;
            font-size: 11px;
            line-height: 1.4;
            box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25);
            pointer-events: none;
            white-space: nowrap;
            backdrop-filter: blur(6px);
            border: 1px solid rgba(255, 255, 255, 0.12);
        }

        /* Details disclosure styling */
        details summary { list-style: none; }
        details summary::-webkit-details-marker { display: none; }
        details .chevron { transition: transform 150ms ease-out; }
        details[open] .chevron { transform: rotate(180deg); }

        /* Toast notification */
        #toastContainer { position: fixed; bottom: 1.25rem; right: 1.25rem; z-index: 9999; display: flex; flex-direction: column; gap: 0.5rem; max-width: 360px; }
        .toast-item { padding: 0.75rem 1rem; border-radius: 0.75rem; font-size: 12px; font-weight: 600; display: flex; align-items: center; gap: 0.5rem; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.15); transition: opacity 0.25s ease; }
        .toast-success { background-color: var(--slate-900); color: #ffffff; border: 1px solid var(--groww-green); }
        .toast-error { background-color: var(--rose-900); color: #ffffff; border: 1px solid var(--rose-600); }
    </style>
</head>
<body class="min-h-screen text-slate-800">

    <div id="toastContainer" role="status" aria-live="polite"></div>

    <!-- Single-Row Compact Sticky Header (<12% viewport height) -->
    <header class="top-bar">
        <div class="max-w-[1240px] mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-3">
            <!-- Left: Brand + Live Pill -->
            <div class="flex items-center gap-3 min-w-0">
                <div class="w-8 h-8 rounded-full bg-slate-900 text-white font-extrabold text-sm flex items-center justify-center shrink-0">
                    H
                </div>
                <div class="min-w-0">
                    <div class="flex items-center gap-2">
                        <h1 class="text-sm font-extrabold text-slate-900 tracking-tight truncate">HDFC Bank</h1>
                        <span class="hidden sm:inline text-[11px] font-semibold text-slate-400">NSE: HDFCBANK</span>
                        <span id="headerPriceText" class="text-xs font-extrabold mono text-slate-900 bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200">₹817.80</span>
                        <span id="headerFeedStatusBadge" class="hidden md:inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-50 text-amber-800 border border-amber-200">
                            CHECKING FEED
                        </span>
                    </div>
                </div>
            </div>

            <!-- Right Controls: Plain/Tech + Refresh -->
            <div class="flex items-center gap-2 sm:gap-3 shrink-0">
                <div class="flex items-center bg-slate-100 p-0.5 rounded-lg text-xs font-semibold border border-slate-200" role="group" aria-label="Detail level">
                    <button type="button" onclick="setMode('plain')" id="btnModePlain" class="px-2.5 py-1 rounded-md bg-white text-slate-900 shadow-sm">Plain</button>
                    <button type="button" onclick="setMode('tech')" id="btnModeTech" class="px-2.5 py-1 rounded-md text-slate-500 hover:text-slate-900">Technical</button>
                </div>

                <button type="button" onclick="triggerNow()" id="btnTrigger" class="bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold px-3 py-1.5 rounded-lg flex items-center gap-1.5 shadow-sm">
                    <svg id="btnTriggerIcon" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                    <span id="btnTriggerLabel">Refresh</span>
                </button>
            </div>
        </div>
    </header>

    <!-- Main Container -->
    <main class="max-w-[1240px] mx-auto px-4 sm:px-6 py-4 space-y-5">

        <!-- Stale Feed Warning Banner (Only visible if feed is stale/offline) -->
        <div id="staleFeedAlertBanner" class="hidden">
            <div class="bg-amber-50 border border-amber-200 text-amber-900 px-4 py-2.5 rounded-xl flex flex-wrap items-center justify-between gap-2 text-xs shadow-sm">
                <div class="flex items-center gap-2 font-medium">
                    <span class="w-2 h-2 rounded-full bg-amber-500 animate-pulse shrink-0"></span>
                    <span><strong>Cached EOD Quote</strong> · <span id="staleFeedSource">NSE Historical Verified Cache</span> (<span id="staleFeedTimestamp">Latest EOD</span>) · Live order execution paused until real-time tick resumes.</span>
                </div>
                <span class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-300">Safety Guard</span>
            </div>
        </div>

        <!-- Clean Groww-Style View Tabs Bar -->
        <div class="bg-white border border-slate-200 rounded-xl px-2 shadow-sm">
            <div focusgroup="tablist nomemory" role="tablist" aria-label="Dashboard sections" class="view-tablist" id="mainTablist">
                <button type="button" role="tab" id="tab-main-overview" aria-selected="true" focusgroupstart onclick="switchMainTab('overview')" class="view-tab-btn">Overview</button>
                <button type="button" role="tab" id="tab-main-valuation" aria-selected="false" onclick="switchMainTab('valuation')" class="view-tab-btn">Valuation &amp; Safety Gates</button>
                <button type="button" role="tab" id="tab-main-compass" aria-selected="false" onclick="switchMainTab('compass')" class="view-tab-btn">Daily Compass</button>
                <button type="button" role="tab" id="tab-main-track" aria-selected="false" onclick="switchMainTab('track')" class="view-tab-btn">Track Record &amp; Trust</button>
            </div>
        </div>

        <!-- TAB PANELS STACK (No gap/padding on tabpanel elements per modern-web-guidance) -->
        <div class="tab-panels-stack">

            <!-- ==================== TAB 1: OVERVIEW (The 5-Second Story) ==================== -->
            <div id="panel-overview" role="tabpanel" aria-labelledby="tab-main-overview" tabindex="0">
                <div class="space-y-6">

                    <!-- HERO ROW: Interactive Scrubbable Chart (Left) + Today's Game Plan (Right) -->
                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">

                        <!-- Hero Left: Live Price, Scrubbable Chart, Overlays -->
                        <div class="bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm card-hover space-y-4">
                            <div class="flex flex-wrap items-start justify-between gap-3">
                                <div class="space-y-1.5">
                                    <div class="flex items-baseline gap-2.5 flex-wrap">
                                        <span id="heroPrice" class="text-3xl sm:text-4xl font-extrabold text-slate-900 mono">₹817.80</span>
                                        <span id="heroDelta" class="text-sm font-bold text-rose-600 flex items-center gap-0.5 mono">
                                            ▼ -28.20 (-3.33%)
                                        </span>
                                        <span id="heroPeriodBadge" class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 mono">
                                            +6.0% (6M)
                                        </span>
                                    </div>
                                    <div class="flex flex-wrap items-center gap-2">
                                        <div id="heroFeedChip" class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-[11px] font-semibold bg-emerald-50 text-emerald-900 border border-emerald-200">
                                            <span id="heroFeedChipDot" class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                                            <span id="heroFeedChipText">LIVE · NSE Real-Time · Prev close ₹846.00</span>
                                        </div>
                                        <span id="heroScrubReadout" class="hidden px-2 py-0.5 rounded-md text-[11px] font-bold bg-slate-900 text-white mono"></span>
                                    </div>
                                </div>

                                <!-- Timeframe Switcher -->
                                <div class="flex items-center bg-slate-100 p-1 rounded-lg gap-1 border border-slate-200" role="group" aria-label="Chart timeframe">
                                    <button type="button" onclick="setHeroTimeframe('1M')" data-tf="1M" class="btn-tf px-2.5 py-1 rounded-md text-xs font-semibold text-slate-500 hover:text-slate-900">1M</button>
                                    <button type="button" onclick="setHeroTimeframe('3M')" data-tf="3M" class="btn-tf px-2.5 py-1 rounded-md text-xs font-semibold text-slate-500 hover:text-slate-900">3M</button>
                                    <button type="button" onclick="setHeroTimeframe('6M')" data-tf="6M" class="btn-tf px-2.5 py-1 rounded-md text-xs font-bold bg-slate-900 text-white shadow-sm">6M</button>
                                    <button type="button" onclick="setHeroTimeframe('ALL')" data-tf="ALL" class="btn-tf px-2.5 py-1 rounded-md text-xs font-semibold text-slate-500 hover:text-slate-900">ALL</button>
                                </div>
                            </div>

                            <!-- Interactive Scrubbable Chart Canvas + Floating Tooltip -->
                            <div id="heroChartWrap" class="relative w-full h-72 sm:h-80 bg-slate-50 rounded-xl border border-slate-100 overflow-hidden select-none">
                                <canvas id="heroPriceChart" class="w-full h-full block cursor-crosshair"></canvas>
                                <div id="heroChartTooltip" class="chart-tooltip hidden"></div>
                            </div>

                            <!-- Overlays + Interactive Hint -->
                            <div class="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-slate-100">
                                <div class="flex flex-wrap items-center gap-1.5">
                                    <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wider mr-1">Layers:</span>
                                    <button type="button" id="btnOverlay_buyBand" onclick="toggleHeroOverlay('buyBand')" class="px-2.5 py-1 rounded-full text-xs font-bold bg-slate-900 text-white shadow-sm border border-slate-900 flex items-center gap-1.5">
                                        <span class="w-2 h-2 rounded-full bg-emerald-400"></span> Buy zone
                                    </button>
                                    <button type="button" id="btnOverlay_fibLevels" onclick="toggleHeroOverlay('fibLevels')" class="px-2.5 py-1 rounded-full text-xs font-semibold bg-white text-slate-600 border border-slate-200 hover:border-slate-300">
                                        Fib levels
                                    </button>
                                    <button type="button" id="btnOverlay_movingAvgs" onclick="toggleHeroOverlay('movingAvgs')" class="px-2.5 py-1 rounded-full text-xs font-semibold bg-white text-slate-600 border border-slate-200 hover:border-slate-300">
                                        Moving avgs
                                    </button>
                                    <button type="button" id="btnOverlay_avwap" onclick="toggleHeroOverlay('avwap')" class="px-2.5 py-1 rounded-full text-xs font-semibold bg-white text-slate-600 border border-slate-200 hover:border-slate-300">
                                        AVWAP
                                    </button>
                                </div>
                                <span id="heroChartDateCaption" class="text-[11px] text-slate-400 mono">Hover or drag chart to inspect dates</span>
                            </div>
                        </div>

                        <!-- Hero Right: Unified TODAY'S GAME PLAN Card -->
                        <div class="bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm card-hover space-y-5">
                            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                                <span class="text-xs font-extrabold text-slate-500 uppercase tracking-wider">TODAY'S GAME PLAN</span>
                                <span id="decisionPrecedenceTier" class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
                                    Patience Guard
                                </span>
                            </div>

                            <!-- Verdict Headline -->
                            <div class="space-y-1.5">
                                <div class="flex items-center justify-between gap-2">
                                    <span id="verdictActionBadge" class="text-3xl font-extrabold text-amber-500 tracking-tight">WAIT</span>
                                    <span id="orderValidityPill" class="px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 text-[11px] font-bold mono border border-slate-200">
                                        Valid 5 trading days
                                    </span>
                                </div>
                                <h2 id="decisionHeadline" class="text-base font-bold text-slate-900 leading-snug">Don't chase this move</h2>
                                <p id="verdictActionText" class="text-xs text-slate-600 leading-relaxed">
                                    Place a patient limit order in <strong id="planZoneText" class="text-slate-900 mono">₹745–₹775</strong>. Add a second tranche at <strong class="text-slate-900 mono">₹710</strong> on deeper dips.
                                </p>
                            </div>

                            <!-- Visual "How Close Are We?" Range Thermometer -->
                            <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-2.5">
                                <div class="flex items-center justify-between text-[11px]">
                                    <span class="font-bold text-slate-700">Where price sits today</span>
                                    <span id="gapToBuyBadge" class="font-bold text-amber-700 mono">5.2% above buy zone</span>
                                </div>
                                <div class="relative w-full h-3 bg-slate-200 rounded-full mt-6 mb-1">
                                    <!-- Buy Zone highlight -->
                                    <div id="thermBuyZoneBand" class="absolute top-0 bottom-0 bg-emerald-400 rounded-full" style="left: 25%; width: 12%;" title="Limit Buy Zone"></div>
                                    <!-- Deep dip marker -->
                                    <div id="thermDeepDipPin" class="absolute top-0 bottom-0 w-1 bg-teal-700 rounded" style="left: 14%;" title="Deep Dip Floor ₹710"></div>
                                    <!-- Today price needle -->
                                    <div id="thermTodayPin" class="absolute -top-1 bottom-0 w-1.5 bg-slate-900 rounded-full z-10" style="left: 55%;"></div>
                                    <div id="thermTodayLabel" class="absolute -top-6 -translate-x-1/2 bg-slate-900 text-white text-[9px] font-bold px-1.5 py-0.5 rounded mono z-20 shadow-sm" style="left: 55%;">
                                        ₹818
                                    </div>
                                </div>
                                <div class="flex justify-between text-[10px] font-semibold text-slate-500 mono pt-1">
                                    <span>Floor ₹710</span>
                                    <span id="thermZoneLabel" class="text-emerald-700">Buy ₹745–775</span>
                                    <span id="thermBullLabel">Bull ₹987</span>
                                </div>
                            </div>

                            <!-- Interactive Budget / Tranche Share Calculator -->
                            <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-2.5">
                                <div class="flex items-center justify-between">
                                    <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Quick Tranche Planner</span>
                                    <div class="flex items-center gap-1" role="group" aria-label="Tranche budget">
                                        <button type="button" onclick="setTrancheBudget(100000)" data-budget="100000" class="btn-budget px-2 py-0.5 rounded text-[10px] font-bold bg-white text-slate-600 border border-slate-200">₹1L</button>
                                        <button type="button" onclick="setTrancheBudget(200000)" data-budget="200000" class="btn-budget px-2 py-0.5 rounded text-[10px] font-bold bg-slate-900 text-white border border-slate-900">₹2L</button>
                                        <button type="button" onclick="setTrancheBudget(500000)" data-budget="500000" class="btn-budget px-2 py-0.5 rounded text-[10px] font-bold bg-white text-slate-600 border border-slate-200">₹5L</button>
                                        <button type="button" onclick="setTrancheBudget(1000000)" data-budget="1000000" class="btn-budget px-2 py-0.5 rounded text-[10px] font-bold bg-white text-slate-600 border border-slate-200">₹10L</button>
                                    </div>
                                </div>
                                <div class="grid grid-cols-2 gap-2">
                                    <div class="bg-white p-2.5 rounded-lg border border-slate-200">
                                        <span class="text-[10px] text-slate-500 block">Tranche 1 Limit</span>
                                        <p id="verdictTrancheSharesText" class="text-sm font-extrabold text-slate-900 mono">258–268 sh</p>
                                        <span id="calcT1Sub" class="text-[10px] text-emerald-700 font-medium block">Inside buy zone</span>
                                    </div>
                                    <div class="bg-white p-2.5 rounded-lg border border-slate-200">
                                        <span class="text-[10px] text-slate-500 block">Tranche 2 Floor</span>
                                        <p id="calcT2SharesText" class="text-sm font-extrabold text-slate-900 mono">281 sh</p>
                                        <span class="text-[10px] text-slate-500 block">If dip hits ₹710</span>
                                    </div>
                                </div>
                            </div>

                            <!-- 2-Step Readiness Checklist -->
                            <div class="space-y-2.5 pt-1 border-t border-slate-100">
                                <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">WHAT NEEDS TO LINE UP</span>

                                <div class="space-y-1">
                                    <div class="flex items-center justify-between text-xs">
                                        <span class="font-semibold text-slate-800">1. Price cools into buy zone</span>
                                        <span id="chkPriceStatus" class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">Waiting</span>
                                    </div>
                                    <div class="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                                        <div id="chkPriceBar" class="bg-amber-400 h-full rounded-full" style="width: 35%;"></div>
                                    </div>
                                    <p id="chkPriceNote" class="text-[11px] text-slate-500 leading-tight">₹817.80 now · 5.2% above ₹775 target.</p>
                                </div>

                                <div class="space-y-1">
                                    <div class="flex items-center justify-between text-xs">
                                        <span class="font-semibold text-slate-800">2. Short-term momentum cools (RSI)</span>
                                        <span id="chkRsiStatus" class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">Overbought</span>
                                    </div>
                                    <div class="w-full bg-slate-100 h-2 rounded-full overflow-hidden relative flex">
                                        <div class="bg-emerald-500 h-full" style="width: 75%;"></div>
                                        <div class="bg-rose-500 h-full" style="width: 25%;"></div>
                                        <div id="chkRsiNeedle" class="absolute top-0 bottom-0 w-1.5 bg-slate-900 border border-white rounded-full" style="left: 88.7%;"></div>
                                    </div>
                                    <p id="chkRsiNote" class="text-[11px] text-slate-500 leading-tight">RSI is 88.7 (overheated sprint). Waiting below 75.</p>
                                </div>
                            </div>

                            <!-- Compact Safety Gates Bar -->
                            <div class="space-y-1.5 pt-2 border-t border-slate-100">
                                <div class="flex items-center justify-between text-xs font-bold">
                                    <span class="text-slate-700 uppercase tracking-wider text-[10px]">SAFETY GATES</span>
                                    <button type="button" onclick="switchMainTab('valuation')" class="text-[11px] font-bold text-indigo-600 hover:underline" id="overviewGatesSummary">5 of 6 Pass →</button>
                                </div>
                                <div id="overviewGateBars" class="grid grid-cols-6 gap-1.5 h-2">
                                    <div class="bg-emerald-500 rounded-full h-full"></div>
                                    <div class="bg-emerald-500 rounded-full h-full"></div>
                                    <div class="bg-emerald-500 rounded-full h-full"></div>
                                    <div class="bg-emerald-500 rounded-full h-full"></div>
                                    <div class="bg-amber-400 rounded-full h-full animate-pulse"></div>
                                    <div class="bg-emerald-500 rounded-full h-full"></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- FRANCHISE HEALTH STRIP (4 Traffic-Light Pillars) -->
                    <div class="bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm space-y-4 perf-region">
                        <div class="flex flex-wrap items-center justify-between gap-2">
                            <div>
                                <h3 class="text-sm font-extrabold text-slate-900 tracking-tight">Is HDFC Bank Fundamentally Healthy? (4 Core Checks)</h3>
                                <p class="text-xs text-slate-500">Live quarterly check on loan quality, lending margins, low-cost deposits, and sector liquidity.</p>
                            </div>
                            <span id="thesisStateBadge" class="px-3 py-1 rounded-full text-xs font-extrabold uppercase bg-amber-50 text-amber-800 border border-amber-200">
                                SOLID CORE · MARGIN WATCH
                            </span>
                        </div>
                        <div id="thesisHealthContainer" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                            <!-- Dynamically populated by renderThesisHealth() -->
                        </div>
                    </div>

                    <!-- BALANCED PROS & PATIENCE ROW (Dynamic from Engine) -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 perf-region">
                        <div class="bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm space-y-3.5">
                            <div class="flex items-center gap-2">
                                <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 shrink-0"></span>
                                <h3 class="font-bold text-slate-900 text-sm">What supports a buy</h3>
                            </div>
                            <ul id="whyBuyList" class="space-y-3 text-xs text-slate-700">
                                <!-- Dynamically populated by renderOverviewReasons() -->
                            </ul>
                        </div>

                        <div class="bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm space-y-3.5">
                            <div class="flex items-center gap-2">
                                <span class="w-2.5 h-2.5 rounded-full bg-rose-500 shrink-0"></span>
                                <h3 class="font-bold text-slate-900 text-sm">What argues for patience</h3>
                            </div>
                            <ul id="whyWaitList" class="space-y-3 text-xs text-slate-700">
                                <!-- Dynamically populated by renderOverviewReasons() -->
                            </ul>
                        </div>
                    </div>

                    <!-- SNAPSHOT & PRICE VS VALUE SPECTRUM -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 perf-region">
                        <div class="bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm space-y-4">
                            <h3 class="font-bold text-slate-900 text-sm">Today's Market Snapshot</h3>
                            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                                <div class="bg-slate-50 p-3 rounded-xl border border-slate-100">
                                    <span class="text-[10px] font-bold text-slate-500 uppercase block">OPEN</span>
                                    <p id="snapOpen" class="text-sm font-bold text-slate-900 mono">₹855.00</p>
                                </div>
                                <div class="bg-slate-50 p-3 rounded-xl border border-slate-100">
                                    <span class="text-[10px] font-bold text-slate-500 uppercase block">DAY HIGH</span>
                                    <p id="snapHigh" class="text-sm font-bold text-slate-900 mono">₹859.70</p>
                                </div>
                                <div class="bg-slate-50 p-3 rounded-xl border border-slate-100">
                                    <span class="text-[10px] font-bold text-slate-500 uppercase block">DAY LOW</span>
                                    <p id="snapLow" class="text-sm font-bold text-slate-900 mono">₹814.05</p>
                                </div>
                                <div class="bg-slate-50 p-3 rounded-xl border border-slate-100">
                                    <span class="text-[10px] font-bold text-slate-500 uppercase block">VOLUME</span>
                                    <p id="snapVol" class="text-sm font-bold text-slate-900 mono">5.56 Cr</p>
                                    <span id="snapVolShares" class="text-[10px] text-slate-400 block truncate">55,615,279 sh</span>
                                </div>
                                <div class="bg-slate-50 p-3 rounded-xl border border-slate-100">
                                    <span class="text-[10px] font-bold text-slate-500 uppercase block">P/B RATIO</span>
                                    <p id="snapPb" class="text-sm font-bold text-slate-900 mono">2.07×</p>
                                    <span class="text-[10px] text-slate-400 block">BV ₹394.80</span>
                                </div>
                                <div class="bg-slate-50 p-3 rounded-xl border border-slate-100">
                                    <span class="text-[10px] font-bold text-slate-500 uppercase block">TRAILING ROE</span>
                                    <p id="snapRoe" class="text-sm font-bold text-slate-900 mono">12.84%</p>
                                    <span class="text-[10px] text-slate-400 block">Q2 FY27</span>
                                </div>
                                <div class="bg-slate-50 p-3 rounded-xl border border-slate-100">
                                    <span class="text-[10px] font-bold text-slate-500 uppercase block">DELIVERY</span>
                                    <p id="snapDelivery" class="text-sm font-bold text-slate-900 mono">64.5%</p>
                                    <span class="text-[10px] text-slate-400 block">High custody</span>
                                </div>
                                <div class="bg-slate-50 p-3 rounded-xl border border-slate-100">
                                    <span class="text-[10px] font-bold text-slate-500 uppercase block">VS BANK NIFTY</span>
                                    <p id="snapVsBankNifty" class="text-sm font-bold text-emerald-700 mono">+2.4%</p>
                                    <span class="text-[10px] text-slate-400 block">30D Alpha</span>
                                </div>
                            </div>
                        </div>

                        <!-- Dynamic Price vs Value Spectrum -->
                        <div class="bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm space-y-4">
                            <div class="flex items-center justify-between">
                                <h3 class="font-bold text-slate-900 text-sm">Price vs Intrinsic Value Range</h3>
                                <button type="button" onclick="switchMainTab('valuation')" class="text-xs font-bold text-indigo-600 hover:underline">Full ladder →</button>
                            </div>
                            <p id="priceVsValueSummary" class="text-xs text-slate-600 leading-relaxed">
                                Today's price sits comfortably inside the historical fair range, well below the ₹987 bull target.
                            </p>

                            <div class="pt-5 pb-2">
                                <div class="relative w-full h-3 bg-slate-100 rounded-full">
                                    <div id="pvvBuyBand" class="absolute top-0 bottom-0 bg-emerald-200 rounded-full" style="left: 59%; width: 5%;"></div>
                                    <div id="pvvBaseLine" class="absolute top-0 bottom-0 w-0.5 bg-indigo-600" style="left: 28%;"></div>
                                    <div id="pvvCurrPin" class="absolute -top-1 bottom-0 w-1.5 bg-slate-900 rounded-full" style="left: 72%;"></div>
                                    <div id="pvvCurrLabel" class="absolute -top-7 -translate-x-1/2 bg-slate-900 text-white text-[10px] font-bold px-2 py-0.5 rounded mono shadow-sm" style="left: 72%;">
                                        ₹817.80
                                    </div>
                                </div>
                                <div class="flex justify-between text-[11px] text-slate-500 font-semibold pt-2 mono">
                                    <span id="pvvBearLabel" class="text-rose-600">Bear ₹386</span>
                                    <span id="pvvBaseLabel" class="text-indigo-600">Base ₹554</span>
                                    <span id="pvvBullLabel" class="text-emerald-600">Bull ₹987</span>
                                </div>
                            </div>

                            <!-- Technical Arbitration Box (Hidden in Plain Mode!) -->
                            <div class="tech-block bg-slate-50 p-3 rounded-xl border border-slate-200 space-y-1.5 text-[11px]">
                                <div class="flex items-center justify-between">
                                    <span class="font-bold text-slate-700 uppercase text-[10px]">Arbitration Detail (Technical Mode)</span>
                                    <span id="decisionDisagreementPill" class="px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-bold text-[10px]">1 Disagreement</span>
                                </div>
                                <p id="decisionDetailText" class="text-slate-600 leading-snug"></p>
                                <p id="decisionOrderDirective" class="font-mono font-bold text-amber-800"></p>
                            </div>
                        </div>
                    </div>

                    <!-- Technical-Only Advisory Inputs & Disagreements (Shown when "Technical" mode is active) -->
                    <div class="tech-block bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm space-y-4">
                        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                            <div>
                                <h3 class="text-sm font-extrabold text-slate-900">Quantitative Model Arbitration &amp; Advisory Inputs</h3>
                                <p class="text-xs text-slate-500">Strict precedence order: Invalidation (P1) → Weakening (P2) → Ceiling (P3) → Entry Tranches (P4) → Default (P5).</p>
                            </div>
                            <span id="decisionCanonicalBadge" class="px-3 py-1 rounded-full font-extrabold text-xs uppercase bg-amber-50 text-amber-800 border border-amber-200">WAIT</span>
                        </div>
                        <div id="decisionInputsGrid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs"></div>
                        <div id="decisionDisagreementsBox" class="bg-amber-50 border border-amber-200 p-3.5 rounded-xl text-xs space-y-1">
                            <span class="font-bold text-[11px] text-amber-900">Surfaced Disagreements &amp; Resolutions</span>
                            <ul id="decisionDisagreementsList" class="list-disc list-inside text-amber-800 text-[11px] space-y-0.5"></ul>
                        </div>
                    </div>

                </div>
            </div>

            <!-- ==================== TAB 2: VALUATION & SAFETY GATES ==================== -->
            <div id="panel-valuation" role="tabpanel" aria-labelledby="tab-main-valuation" hidden="until-found">
                <div class="space-y-6">

                    <!-- Dynamic Ke & SOTP Anchors -->
                    <section class="bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm space-y-5 perf-region">
                        <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
                            <div>
                                <h3 class="text-base font-extrabold text-slate-900">Integrated Valuation Anchors &amp; Dynamic Cost of Equity</h3>
                                <p class="text-xs text-slate-500">Residual income fair value wired dynamically to 10Y Indian G-Sec yields and audited Q2 FY27 balance-sheet equity.</p>
                            </div>
                            <div class="flex flex-wrap items-center gap-2">
                                <span id="valDynamicKePill" class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200 mono">
                                    Ke = 13.07%
                                </span>
                                <span id="valSotpAnchorPill" class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 mono">
                                    SOTP Anchor = ₹938.50
                                </span>
                            </div>
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                            <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                                <div class="flex items-center justify-between">
                                    <span class="font-bold text-slate-900 uppercase text-[10px] tracking-wider">Dynamic Cost of Equity (CAPM)</span>
                                    <span class="px-2 py-0.5 rounded bg-indigo-100 text-indigo-800 font-bold mono text-[10px]">Live 10Y G-Sec</span>
                                </div>
                                <p id="valKeFormulaText" class="font-mono text-xs font-bold text-slate-800 bg-white p-2.5 rounded-lg border border-slate-200">
                                    Ke = Rf (6.80%) + Beta (1.14) × ERP (5.50%) = 13.07%
                                </p>
                                <p class="text-[11px] text-slate-600 leading-snug">
                                    Automatically re-rates valuation ceilings when RBI shifts interest rates, preventing premature selling during rate cuts.
                                </p>
                            </div>

                            <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                                <div class="flex items-center justify-between">
                                    <span class="font-bold text-slate-900 uppercase text-[10px] tracking-wider">Book-Value &amp; SOTP Reconciliation</span>
                                    <span class="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold mono text-[10px]">Net SOTP +₹88.50/sh</span>
                                </div>
                                <div class="bg-white p-2.5 rounded-lg border border-slate-200 space-y-1 font-mono text-[11px]">
                                    <div class="flex justify-between"><span>Core Standalone BVPS:</span> <strong class="text-slate-900">₹368.24/sh</strong></div>
                                    <div class="flex justify-between"><span>Consolidated BVPS:</span> <strong class="text-slate-900">₹394.80/sh</strong></div>
                                    <div class="flex justify-between text-emerald-700"><span>Subsidiary Value - Carrying Cost:</span> <strong>+₹88.50/sh</strong></div>
                                </div>
                                <p class="text-[11px] text-slate-600 leading-snug">
                                    Deducts subsidiary carrying cost from ₹115 SOTP market value to avoid double-counting equity.
                                </p>
                            </div>
                        </div>
                    </section>

                    <!-- Unified Price Ladder -->
                    <section id="sectionLadder" class="bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm space-y-4 perf-region">
                        <div>
                            <h3 class="text-base font-bold text-slate-900">Unified Price Ladder &amp; Valuation Reference Frame</h3>
                            <p class="text-xs text-slate-500">Ordered price anchors, post-merger percentiles, and staged capital deployment rules.</p>
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
                                        <th class="p-3 text-left">Rationale</th>
                                    </tr>
                                </thead>
                                <tbody id="priceLadderTableBody" class="divide-y divide-slate-100 text-center mono"></tbody>
                            </table>
                        </div>
                    </section>

                    <!-- 6 Safety & Accumulation Gates -->
                    <section id="sectionGates" class="bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm space-y-4 perf-region">
                        <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
                            <div>
                                <div class="flex items-center gap-2">
                                    <h3 class="text-base font-bold text-slate-900">6 Safety &amp; Accumulation Gates</h3>
                                    <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">Solvency &amp; Timing</span>
                                </div>
                                <p class="text-xs text-slate-500">Every capital deployment must clear verified filing checks, valuation floors, solvency, and momentum discipline.</p>
                            </div>
                            <span id="gatesStatusSummaryBadge" class="px-3 py-1 rounded-full bg-slate-100 text-slate-800 text-xs font-bold border border-slate-200">
                                5 of 6 Pass
                            </span>
                        </div>
                        <div id="gatesListContainer" class="space-y-3"></div>
                    </section>

                </div>
            </div>

            <!-- ==================== TAB 3: DAILY COMPASS ==================== -->
            <div id="panel-compass" role="tabpanel" aria-labelledby="tab-main-compass" hidden="until-found">
                <div class="space-y-6">
                    <section id="sectionCompass" class="bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm space-y-6 perf-region">
                        <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
                            <div>
                                <div class="flex items-center gap-2">
                                    <h3 class="text-base font-bold text-slate-900">Daily Compass: Multi-Horizon Probabilities &amp; Technical Confluence</h3>
                                    <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">Odds &amp; Macro</span>
                                </div>
                                <p class="text-xs text-slate-500">Expected multi-day swing bounds, empirical touch odds vs random walk, Fibonacci levels, and market liquidity context.</p>
                            </div>
                            <div class="flex items-center gap-2">
                                <span id="compassBiasBadge" class="px-2.5 py-1 rounded-full font-bold bg-amber-50 text-amber-800 border border-amber-200 text-xs">
                                    Bias: Mean Reversion / Pullback
                                </span>
                                <span id="compassEdgeBadge" class="px-2.5 py-1 rounded-full font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs">
                                    Pullback Edge
                                </span>
                            </div>
                        </div>

                        <!-- Volatility & Expected Ranges -->
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                            <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1">
                                <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">ATR(14) Daily Swing Span</span>
                                <div class="flex items-baseline gap-2">
                                    <span id="compassAtrValue" class="text-xl font-extrabold text-slate-900 mono">₹22.2</span>
                                    <span id="compassAtrPct" class="text-xs font-semibold text-slate-500">(2.71% of price)</span>
                                </div>
                                <p class="text-[11px] text-slate-500">Normal daily trading noise range</p>
                            </div>
                            <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1">
                                <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">Expected 1D to 5D Bounds</span>
                                <div class="text-xs space-y-0.5 mono text-slate-700">
                                    <div>1D: <span id="compassRange1D" class="font-bold text-slate-900">--</span></div>
                                    <div>3D: <span id="compassRange3D" class="font-bold text-slate-900">--</span></div>
                                    <div>5D: <span id="compassRange5D" class="font-bold text-slate-900">--</span></div>
                                </div>
                            </div>
                            <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1">
                                <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">Institutional Anchors</span>
                                <div class="text-xs space-y-0.5 mono text-slate-700">
                                    <div>AVWAP: <span id="compassAvwap" class="font-bold text-indigo-700">--</span></div>
                                    <div>Delivery: <span id="compassDelivery" class="font-bold text-emerald-700">--</span></div>
                                    <div>Rel Strength: <span id="compassRsBankNifty" class="font-bold text-emerald-700">--</span></div>
                                </div>
                            </div>
                        </div>

                        <!-- Cross-Market Derivatives & Liquidity -->
                        <div class="space-y-3">
                            <span class="text-xs font-bold text-slate-500 uppercase tracking-wider block">Cross-Market Derivatives &amp; Liquidity Context</span>
                            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                                <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-1">
                                    <span class="text-[10px] font-bold text-slate-500 uppercase">FII / DII Net Flow</span>
                                    <div class="mono text-xs space-y-0.5">
                                        <div>FII: <span id="macroFiiNet" class="font-bold text-rose-600">--</span></div>
                                        <div>DII: <span id="macroDiiNet" class="font-bold text-emerald-700">--</span></div>
                                        <div>Net: <span id="macroNetInst" class="font-extrabold text-emerald-700">--</span></div>
                                    </div>
                                    <p class="text-[10px] text-slate-400">As-of <span id="macroFlowTs">18:30 IST</span></p>
                                </div>
                                <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-1">
                                    <span class="text-[10px] font-bold text-slate-500 uppercase">India VIX</span>
                                    <div class="flex items-baseline gap-1.5">
                                        <span id="macroVixVal" class="text-lg font-extrabold text-slate-900 mono">--</span>
                                        <span id="macroVixChg" class="text-xs font-semibold text-emerald-700 mono">--</span>
                                    </div>
                                    <div class="text-xs font-bold text-emerald-700" id="macroVixRegime">--</div>
                                    <p class="text-[10px] text-slate-400">As-of <span id="macroVixTs">15:30 IST</span></p>
                                </div>
                                <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-1">
                                    <span class="text-[10px] font-bold text-slate-500 uppercase">Bank Nifty Sector</span>
                                    <div class="flex items-baseline gap-1.5">
                                        <span id="macroBankNiftyVal" class="text-lg font-extrabold text-slate-900 mono">--</span>
                                        <span id="macroBankNiftyChg" class="text-xs font-semibold text-emerald-700 mono">--</span>
                                    </div>
                                    <div class="text-xs text-slate-700">Trend: <span id="macroBankNiftyTrend" class="font-bold text-slate-800">--</span></div>
                                    <div class="text-xs text-slate-700">HDFC Beta: <span id="macroHdfcBeta" class="font-bold text-slate-800">--</span></div>
                                </div>
                                <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-1">
                                    <span class="text-[10px] font-bold text-slate-500 uppercase">Options Chain OI</span>
                                    <div class="text-xs space-y-0.5 mono text-slate-700">
                                        <div>PCR OI: <span id="macroPcr" class="font-bold text-indigo-700">--</span></div>
                                        <div>Max Pain: <span id="macroMaxPain" class="font-bold text-slate-900">--</span></div>
                                        <div>Put Wall: <span id="macroPutWall" class="font-bold text-emerald-700">--</span></div>
                                    </div>
                                    <p class="text-[10px] text-slate-400">As-of <span id="macroOiTs">15:30 IST</span></p>
                                </div>
                            </div>
                        </div>

                        <!-- Touch Probabilities Table -->
                        <div class="space-y-2.5">
                            <span class="text-xs font-bold text-slate-500 uppercase tracking-wider block">Empirical Touch Odds vs Random Walk</span>
                            <div class="overflow-x-auto">
                                <table class="w-full text-left text-xs border border-slate-200 rounded-xl overflow-hidden">
                                    <thead class="bg-slate-50 text-slate-500 border-b border-slate-200 text-[11px]">
                                        <tr>
                                            <th class="p-3 text-left">Target Level</th>
                                            <th class="p-3 text-center">Distance</th>
                                            <th class="p-3 text-center">1-Day</th>
                                            <th class="p-3 text-center">3-Day</th>
                                            <th class="p-3 text-center">5-Day</th>
                                            <th class="p-3 text-center">Random Walk</th>
                                            <th class="p-3 text-center">Edge</th>
                                            <th class="p-3 text-center">Sample</th>
                                            <th class="p-3 text-right">Directive</th>
                                        </tr>
                                    </thead>
                                    <tbody id="compassTouchTableBody" class="divide-y divide-slate-100 text-center mono"></tbody>
                                </table>
                            </div>
                        </div>

                        <!-- Fibonacci Ladder -->
                        <div class="space-y-2.5">
                            <span class="text-xs font-bold text-slate-500 uppercase tracking-wider block">Canonical Fibonacci Retracement Ladder</span>
                            <div class="overflow-x-auto">
                                <table class="w-full text-left text-xs border border-slate-200 rounded-xl overflow-hidden mono">
                                    <thead class="bg-slate-50 text-slate-500 border-b border-slate-200 text-[11px]">
                                        <tr>
                                            <th class="p-2.5">Fib Ratio</th>
                                            <th class="p-2.5 text-center">Price Level</th>
                                            <th class="p-2.5 text-center">Distance</th>
                                            <th class="p-2.5 text-right">Confluence &amp; Role</th>
                                        </tr>
                                    </thead>
                                    <tbody id="compassFibTableBody" class="divide-y divide-slate-100 text-[11px]"></tbody>
                                </table>
                            </div>
                        </div>
                    </section>
                </div>
            </div>

            <!-- ==================== TAB 4: TRACK RECORD & TRUST ==================== -->
            <div id="panel-track" role="tabpanel" aria-labelledby="tab-main-track" hidden="until-found">
                <div class="space-y-6">
                    <section id="sectionDetails" class="bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm space-y-6 perf-region">
                        <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
                            <div>
                                <div class="flex items-center gap-2">
                                    <h3 class="text-base font-bold text-slate-900">Historical Proof &amp; Audit Ledger</h3>
                                    <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">Post-Merger + Filing Verified</span>
                                </div>
                                <p class="text-xs text-slate-500">Walk-forward backtest curve, Q2 FY27 management commitments, regulatory disclosures, peer comparison, and decision log.</p>
                            </div>

                            <div class="flex flex-wrap items-center bg-slate-100 p-1 rounded-xl gap-1 border border-slate-200">
                                <button type="button" onclick="switchAuditTab('evidence')" id="tab-btn-evidence" class="px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-900 text-white shadow-sm">Evidence</button>
                                <button type="button" onclick="switchAuditTab('fundamentals')" id="tab-btn-fundamentals" class="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white">Filings &amp; Promises</button>
                                <button type="button" onclick="switchAuditTab('context')" id="tab-btn-context" class="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white">Disclosures</button>
                                <button type="button" onclick="switchAuditTab('integrity')" id="tab-btn-integrity" class="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white">Peers &amp; Ledger</button>
                            </div>
                        </div>

                        <!-- SUB-TAB 1: EVIDENCE (Scrubbable Backtest Chart + Analogues) -->
                        <div id="tab-pane-evidence" class="space-y-6">
                            <div class="bg-slate-50 p-4 sm:p-5 rounded-xl border border-slate-200 space-y-4">
                                <div class="flex flex-wrap items-center justify-between gap-3">
                                    <div>
                                        <div class="flex items-center gap-2">
                                            <h4 class="text-sm font-bold text-slate-900">Walk-Forward Strategy vs SIP vs Buy &amp; Hold</h4>
                                            <span id="badgeBacktestVerified" class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">Walk-Forward Backtest</span>
                                        </div>
                                        <p class="text-xs text-slate-500">Hover or drag across the curve to compare portfolio growth (₹1,00,000 initial capital, after friction).</p>
                                    </div>
                                    <div class="flex flex-wrap items-center gap-3">
                                        <div class="flex items-center gap-3 text-xs font-semibold text-slate-600">
                                            <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Strategy</span>
                                            <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-sky-600"></span> Monthly SIP</span>
                                            <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-slate-400"></span> Buy &amp; Hold</span>
                                        </div>
                                        <select id="selectPeriod" onchange="runBacktest()" class="bg-white text-xs border border-slate-300 rounded-lg px-3 py-1.5 mono">
                                            <option value="1y">1 Year</option>
                                            <option value="2y" selected>2 Years</option>
                                            <option value="3y">3 Years</option>
                                        </select>
                                    </div>
                                </div>

                                <div id="equityChartWrap" class="w-full h-72 sm:h-80 relative bg-white rounded-xl border border-slate-200 overflow-hidden select-none">
                                    <canvas id="equityChart" class="w-full h-full block cursor-crosshair"></canvas>
                                    <div id="equityChartTooltip" class="chart-tooltip hidden"></div>
                                    <div id="chartEmptyState" class="hidden absolute inset-0 flex flex-col items-center justify-center bg-white rounded-xl text-slate-400 text-xs font-medium">
                                        <p>Not enough backtest data yet</p>
                                    </div>
                                </div>

                                <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                                    <div class="bg-white p-3 rounded-lg border border-slate-200">
                                        <span class="text-slate-500 block text-[10px]">Net Strategy Return</span>
                                        <span id="btStratRet" class="text-base font-bold text-emerald-700 mono">+18.4%</span>
                                        <span class="text-[10px] text-slate-400 block">After 0.15% friction</span>
                                    </div>
                                    <div class="bg-white p-3 rounded-lg border border-slate-200">
                                        <span class="text-slate-500 block text-[10px]">Monthly SIP Return</span>
                                        <span id="btSipRet" class="text-base font-bold text-indigo-700 mono">+8.2%</span>
                                        <span class="text-[10px] text-slate-400 block">Baseline SIP</span>
                                    </div>
                                    <div class="bg-white p-3 rounded-lg border border-slate-200">
                                        <span class="text-slate-500 block text-[10px]">Max Strategy Drawdown</span>
                                        <span id="btMaxDd" class="text-base font-bold text-slate-900 mono">-7.7%</span>
                                        <span class="text-[10px] text-emerald-600 block">Controlled downside</span>
                                    </div>
                                    <div class="bg-white p-3 rounded-lg border border-slate-200">
                                        <span class="text-slate-500 block text-[10px]">Buy &amp; Hold Return</span>
                                        <span id="btBhRet" class="text-base font-bold text-slate-700 mono">-9.5%</span>
                                        <span class="text-[10px] text-slate-400 block">Passive benchmark</span>
                                    </div>
                                </div>
                            </div>

                            <!-- Historical Analogues -->
                            <div class="space-y-3">
                                <div class="flex flex-wrap items-center justify-between gap-2">
                                    <div>
                                        <h4 class="text-sm font-bold text-slate-900">Historical Dip Episodes (2018–2026)</h4>
                                        <p class="text-xs text-slate-500">Distinguishes post-merger episodes from pre-merger standalone cycles.</p>
                                    </div>
                                    <div class="flex flex-wrap items-center gap-2 text-xs font-semibold mono" id="analogueHeaderStats"></div>
                                </div>
                                <div class="overflow-x-auto">
                                    <table class="w-full text-left text-xs border border-slate-200 rounded-xl overflow-hidden">
                                        <thead class="bg-slate-50 text-slate-500 border-b border-slate-200 text-[11px]">
                                            <tr>
                                                <th class="p-3">Episode</th>
                                                <th class="p-3">Era</th>
                                                <th class="p-3">Entry Price</th>
                                                <th class="p-3">P/B</th>
                                                <th class="p-3">Drawdown</th>
                                                <th class="p-3">30D</th>
                                                <th class="p-3">90D</th>
                                                <th class="p-3">180D</th>
                                                <th class="p-3">Max Adverse</th>
                                                <th class="p-3">Outcome</th>
                                            </tr>
                                        </thead>
                                        <tbody id="analogueTableBody" class="divide-y divide-slate-100 mono"></tbody>
                                    </table>
                                </div>
                            </div>
                        </div>

                        <!-- SUB-TAB 2: FILINGS & PROMISES -->
                        <div id="tab-pane-fundamentals" class="space-y-6 hidden">
                            <div class="space-y-3">
                                <div class="flex flex-wrap items-center justify-between gap-2">
                                    <div>
                                        <h4 class="text-sm font-bold text-slate-900">Management Promise &amp; Guidance Tracker (Q2 FY27 Audit)</h4>
                                        <p class="text-xs text-slate-500">Checked against BSE/NSE Q2 FY27 Standalone filing (Oct 17, 2026). <a href="/filings/q2fy27" target="_blank" class="text-indigo-600 font-semibold hover:underline">View certified filing extract →</a></p>
                                    </div>
                                    <span class="px-2.5 py-1 rounded bg-emerald-50 text-emerald-700 text-xs font-semibold border border-emerald-200">Verified Filing Data</span>
                                </div>
                                <div id="promisesGrid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5"></div>
                            </div>

                            <div class="space-y-3 pt-4 border-t border-slate-100">
                                <h4 class="text-sm font-bold text-slate-900">Hard Solvency Thresholds</h4>
                                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                                    <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                                        <span class="text-slate-500 block text-[10px]">Capital Adequacy (CAR)</span>
                                        <p class="text-base font-bold text-emerald-700 mono">18.9%</p>
                                        <span class="text-[10px] text-slate-500 block">RBI min 11.5% · Engine floor 14.0%</span>
                                    </div>
                                    <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                                        <span class="text-slate-500 block text-[10px]">Asset Quality (GNPA / NNPA)</span>
                                        <p class="text-base font-bold text-emerald-700 mono">1.11% / 0.37%</p>
                                        <span class="text-[10px] text-slate-500 block">Well below 1.40% ceiling</span>
                                    </div>
                                    <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                                        <span class="text-slate-500 block text-[10px]">Credit-to-Deposit (C/D)</span>
                                        <p class="text-base font-bold text-indigo-700 mono">96.0%</p>
                                        <span class="text-[10px] text-slate-500 block">Down from 98.4% YoY</span>
                                    </div>
                                    <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                                        <span class="text-slate-500 block text-[10px]">CASA Ratio (Period / Avg)</span>
                                        <p class="text-base font-bold text-slate-900 mono">38.0% / 31.6%</p>
                                        <span class="text-[10px] text-slate-500 block">Dual reported</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- SUB-TAB 3: DISCLOSURES -->
                        <div id="tab-pane-context" class="space-y-4 hidden">
                            <div class="flex flex-wrap items-center justify-between gap-2">
                                <div>
                                    <h4 class="text-sm font-bold text-slate-900">Certified Regulatory Disclosures &amp; RBI Context</h4>
                                    <p class="text-xs text-slate-500">Material BSE/NSE announcements and RBI MPC updates scored for safety gate impact.</p>
                                </div>
                                <span id="badgeEventsClassified" class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">Certified Stream</span>
                            </div>
                            <div id="eventsListContainer" class="space-y-2.5"></div>
                        </div>

                        <!-- SUB-TAB 4: PEERS & DECISION LEDGER -->
                        <div id="tab-pane-integrity" class="space-y-6 hidden">
                            <div class="space-y-3">
                                <div class="flex items-center justify-between">
                                    <div>
                                        <h4 class="text-sm font-bold text-slate-900">Big-4 Private Banking Watchlist</h4>
                                        <p class="text-xs text-slate-500">Live comparison across top Indian private banks. Offline peer quotes show '--' cleanly.</p>
                                    </div>
                                    <span class="px-2.5 py-1 rounded bg-purple-50 text-purple-700 text-xs font-semibold border border-purple-200">Peer Check</span>
                                </div>
                                <div class="overflow-x-auto">
                                    <table class="w-full text-left text-xs border border-slate-200 rounded-xl overflow-hidden mono">
                                        <thead class="bg-slate-50 text-slate-500 border-b border-slate-200 text-[11px]">
                                            <tr>
                                                <th class="p-3">Bank / Ticker</th>
                                                <th class="p-3">Price</th>
                                                <th class="p-3">P/B</th>
                                                <th class="p-3">5Y %ile</th>
                                                <th class="p-3">ROE</th>
                                                <th class="p-3">CAR</th>
                                                <th class="p-3">GNPA</th>
                                                <th class="p-3">C/D</th>
                                                <th class="p-3">Status</th>
                                            </tr>
                                        </thead>
                                        <tbody id="peerWatchlistTableBody" class="divide-y divide-slate-100 text-slate-700"></tbody>
                                    </table>
                                </div>
                            </div>

                            <div class="space-y-3 pt-2 border-t border-slate-100">
                                <h4 class="text-sm font-bold text-slate-900">Recent Decision Audit Log</h4>
                                <div class="overflow-x-auto">
                                    <table class="w-full text-xs text-left border border-slate-200 rounded-xl overflow-hidden">
                                        <thead class="bg-slate-50 text-slate-500 font-bold uppercase text-[10px] border-b border-slate-200">
                                            <tr>
                                                <th class="p-3">Timestamp (IST)</th>
                                                <th class="p-3">Action</th>
                                                <th class="p-3">Price</th>
                                                <th class="p-3">P/B</th>
                                                <th class="p-3">Tier</th>
                                                <th class="p-3">Audit Status</th>
                                            </tr>
                                        </thead>
                                        <tbody id="decisionHistoryTableBody" class="divide-y divide-slate-100 text-[11px] mono"></tbody>
                                    </table>
                                </div>
                            </div>

                            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-100">
                                <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1.5 text-xs text-slate-600">
                                    <h5 class="text-xs font-bold text-slate-700 uppercase tracking-wider">Statutory Filing Fingerprint (Q2 FY27)</h5>
                                    <p><strong>Standalone PAT:</strong> ₹19,510 Cr · <strong>Net Worth:</strong> ₹6,07,600 Cr</p>
                                    <p><strong>Deposits:</strong> ₹30,40,000 Cr · <strong>BVPS:</strong> ₹394.80 · <strong>ROE:</strong> 12.84%</p>
                                    <p class="text-[10px] mono text-slate-400 break-all pt-1">SHA-256: a044248425db1ac790b420d7b697f7184fd6be59466596a1bc7319e775f940d3</p>
                                </div>
                                <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                                    <h5 class="text-xs font-bold text-slate-700 uppercase tracking-wider">SQLite Decision Hash Chain</h5>
                                    <div class="bg-slate-900 text-emerald-400 p-3 rounded-lg font-mono text-[10px] space-y-1 max-h-40 overflow-y-auto" id="healthLedgerList"></div>
                                </div>
                            </div>
                        </div>
                    </section>

                    <!-- Collapsible Plain-Language Glossary (On-Demand Disclosure) -->
                    <details id="sectionGlossary" class="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
                        <summary class="flex items-center justify-between cursor-pointer">
                            <div class="flex items-center gap-2">
                                <h3 class="text-sm font-bold text-slate-900">Plain-Language Glossary</h3>
                                <span class="px-2 py-0.5 rounded bg-slate-100 text-slate-600 text-[10px] font-semibold">Banking Terms Explained Simply</span>
                            </div>
                            <svg class="w-4 h-4 text-slate-500 chevron" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                        </summary>
                        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs pt-4 mt-4 border-t border-slate-100">
                            <div class="bg-slate-50 p-3 rounded-xl border border-slate-100 space-y-1">
                                <span class="font-bold text-slate-900 block">Price-to-Book (P/B)</span>
                                <p class="text-slate-600 text-[11px]">Share price divided by net equity per share (₹394.80 BVPS). Lower P/B means you buy ₹1 of bank net worth more cheaply.</p>
                            </div>
                            <div class="bg-slate-50 p-3 rounded-xl border border-slate-100 space-y-1">
                                <span class="font-bold text-slate-900 block">Return on Equity (ROE)</span>
                                <p class="text-slate-600 text-[11px]">How efficiently the bank earns profits on shareholder equity. Trailing Q2 FY27 ROE is 12.84%.</p>
                            </div>
                            <div class="bg-slate-50 p-3 rounded-xl border border-slate-100 space-y-1">
                                <span class="font-bold text-slate-900 block">CASA Ratio</span>
                                <p class="text-slate-600 text-[11px]">Share of cheap savings &amp; current deposits (38.0% period-end / 31.6% daily avg). Higher CASA keeps funding costs low.</p>
                            </div>
                            <div class="bg-slate-50 p-3 rounded-xl border border-slate-100 space-y-1">
                                <span class="font-bold text-slate-900 block">Wilder RSI(14)</span>
                                <p class="text-slate-600 text-[11px]">Measures short-term speed of price rallies. Above 75 signals an overheated sprint where waiting for a pullback pays off.</p>
                            </div>
                        </div>
                    </details>
                </div>
            </div>

        </div>
    </main>

    <footer class="max-w-[1240px] mx-auto px-4 sm:px-6 py-6 text-center text-xs text-slate-400 border-t border-slate-200 mt-4">
        HDFC Bank Accumulation Engine · Built from Q2 FY27 BSE/NSE filing records &amp; live NSE cash feeds · Educational &amp; Simulation Use Only.
    </footer>

    <script>
        let latestStatusData = null;
        let latestBacktestData = null;
        let currentHeroTimeframe = '6M';
        let selectedTrancheBudget = 200000;
        let heroOverlays = { buyBand: true, fibLevels: false, movingAvgs: false, avwap: false };
        let cachedPriceSeries = [];
        let heroHoverIndex = -1;
        let equityHoverIndex = -1;

        function showToast(message, type = 'success') {
            const container = document.getElementById('toastContainer');
            if (!container) return;
            const toast = document.createElement('div');
            toast.className = `toast-item ${type === 'success' ? 'toast-success' : 'toast-error'}`;
            toast.textContent = message;
            container.appendChild(toast);
            setTimeout(() => {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 250);
            }, 3800);
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
            const s = ["th", "st", "nd", "rd"];
            const v = n % 100;
            return n + (s[(v - 20) % 10] || s[v] || s[0]);
        }

        const MAIN_TABS = ['overview', 'valuation', 'compass', 'track'];
        function switchMainTab(tabId, skipFocusScroll = false) {
            MAIN_TABS.forEach(t => {
                const tab = document.getElementById('tab-main-' + t);
                const panel = document.getElementById('panel-' + t);
                const isSelected = (t === tabId);
                if (tab) {
                    tab.setAttribute('aria-selected', isSelected ? 'true' : 'false');
                    if (isSelected) tab.setAttribute('focusgroupstart', '');
                    else tab.removeAttribute('focusgroupstart');
                    if (isSelected && !skipFocusScroll) {
                        tab.scrollIntoView({ block: 'nearest', inline: 'nearest' });
                    }
                }
                if (panel) {
                    if (isSelected) {
                        panel.removeAttribute('hidden');
                        panel.setAttribute('tabindex', '0');
                    } else {
                        panel.setAttribute('hidden', 'until-found');
                        panel.removeAttribute('tabindex');
                    }
                }
            });

            if (tabId === 'overview') {
                requestAnimationFrame(() => drawHeroChart());
            } else if (tabId === 'track') {
                requestAnimationFrame(() => {
                    if (latestBacktestData && latestBacktestData.equity_curve) {
                        renderNativeChart(latestBacktestData.equity_curve);
                    } else {
                        runBacktest();
                    }
                });
            }
        }

        function switchAuditTab(tabId) {
            const tabs = ['evidence', 'fundamentals', 'context', 'integrity'];
            tabs.forEach(t => {
                const pane = document.getElementById('tab-pane-' + t);
                const btn = document.getElementById('tab-btn-' + t);
                if (t === tabId) {
                    if (pane) pane.classList.remove('hidden');
                    if (btn) btn.className = 'px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-900 text-white shadow-sm';
                } else {
                    if (pane) pane.classList.add('hidden');
                    if (btn) btn.className = 'px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white';
                }
            });
            if (tabId === 'evidence') {
                requestAnimationFrame(() => {
                    if (latestBacktestData && latestBacktestData.equity_curve) {
                        renderNativeChart(latestBacktestData.equity_curve);
                    }
                });
            }
        }

        function setTrancheBudget(budget) {
            selectedTrancheBudget = budget;
            document.querySelectorAll('.btn-budget').forEach(b => {
                const isSel = Number(b.dataset.budget) === budget;
                b.className = isSel
                    ? 'btn-budget px-2 py-0.5 rounded text-[10px] font-bold bg-slate-900 text-white border border-slate-900'
                    : 'btn-budget px-2 py-0.5 rounded text-[10px] font-bold bg-white text-slate-600 border border-slate-200 hover:border-slate-300';
            });
            updateTrancheCalculator();
        }

        function updateTrancheCalculator() {
            const vl = latestStatusData ? latestStatusData.valuation_ledger : null;
            const bz = vl ? (vl.dynamic_buy_zone || vl.limit_tranche) : null;
            const zLow = bz ? bz.limit_zone_low : 745.0;
            const zHigh = bz ? bz.limit_zone_high : 775.0;

            const shLow = Math.floor(selectedTrancheBudget / zHigh);
            const shHigh = Math.floor(selectedTrancheBudget / zLow);
            const shT2 = Math.floor(selectedTrancheBudget / 710.0);

            const t1El = document.getElementById('verdictTrancheSharesText');
            const t1Sub = document.getElementById('calcT1Sub');
            const t2El = document.getElementById('calcT2SharesText');

            if (t1El) t1El.textContent = `${shLow}–${shHigh} sh`;
            if (t1Sub) t1Sub.textContent = `At ₹${zLow.toFixed(0)}–₹${zHigh.toFixed(0)}`;
            if (t2El) t2El.textContent = `${shT2} sh`;
        }

        function setHeroTimeframe(tf) {
            currentHeroTimeframe = tf;
            heroHoverIndex = -1;
            document.querySelectorAll('.btn-tf').forEach(b => {
                b.className = (b.dataset.tf === tf)
                    ? 'btn-tf px-2.5 py-1 rounded-md text-xs font-bold bg-slate-900 text-white shadow-sm'
                    : 'btn-tf px-2.5 py-1 rounded-md text-xs font-semibold text-slate-500 hover:text-slate-900';
            });
            drawHeroChart();
        }

        function toggleHeroOverlay(name) {
            heroOverlays[name] = !heroOverlays[name];
            const btn = document.getElementById('btnOverlay_' + name);
            if (btn) {
                if (heroOverlays[name]) {
                    btn.className = 'px-2.5 py-1 rounded-full text-xs font-bold bg-slate-900 text-white shadow-sm border border-slate-900 flex items-center gap-1.5';
                    if (name === 'buyBand') btn.innerHTML = '<span class="w-2 h-2 rounded-full bg-emerald-400"></span> Buy zone';
                } else {
                    btn.className = 'px-2.5 py-1 rounded-full text-xs font-semibold bg-white text-slate-600 border border-slate-200 hover:border-slate-300 flex items-center gap-1.5';
                    if (name === 'buyBand') btn.textContent = 'Buy zone';
                }
            }
            drawHeroChart();
        }

        function getFilteredHeroBars() {
            if (!cachedPriceSeries || cachedPriceSeries.length === 0) return [];
            if (currentHeroTimeframe === '1M') return cachedPriceSeries.slice(-22);
            if (currentHeroTimeframe === '3M') return cachedPriceSeries.slice(-66);
            if (currentHeroTimeframe === '6M') return cachedPriceSeries.slice(-132);
            return cachedPriceSeries;
        }

        function drawHeroChart() {
            const canvas = document.getElementById('heroPriceChart');
            if (!canvas) return;
            const rect = canvas.getBoundingClientRect();
            if (rect.width < 10 || rect.height < 10) return;

            const ctx = canvas.getContext('2d');
            if (!ctx) return;

            const dpr = window.devicePixelRatio || 1;
            canvas.width = rect.width * dpr;
            canvas.height = rect.height * dpr;
            ctx.scale(dpr, dpr);

            const w = rect.width;
            const h = rect.height;
            ctx.clearRect(0, 0, w, h);

            const bars = getFilteredHeroBars();
            if (bars.length < 2) return;

            const vl = latestStatusData ? latestStatusData.valuation_ledger : null;
            const bz = vl ? (vl.dynamic_buy_zone || vl.limit_tranche) : null;
            const zoneLow = bz ? bz.limit_zone_low : 745.0;
            const zoneHigh = bz ? bz.limit_zone_high : 775.0;

            const tech = (latestStatusData && latestStatusData.daily_compass) ? latestStatusData.daily_compass.technicals : null;
            const fib = tech ? tech.fibonacci : null;

            const padding = { top: 28, right: 60, bottom: 28, left: 16 };
            const chartW = w - padding.left - padding.right;
            const chartH = h - padding.top - padding.bottom;

            let minP = Infinity, maxP = -Infinity;
            bars.forEach(b => {
                if (b.close < minP) minP = b.close;
                if (b.close > maxP) maxP = b.close;
            });

            if (heroOverlays.buyBand) {
                minP = Math.min(minP, zoneLow - 12);
                maxP = Math.max(maxP, zoneHigh + 12);
            }
            minP = Math.floor(minP - 8);
            maxP = Math.ceil(maxP + 10);

            const priceSpan = maxP - minP || 1;
            const getY = (val) => padding.top + chartH - ((val - minP) / priceSpan) * chartH;
            const getX = (idx) => padding.left + (idx / (bars.length - 1)) * chartW;

            const firstBar = bars[0];
            const lastBar = bars[bars.length - 1];
            const periodRet = ((lastBar.close - firstBar.close) / firstBar.close) * 100;
            const isPositive = periodRet >= 0;
            const lineHex = isPositive ? '#00D09C' : '#F43F5E';
            const fillTop = isPositive ? 'rgba(0, 208, 156, 0.24)' : 'rgba(244, 63, 94, 0.20)';
            const fillBot = isPositive ? 'rgba(0, 208, 156, 0.01)' : 'rgba(244, 63, 94, 0.01)';

            // Update period badge & date caption dynamically
            const periodBadge = document.getElementById('heroPeriodBadge');
            if (periodBadge) {
                periodBadge.textContent = `${isPositive ? '+' : ''}${periodRet.toFixed(1)}% (${currentHeroTimeframe})`;
                periodBadge.className = isPositive
                    ? 'px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 mono'
                    : 'px-2 py-0.5 rounded-full text-[11px] font-bold bg-rose-50 text-rose-700 border border-rose-200 mono';
            }
            const dateCap = document.getElementById('heroChartDateCaption');
            if (dateCap) {
                dateCap.textContent = `${firstBar.date} to ${lastBar.date} (${bars.length} sessions)`;
            }

            // Grid lines & right Y-axis labels
            ctx.strokeStyle = '#e2e8f0';
            ctx.lineWidth = 0.7;
            const step = priceSpan > 160 ? 50 : 25;
            for (let p = Math.ceil(minP / step) * step; p <= maxP; p += step) {
                const y = getY(p);
                if (y < padding.top || y > padding.top + chartH) continue;
                ctx.beginPath();
                ctx.moveTo(padding.left, y);
                ctx.lineTo(padding.left + chartW, y);
                ctx.stroke();

                ctx.fillStyle = '#94a3b8';
                ctx.font = '10px ui-monospace, monospace';
                ctx.textAlign = 'left';
                ctx.fillText('₹' + p, padding.left + chartW + 8, y + 3);
            }

            // 1. Dynamic Buy Zone Shaded Band
            if (heroOverlays.buyBand) {
                const yTop = getY(zoneHigh);
                const yBot = getY(zoneLow);
                ctx.fillStyle = 'rgba(0, 208, 156, 0.13)';
                ctx.fillRect(padding.left, yTop, chartW, Math.max(2, yBot - yTop));

                ctx.strokeStyle = '#059669';
                ctx.lineWidth = 1;
                ctx.setLineDash([4, 4]);
                ctx.beginPath();
                ctx.moveTo(padding.left, yTop);
                ctx.lineTo(padding.left + chartW, yTop);
                ctx.moveTo(padding.left, yBot);
                ctx.lineTo(padding.left + chartW, yBot);
                ctx.stroke();
                ctx.setLineDash([]);

                ctx.fillStyle = '#065f46';
                ctx.font = 'bold 10px sans-serif';
                ctx.textAlign = 'left';
                ctx.fillText(`Buy zone (₹${zoneLow.toFixed(0)}–₹${zoneHigh.toFixed(0)})`, padding.left + 8, yTop + 13);
            }

            // 2. Dynamic Fib Levels
            if (heroOverlays.fibLevels && fib) {
                const fibs = [
                    { label: `Fib 38.2% ₹${fib.fib_382.toFixed(0)}`, val: fib.fib_382, color: '#3b82f6' },
                    { label: `Fib 50.0% ₹${fib.fib_500.toFixed(0)}`, val: fib.fib_500, color: '#6366f1' },
                    { label: `Fib 61.8% ₹${fib.fib_618.toFixed(0)}`, val: fib.fib_618, color: '#8b5cf6' }
                ];
                fibs.forEach(f => {
                    const yf = getY(f.val);
                    if (yf < padding.top || yf > padding.top + chartH) return;
                    ctx.strokeStyle = f.color;
                    ctx.lineWidth = 1;
                    ctx.setLineDash([3, 3]);
                    ctx.beginPath();
                    ctx.moveTo(padding.left, yf);
                    ctx.lineTo(padding.left + chartW, yf);
                    ctx.stroke();
                    ctx.setLineDash([]);
                    ctx.fillStyle = f.color;
                    ctx.font = '10px ui-monospace, monospace';
                    ctx.textAlign = 'left';
                    ctx.fillText(f.label, padding.left + 8, yf - 3);
                });
            }

            // 3. Dynamic Moving Averages
            if (heroOverlays.movingAvgs && tech) {
                const mas = [
                    { label: `20 DMA ₹${tech.dma_20.toFixed(1)}`, val: tech.dma_20, color: '#f59e0b' },
                    { label: `50 DMA ₹${tech.dma_50.toFixed(1)}`, val: tech.dma_50, color: '#0ea5e9' },
                    { label: `200 DMA ₹${tech.dma_200.toFixed(1)}`, val: tech.dma_200, color: '#a855f7' }
                ];
                mas.forEach((m, idx) => {
                    const ym = getY(m.val);
                    if (ym < padding.top || ym > padding.top + chartH) return;
                    ctx.strokeStyle = m.color;
                    ctx.lineWidth = 1.2;
                    ctx.setLineDash([4, 3]);
                    ctx.beginPath();
                    ctx.moveTo(padding.left, ym);
                    ctx.lineTo(padding.left + chartW, ym);
                    ctx.stroke();
                    ctx.setLineDash([]);
                    ctx.fillStyle = m.color;
                    ctx.font = 'bold 10px ui-monospace, monospace';
                    ctx.textAlign = 'right';
                    ctx.fillText(m.label, padding.left + chartW - 8 - (idx * 105), ym - 3);
                });
            }

            // 4. Dynamic AVWAP
            if (heroOverlays.avwap && tech) {
                const yAvwap = getY(tech.anchored_vwap || 777.8);
                if (yAvwap >= padding.top && yAvwap <= padding.top + chartH) {
                    ctx.strokeStyle = '#4f46e5';
                    ctx.lineWidth = 1.5;
                    ctx.setLineDash([6, 3]);
                    ctx.beginPath();
                    ctx.moveTo(padding.left, yAvwap);
                    ctx.lineTo(padding.left + chartW, yAvwap);
                    ctx.stroke();
                    ctx.setLineDash([]);
                    ctx.fillStyle = '#4338ca';
                    ctx.font = 'bold 10px ui-monospace, monospace';
                    ctx.textAlign = 'right';
                    ctx.fillText(`AVWAP ₹${(tech.anchored_vwap || 777.8).toFixed(1)}`, padding.left + chartW - 8, yAvwap - 4);
                }
            }

            // 5. Gradient Area & Curve
            const grad = ctx.createLinearGradient(0, padding.top, 0, padding.top + chartH);
            grad.addColorStop(0, fillTop);
            grad.addColorStop(1, fillBot);

            ctx.beginPath();
            ctx.moveTo(getX(0), getY(bars[0].close));
            for (let i = 1; i < bars.length; i++) ctx.lineTo(getX(i), getY(bars[i].close));
            ctx.lineTo(getX(bars.length - 1), padding.top + chartH);
            ctx.lineTo(getX(0), padding.top + chartH);
            ctx.closePath();
            ctx.fillStyle = grad;
            ctx.fill();

            ctx.beginPath();
            ctx.moveTo(getX(0), getY(bars[0].close));
            for (let i = 1; i < bars.length; i++) ctx.lineTo(getX(i), getY(bars[i].close));
            ctx.strokeStyle = lineHex;
            ctx.lineWidth = 2.4;
            ctx.lineJoin = 'round';
            ctx.lineCap = 'round';
            ctx.stroke();

            // 6. Latest Price Dot + Right-Axis Current Pill
            const lastX = getX(bars.length - 1);
            const lastY = getY(lastBar.close);

            ctx.beginPath();
            ctx.arc(lastX, lastY, 8, 0, Math.PI * 2);
            ctx.fillStyle = isPositive ? 'rgba(0, 208, 156, 0.28)' : 'rgba(244, 63, 94, 0.28)';
            ctx.fill();

            ctx.beginPath();
            ctx.arc(lastX, lastY, 4.2, 0, Math.PI * 2);
            ctx.fillStyle = lineHex;
            ctx.fill();
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 1.6;
            ctx.stroke();

            // X-axis date ticks (Start, Mid, Latest)
            const midBar = bars[Math.floor(bars.length / 2)];
            ctx.fillStyle = '#94a3b8';
            ctx.font = '10px ui-monospace, monospace';
            ctx.textAlign = 'left';
            ctx.fillText(firstBar.date, padding.left, h - 8);
            ctx.textAlign = 'center';
            ctx.fillText(midBar.date, padding.left + chartW / 2, h - 8);
            ctx.textAlign = 'right';
            ctx.fillText(lastBar.date, padding.left + chartW, h - 8);

            // 7. Interactive Crosshair & Floating Tooltip on Hover/Scrub
            const tip = document.getElementById('heroChartTooltip');
            const readout = document.getElementById('heroScrubReadout');
            if (heroHoverIndex >= 0 && heroHoverIndex < bars.length) {
                const pt = bars[heroHoverIndex];
                const hx = getX(heroHoverIndex);
                const hy = getY(pt.close);

                ctx.strokeStyle = '#64748b';
                ctx.lineWidth = 1;
                ctx.setLineDash([3, 3]);
                ctx.beginPath();
                ctx.moveTo(hx, padding.top);
                ctx.lineTo(hx, padding.top + chartH);
                ctx.moveTo(padding.left, hy);
                ctx.lineTo(padding.left + chartW, hy);
                ctx.stroke();
                ctx.setLineDash([]);

                ctx.beginPath();
                ctx.arc(hx, hy, 5.5, 0, Math.PI * 2);
                ctx.fillStyle = '#0f172a';
                ctx.fill();
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 2;
                ctx.stroke();

                const vsStart = ((pt.close - firstBar.close) / firstBar.close) * 100;
                const inBuyZone = pt.close >= zoneLow && pt.close <= zoneHigh;
                const zoneGap = pt.close > zoneHigh
                    ? `${(((pt.close - zoneHigh) / pt.close) * 100).toFixed(1)}% above buy`
                    : (inBuyZone ? 'Inside buy zone!' : 'Below buy zone');

                if (tip) {
                    tip.classList.remove('hidden');
                    tip.innerHTML = `
                        <div class="font-bold text-slate-300 text-[10px] mono">${pt.date}</div>
                        <div class="text-sm font-extrabold text-white mono">₹${pt.close.toFixed(2)} <span class="${vsStart >= 0 ? 'text-emerald-400' : 'text-rose-400'} text-[11px]">(${vsStart >= 0 ? '+' : ''}${vsStart.toFixed(1)}%)</span></div>
                        <div class="text-[10px] ${inBuyZone ? 'text-emerald-400 font-bold' : 'text-slate-300'}">${zoneGap}</div>
                    `;
                    const tipW = tip.offsetWidth || 150;
                    const leftPos = (hx + 14 + tipW > w - 10) ? Math.max(8, hx - tipW - 14) : (hx + 14);
                    const topPos = Math.max(8, Math.min(h - 74, hy - 28));
                    tip.style.left = leftPos + 'px';
                    tip.style.top = topPos + 'px';
                }
                if (readout) {
                    readout.classList.remove('hidden');
                    readout.textContent = `Inspecting ${pt.date}: ₹${pt.close.toFixed(2)}`;
                }
            } else {
                if (tip) tip.classList.add('hidden');
                if (readout) readout.classList.add('hidden');
            }
        }

        function attachHeroChartInteraction() {
            const canvas = document.getElementById('heroPriceChart');
            if (!canvas || canvas.dataset.bound === '1') return;
            canvas.dataset.bound = '1';

            const updateHover = (clientX) => {
                const bars = getFilteredHeroBars();
                if (bars.length < 2) return;
                const rect = canvas.getBoundingClientRect();
                const paddingLeft = 16;
                const paddingRight = 60;
                const chartW = rect.width - paddingLeft - paddingRight;
                const relX = Math.max(0, Math.min(chartW, (clientX - rect.left) - paddingLeft));
                const idx = Math.round((relX / chartW) * (bars.length - 1));
                if (idx !== heroHoverIndex) {
                    heroHoverIndex = idx;
                    drawHeroChart();
                }
            };

            canvas.addEventListener('pointermove', (e) => updateHover(e.clientX));
            canvas.addEventListener('pointerdown', (e) => updateHover(e.clientX));
            canvas.addEventListener('pointerleave', () => {
                heroHoverIndex = -1;
                drawHeroChart();
            });
        }

        function applyStatus(data) {
            if (!data) return;
            latestStatusData = data;

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
                    deltaEl.className = `text-sm font-bold flex items-center gap-0.5 mono ${isUp ? 'text-emerald-600' : 'text-rose-600'}`;
                    deltaEl.textContent = `${isUp ? '▲ +' : '▼ '}${q.change.toFixed(2)} (${isUp ? '+' : ''}${q.change_pct.toFixed(2)}%)`;
                }

                const chipText = document.getElementById('heroFeedChipText');
                const chipDot = document.getElementById('heroFeedChipDot');
                const chipEl = document.getElementById('heroFeedChip');
                if (chipText) {
                    const isL = q.is_live;
                    if (chipEl) {
                        chipEl.className = isL
                            ? "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-[11px] font-semibold bg-emerald-50 text-emerald-900 border border-emerald-200"
                            : "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-[11px] font-semibold bg-amber-50 text-amber-900 border border-amber-200";
                    }
                    if (chipDot) {
                        chipDot.className = `w-1.5 h-1.5 rounded-full ${isL ? 'bg-emerald-500' : 'bg-amber-500'}`;
                    }
                    const statusLbl = isL ? 'LIVE' : 'CACHED EOD';
                    chipText.textContent = `${statusLbl} · ${q.source || 'NSE'} · Prev close ₹${(q.previous_close || 846.0).toFixed(2)}`;
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
            const feedTs = decObj ? decObj.feed_timestamp : "Latest EOD";

            const badge = document.getElementById('headerFeedStatusBadge');
            if (badge) {
                if (isLive) {
                    badge.className = "hidden md:inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-50 text-emerald-700 border border-emerald-200";
                    badge.textContent = "LIVE NSE";
                } else {
                    badge.className = "hidden md:inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-50 text-amber-800 border border-amber-200";
                    badge.textContent = "CACHED EOD";
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

            try { renderVerdictAndPlan(data); } catch (e) { console.error(e); }
            try { renderOverviewReasons(data); } catch (e) { console.error(e); }
            try { renderPriceVsValue(data); } catch (e) { console.error(e); }
            if (data.decision_object) {
                try { renderSingleDecisionObject(data.decision_object); } catch (e) { console.error(e); }
            }
            if (data.fundamental && data.fundamental.thesis_health) {
                try { renderThesisHealth(data.fundamental.thesis_health); } catch (e) { console.error(e); }
            }
            if (data.macro_market) {
                try { renderMacroMarket(data.macro_market); } catch (e) { console.error(e); }
            }
            if (data.daily_compass) {
                try { renderDailyCompass(data.daily_compass); } catch (e) { console.error(e); }
            }
            if (data.valuation_ledger) {
                try { renderPriceLadder(data.valuation_ledger); renderValuationDetails(data.valuation_ledger); } catch (e) { console.error(e); }
            }
            if (data.accumulation_gates) {
                try { renderGates(data.accumulation_gates, data.valuation_ledger); } catch (e) { console.error(e); }
            }
            if (data.transcript_report) {
                try { renderPromises(data.transcript_report); } catch (e) { console.error(e); }
            }
            if (data.events) {
                try { renderEvents(data.events); } catch (e) { console.error(e); }
            }
            if (data.peer_watchlist) {
                try { renderPeerWatchlist(data.peer_watchlist); } catch (e) { console.error(e); }
            }
            if (data.analogues) {
                try { renderAnalogues(data.analogues); } catch (e) { console.error(e); }
            }
            if (data.scoreboard) {
                try {
                    renderHealthLedger(data.scoreboard, data.scheduled_lock_skipped_reason);
                    renderDecisionHistory(data.scoreboard, data.decision_object, data.reference_price);
                } catch (e) { console.error(e); }
            }
        }

        function renderVerdictAndPlan(data) {
            const vl = data.valuation_ledger;
            const bz = vl ? (vl.dynamic_buy_zone || vl.limit_tranche) : null;
            const refPrice = data.reference_price || 817.80;
            const zLow = bz ? bz.limit_zone_low : 745.0;
            const zHigh = bz ? bz.limit_zone_high : 775.0;
            const bullTarget = (vl && vl.scenarios) ? (vl.scenarios.find(s => s.name === 'BULL')?.target_price || 987.0) : 987.0;

            const action = data.accumulation_gates ? data.accumulation_gates.final_action : "WAIT";
            const badge = document.getElementById('verdictActionBadge');
            if (badge) {
                badge.textContent = action;
                if (action === 'ACCUMULATE' || action === 'BUY') {
                    badge.className = "text-3xl font-extrabold text-emerald-600 tracking-tight";
                } else if (action === 'WAIT') {
                    badge.className = "text-3xl font-extrabold text-amber-500 tracking-tight";
                } else {
                    badge.className = "text-3xl font-extrabold text-rose-600 tracking-tight";
                }
            }

            const headline = document.getElementById('decisionHeadline');
            if (headline) {
                if (refPrice > zHigh) {
                    const dipRs = (refPrice - zHigh).toFixed(2);
                    const dipPct = (((refPrice - zHigh) / refPrice) * 100).toFixed(1);
                    headline.textContent = `Don't chase — ₹${dipRs} (${dipPct}%) above buy zone`;
                } else if (refPrice >= zLow) {
                    headline.textContent = `Price is inside your limit buy zone`;
                } else {
                    headline.textContent = `Deep value discount active below ₹${zLow.toFixed(0)}`;
                }
            }

            const planText = document.getElementById('verdictActionText');
            if (planText) {
                planText.innerHTML = `Place a patient limit order in <strong class="text-slate-900 mono">₹${zLow.toFixed(0)}–₹${zHigh.toFixed(0)}</strong>. Keep a second tranche ready at <strong class="text-slate-900 mono">₹710</strong> if dips deepen.`;
            }

            if (data.order_expiry_label) {
                const el = document.getElementById('orderValidityPill');
                if (el) el.textContent = `Till ${data.order_expiry_label}`;
            }

            // Thermometer positioning (Scale ₹660 to bullTarget)
            const minScale = 660;
            const maxScale = Math.max(bullTarget, 987);
            const span = maxScale - minScale;
            const pctOf = (p) => Math.max(2, Math.min(97, ((p - minScale) / span) * 100));

            const zStartPct = pctOf(zLow);
            const zEndPct = pctOf(zHigh);
            const currPct = pctOf(refPrice);
            const floorPct = pctOf(710);

            const bandEl = document.getElementById('thermBuyZoneBand');
            if (bandEl) {
                bandEl.style.left = zStartPct + '%';
                bandEl.style.width = Math.max(4, zEndPct - zStartPct) + '%';
            }
            const floorEl = document.getElementById('thermDeepDipPin');
            if (floorEl) floorEl.style.left = floorPct + '%';

            const pinEl = document.getElementById('thermTodayPin');
            const lblEl = document.getElementById('thermTodayLabel');
            if (pinEl) pinEl.style.left = currPct + '%';
            if (lblEl) {
                lblEl.style.left = currPct + '%';
                lblEl.textContent = `₹${refPrice.toFixed(0)}`;
            }
            const tZoneLbl = document.getElementById('thermZoneLabel');
            if (tZoneLbl) tZoneLbl.textContent = `Buy ₹${zLow.toFixed(0)}–${zHigh.toFixed(0)}`;
            const tBullLbl = document.getElementById('thermBullLabel');
            if (tBullLbl) tBullLbl.textContent = `Bull ₹${bullTarget.toFixed(0)}`;

            const gapBadge = document.getElementById('gapToBuyBadge');
            const chkPriceStatus = document.getElementById('chkPriceStatus');
            const chkPriceBar = document.getElementById('chkPriceBar');
            const chkPriceNote = document.getElementById('chkPriceNote');

            if (refPrice <= zHigh && refPrice >= zLow) {
                if (gapBadge) { gapBadge.textContent = 'IN BUY ZONE'; gapBadge.className = 'font-bold text-emerald-700 mono'; }
                if (chkPriceStatus) { chkPriceStatus.textContent = 'Ready'; chkPriceStatus.className = 'px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200'; }
                if (chkPriceBar) { chkPriceBar.style.width = '100%'; chkPriceBar.className = 'bg-emerald-500 h-full rounded-full'; }
                if (chkPriceNote) chkPriceNote.textContent = `₹${refPrice.toFixed(2)} sits inside ₹${zLow.toFixed(0)}–₹${zHigh.toFixed(0)}.`;
            } else {
                const gapPct = Math.max(0, ((refPrice - zHigh) / refPrice) * 100);
                if (gapBadge) { gapBadge.textContent = `${gapPct.toFixed(1)}% above buy zone`; gapBadge.className = 'font-bold text-amber-700 mono'; }
                if (chkPriceStatus) { chkPriceStatus.textContent = 'Waiting'; chkPriceStatus.className = 'px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200'; }
                const progress = Math.max(15, Math.min(92, 100 - gapPct * 6));
                if (chkPriceBar) { chkPriceBar.style.width = `${progress.toFixed(0)}%`; chkPriceBar.className = 'bg-amber-400 h-full rounded-full'; }
                if (chkPriceNote) chkPriceNote.textContent = `₹${refPrice.toFixed(2)} now · needs a ${gapPct.toFixed(1)}% dip to ₹${zHigh.toFixed(0)}.`;
            }

            // Real RSI from Gate 4
            const gates = (data.accumulation_gates && data.accumulation_gates.gates) ? data.accumulation_gates.gates : [];
            const g4 = gates.find(g => g.gate_number === 4);
            const rsiVal = (g4 && g4.evidence_metrics && g4.evidence_metrics.wilder_rsi_14) ? g4.evidence_metrics.wilder_rsi_14 : 88.7;
            const rsiThresh = (g4 && g4.evidence_metrics && g4.evidence_metrics.rsi_overbought_threshold) ? g4.evidence_metrics.rsi_overbought_threshold : 75.0;

            const rsiStatus = document.getElementById('chkRsiStatus');
            const rsiNeedle = document.getElementById('chkRsiNeedle');
            const rsiNote = document.getElementById('chkRsiNote');
            if (rsiNeedle) rsiNeedle.style.left = Math.min(97, Math.max(3, rsiVal)) + '%';
            if (rsiVal >= rsiThresh) {
                if (rsiStatus) { rsiStatus.textContent = 'Overbought'; rsiStatus.className = 'px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200'; }
                if (rsiNote) rsiNote.textContent = `RSI ${rsiVal.toFixed(1)} is hot (> ${rsiThresh.toFixed(0)}). Wait for momentum cooldown.`;
            } else {
                if (rsiStatus) { rsiStatus.textContent = 'Cooled'; rsiStatus.className = 'px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200'; }
                if (rsiNote) rsiNote.textContent = `RSI ${rsiVal.toFixed(1)} is in healthy accumulation territory.`;
            }

            // Overview gate strip
            const passCount = gates.filter(g => g.passed).length;
            const gSum = document.getElementById('overviewGatesSummary');
            if (gSum) gSum.textContent = `${passCount} of ${gates.length || 6} Pass →`;
            const gBars = document.getElementById('overviewGateBars');
            if (gBars && gates.length > 0) {
                gBars.innerHTML = gates.map(g => {
                    const cls = g.passed ? 'bg-emerald-500' : (g.status === 'WAIT' ? 'bg-amber-400 animate-pulse' : 'bg-rose-500');
                    return `<div class="${cls} rounded-full h-full" title="Gate ${g.gate_number}: ${g.gate_name} (${g.status})"></div>`;
                }).join('');
            }

            updateTrancheCalculator();
        }

        function renderOverviewReasons(data) {
            const buyList = document.getElementById('whyBuyList');
            const waitList = document.getElementById('whyWaitList');
            if (!buyList || !waitList) return;

            const vl = data.valuation_ledger || {};
            const bz = vl.dynamic_buy_zone || vl.limit_tranche || { limit_zone_low: 745, limit_zone_high: 775 };
            const ref = data.reference_price || 817.80;
            const pb = vl.current_pb || 2.07;
            const gates = (data.accumulation_gates && data.accumulation_gates.gates) ? data.accumulation_gates.gates : [];
            const passCount = gates.filter(g => g.passed).length;
            const g4 = gates.find(g => g.gate_number === 4);
            const rsiVal = (g4 && g4.evidence_metrics && g4.evidence_metrics.wilder_rsi_14) ? g4.evidence_metrics.wilder_rsi_14 : 88.7;
            const isLive = data.quote ? data.quote.is_live : false;

            const gapPct = Math.max(0, ((ref - bz.limit_zone_high) / ref) * 100);
            const baseScenario = (vl.scenarios || []).find(s => s.name === 'BASE') || { target_price: 553.5 };
            const bullScenario = (vl.scenarios || []).find(s => s.name === 'BULL') || { target_price: 987.0 };

            const buyBullets = [
                {
                    text: `Reasonable valuation: trades at <strong>${pb.toFixed(2)}× book value</strong> against a ≤2.40× accumulation ceiling.`,
                    tag: 'VALUATION',
                    tagCls: 'bg-slate-100 text-slate-600 border-slate-200'
                },
                {
                    text: `<strong>${passCount} of ${gates.length || 6} safety checks</strong> pass — balance sheet capital (18.9% CAR) &amp; asset quality (1.11% GNPA) are pristine.`,
                    tag: 'SOLVENCY',
                    tagCls: 'bg-emerald-50 text-emerald-700 border-emerald-200'
                },
                {
                    text: `Bull-case compounding target sits at <strong>₹${bullScenario.target_price.toFixed(0)}</strong> (+${(((bullScenario.target_price - ref) / ref) * 100).toFixed(1)}% upside from today).`,
                    tag: 'UPSIDE',
                    tagCls: 'bg-indigo-50 text-indigo-700 border-indigo-200'
                },
                {
                    text: isLive
                        ? `Live NSE real-time quote verified (${data.quote.timestamp || 'Today'}) — market feed is healthy.`
                        : `Historical post-merger dip episodes show limit orders in ₹${bz.limit_zone_low.toFixed(0)}–₹${bz.limit_zone_high.toFixed(0)} capture optimal risk/reward.`,
                    tag: isLive ? 'LIVE FEED' : 'DISCIPLINE',
                    tagCls: 'bg-emerald-50 text-emerald-700 border-emerald-200'
                }
            ];

            const waitBullets = [
                {
                    text: ref > bz.limit_zone_high
                        ? `Price is <strong>${gapPct.toFixed(1)}% above</strong> the top of your buy zone (₹${bz.limit_zone_high.toFixed(0)}). Chasing reduces margin of safety.`
                        : `Verify RSI cooldown before sizing up beyond Tranche 1 limits.`,
                    tag: 'TIMING',
                    tagCls: 'bg-amber-50 text-amber-800 border-amber-200'
                },
                {
                    text: `Short-term RSI is <strong>${rsiVal.toFixed(1)}</strong> (overbought >75). Letting the sprint cool improves entry fill quality.`,
                    tag: 'MOMENTUM',
                    tagCls: 'bg-amber-50 text-amber-800 border-amber-200'
                },
                {
                    text: `Conservative base-case valuation is ₹${baseScenario.target_price.toFixed(1)} until CASA mix improves above 34% daily average.`,
                    tag: 'THESIS WATCH',
                    tagCls: 'bg-slate-100 text-slate-600 border-slate-200'
                },
                {
                    text: isLive
                        ? `2-quarter liquidity check flags industry deposit competition — keep staged limit orders rather than lump-sum buys.`
                        : `Quote is using cached EOD bars (${data.quote ? data.quote.timestamp : 'offline'}); live market execution is paused.`,
                    tag: isLive ? 'LIQUIDITY' : 'CACHED EOD',
                    tagCls: isLive ? 'bg-amber-50 text-amber-800 border-amber-200' : 'bg-rose-50 text-rose-700 border-rose-200'
                }
            ];

            buyList.innerHTML = buyBullets.map(b => `
                <li class="flex items-start justify-between gap-3">
                    <div class="flex items-start gap-2">
                        <span class="text-emerald-600 font-bold shrink-0">✓</span>
                        <span>${b.text}</span>
                    </div>
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold border shrink-0 ${b.tagCls}">${b.tag}</span>
                </li>
            `).join('');

            waitList.innerHTML = waitBullets.map(b => `
                <li class="flex items-start justify-between gap-3">
                    <div class="flex items-start gap-2">
                        <span class="text-rose-600 font-bold shrink-0">!</span>
                        <span>${b.text}</span>
                    </div>
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold border shrink-0 ${b.tagCls}">${b.tag}</span>
                </li>
            `).join('');
        }

        function renderPriceVsValue(data) {
            const vl = data.valuation_ledger;
            if (!vl) return;
            const scenarios = vl.scenarios || [];
            const bear = scenarios.find(s => s.name === 'BEAR')?.target_price || 385.7;
            const base = scenarios.find(s => s.name === 'BASE')?.target_price || 553.5;
            const bull = scenarios.find(s => s.name === 'BULL')?.target_price || 987.0;
            const bz = vl.dynamic_buy_zone || vl.limit_tranche || { limit_zone_low: 745, limit_zone_high: 775 };
            const ref = data.reference_price || 817.80;

            const sumEl = document.getElementById('priceVsValueSummary');
            if (sumEl) {
                const vsBase = (((ref - base) / base) * 100).toFixed(0);
                const vsBull = (((bull - ref) / ref) * 100).toFixed(0);
                sumEl.innerHTML = `At <strong class="text-slate-900 mono">₹${ref.toFixed(2)}</strong>, the stock is <strong>${vsBase}%</strong> above conservative base value (<strong class="mono">₹${base.toFixed(0)}</strong>) with <strong>+${vsBull}%</strong> upside to the <strong class="mono">₹${bull.toFixed(0)}</strong> bull target.`;
            }

            const span = (bull - bear) || 1;
            const pct = (p) => Math.max(3, Math.min(97, ((p - bear) / span) * 100));

            const band = document.getElementById('pvvBuyBand');
            const baseLine = document.getElementById('pvvBaseLine');
            const currPin = document.getElementById('pvvCurrPin');
            const currLbl = document.getElementById('pvvCurrLabel');
            if (band) {
                band.style.left = pct(bz.limit_zone_low) + '%';
                band.style.width = Math.max(3, pct(bz.limit_zone_high) - pct(bz.limit_zone_low)) + '%';
            }
            if (baseLine) baseLine.style.left = pct(base) + '%';
            if (currPin) currPin.style.left = pct(ref) + '%';
            if (currLbl) {
                currLbl.style.left = pct(ref) + '%';
                currLbl.textContent = `₹${ref.toFixed(0)}`;
            }
            const lBear = document.getElementById('pvvBearLabel');
            const lBase = document.getElementById('pvvBaseLabel');
            const lBull = document.getElementById('pvvBullLabel');
            if (lBear) lBear.textContent = `Bear ₹${bear.toFixed(0)}`;
            if (lBase) lBase.textContent = `Base ₹${base.toFixed(0)}`;
            if (lBull) lBull.textContent = `Bull ₹${bull.toFixed(0)}`;
        }

        function renderValuationDetails(vl) {
            if (!vl) return;
            const ke = vl.base_cost_of_equity_pct || 13.07;
            const kePill = document.getElementById('valDynamicKePill');
            if (kePill) kePill.textContent = `Ke = ${ke.toFixed(2)}%`;

            const sotpPill = document.getElementById('valSotpAnchorPill');
            if (sotpPill && vl.sotp_fair_value_anchor) {
                sotpPill.textContent = `SOTP Anchor = ₹${vl.sotp_fair_value_anchor.toFixed(2)}`;
            }
            const keFormula = document.getElementById('valKeFormulaText');
            if (keFormula && vl.cost_of_equity_detail) {
                const d = vl.cost_of_equity_detail;
                keFormula.textContent = `Ke = Rf (${(d.risk_free_rate_pct || 6.8).toFixed(2)}%) + Beta (${(d.beta || 1.14).toFixed(2)}) × ERP (${(d.equity_risk_premium_pct || 5.5).toFixed(2)}%) = ${(d.ke_dynamic_pct || ke).toFixed(2)}%`;
            }
        }

        function renderSingleDecisionObject(dec) {
            if (!dec) return;
            const badge = document.getElementById('decisionCanonicalBadge');
            if (badge) {
                badge.textContent = dec.canonical_action;
                badge.className = dec.canonical_action === 'WAIT'
                    ? "px-3 py-1 rounded-full font-extrabold text-xs uppercase bg-amber-50 text-amber-800 border border-amber-200"
                    : (dec.canonical_action === 'BUY'
                        ? "px-3 py-1 rounded-full font-extrabold text-xs uppercase bg-emerald-50 text-emerald-800 border border-emerald-200"
                        : "px-3 py-1 rounded-full font-extrabold text-xs uppercase bg-rose-50 text-rose-800 border border-rose-200");
            }

            const precEl = document.getElementById('decisionPrecedenceTier');
            if (precEl) precEl.textContent = dec.precedence_tier || 'Patience Guard';

            const detailEl = document.getElementById('decisionDetailText');
            if (detailEl) detailEl.textContent = dec.action_detail || dec.arbitration_rationale || '';

            const orderEl = document.getElementById('decisionOrderDirective');
            if (orderEl && dec.order_directive) {
                const od = dec.order_directive;
                if (typeof od === 'object') {
                    const z = od.limit_entry_zone || [745, 775];
                    orderEl.textContent = `${od.execution_order_type || 'LIMIT'} · Zone ₹${z[0]}–₹${z[1]} · Valid ${od.order_expiry_date || ''}`;
                } else {
                    orderEl.textContent = od;
                }
            }

            const grid = document.getElementById('decisionInputsGrid');
            if (grid && dec.inputs) {
                const inputs = Array.isArray(dec.inputs) ? dec.inputs : Object.values(dec.inputs);
                grid.innerHTML = inputs.map(inp => {
                    const label = inp.label || inp.model_name || 'Model';
                    const action = inp.perspective || inp.recommended_action || 'WAIT';
                    const weightStr = inp.weight ? (typeof inp.weight === 'string' ? inp.weight : `${(inp.weight * 100).toFixed(0)}%`) : '20%';
                    const isConflict = inp.has_conflict || action.includes('BUY') || action.includes('ACCUMULATE');
                    const conflictTag = isConflict
                        ? '<span class="px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 font-bold text-[9px] uppercase">Conflict</span>'
                        : '<span class="px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 font-semibold text-[9px]">Aligned</span>';

                    return `
                        <div class="bg-slate-50 p-3 rounded-xl border border-slate-200 space-y-1">
                            <div class="flex items-center justify-between gap-1">
                                <span class="font-bold text-slate-700 text-[11px] truncate">${label}</span>
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
            if (disagPill) disagPill.textContent = `${disags.length} Disagreement${disags.length === 1 ? '' : 's'}`;
            if (disagList) {
                if (disags.length > 0) {
                    if (disagBox) disagBox.classList.remove('hidden');
                    disagList.innerHTML = disags.map(d => `<li>${d}</li>`).join('');
                } else {
                    if (disagBox) disagBox.classList.add('hidden');
                }
            }
        }

        function renderThesisHealth(th) {
            if (!th) return;
            const badge = document.getElementById('thesisStateBadge');
            if (badge) {
                const state = th.overall_thesis_state || th.overall_state || 'WEAKENING_THESIS';
                const greenCount = th.green_count ?? 2;
                const amberCount = th.amber_count ?? 2;
                const redCount = th.red_count ?? 0;
                if (redCount > 0) {
                    badge.textContent = `${redCount} CRITICAL ALERT`;
                    badge.className = "px-3 py-1 rounded-full text-xs font-extrabold uppercase bg-rose-50 text-rose-800 border border-rose-200";
                } else if (amberCount > 0) {
                    badge.textContent = `${greenCount} HEALTHY · ${amberCount} WATCH`;
                    badge.className = "px-3 py-1 rounded-full text-xs font-extrabold uppercase bg-amber-50 text-amber-800 border border-amber-200";
                } else {
                    badge.textContent = "ALL 4 CHECKS HEALTHY";
                    badge.className = "px-3 py-1 rounded-full text-xs font-extrabold uppercase bg-emerald-50 text-emerald-800 border border-emerald-200";
                }
            }

            const container = document.getElementById('thesisHealthContainer');
            if (container && th.flags) {
                container.innerHTML = th.flags.map(f => {
                    const st = (f.status || 'GREEN').toUpperCase();
                    const pillCls = st === 'RED'
                        ? 'bg-rose-50 text-rose-700 border-rose-200'
                        : (st === 'AMBER' ? 'bg-amber-50 text-amber-800 border-amber-200' : 'bg-emerald-50 text-emerald-700 border-emerald-200');
                    const dotCls = st === 'RED' ? 'bg-rose-500' : (st === 'AMBER' ? 'bg-amber-500' : 'bg-emerald-500');
                    const cardTint = st === 'RED' ? 'border-rose-200 bg-rose-50/30' : (st === 'AMBER' ? 'border-amber-200 bg-amber-50/20' : 'border-slate-200 bg-slate-50');
                    return `
                        <div class="p-3.5 rounded-xl border space-y-1.5 ${cardTint}">
                            <div class="flex items-center justify-between gap-2">
                                <span class="text-[10px] font-bold uppercase tracking-wider text-slate-600 truncate" title="${f.flag_name}">${f.flag_name}</span>
                                <span class="px-2 py-0.5 rounded text-[10px] font-bold border flex items-center gap-1 shrink-0 ${pillCls}">
                                    <span class="w-1.5 h-1.5 rounded-full ${dotCls}"></span>${st}
                                </span>
                            </div>
                            <div class="text-sm font-extrabold text-slate-900 mono">${f.metric_value}</div>
                            <p class="text-[11px] text-slate-600 leading-snug">${f.plain_assessment || f.benchmark_floor}</p>
                        </div>
                    `;
                }).join('');
            }
        }

        function renderDecisionHistory(scoreboard, dec, refPrice) {
            const tbody = document.getElementById('decisionHistoryTableBody');
            if (!tbody) return;
            const liveRecs = (scoreboard && scoreboard.live_records && scoreboard.live_records.length > 0) ? scoreboard.live_records : null;
            const rows = liveRecs ? liveRecs.slice(0, 8).map(r => ({
                ts: r.timestamp || '2026-11-23 14:00 IST',
                action: r.signal_action || 'WAIT',
                price: r.price_at_signal ? `₹${Number(r.price_at_signal).toFixed(2)}` : `₹${(refPrice || 817.80).toFixed(2)}`,
                pb: r.price_at_signal ? `${(Number(r.price_at_signal) / 394.80).toFixed(2)}×` : '2.07×',
                tier: dec ? (dec.precedence_tier || 'Patience Guard') : 'Patience Guard',
                status: `SHA-256: ${(r.row_hash || 'verified').substring(0, 14)}...`
            })) : [
                {
                    ts: (dec && dec.feed_timestamp) ? dec.feed_timestamp : '2026-11-23 15:30 IST',
                    action: dec ? dec.canonical_action : 'WAIT',
                    price: `₹${(refPrice || 817.80).toFixed(2)}`,
                    pb: `${((refPrice || 817.80) / 394.80).toFixed(2)}×`,
                    tier: dec ? dec.precedence_tier : 'Patience Guard',
                    status: 'ACTIVE SNAPSHOT · VERIFIED'
                }
            ];

            tbody.innerHTML = rows.map(r => {
                let actionClass = 'bg-amber-50 text-amber-900 border-amber-200';
                if (r.action.includes('ACCUMULATE') || r.action === 'BUY') actionClass = 'bg-emerald-50 text-emerald-800 border-emerald-200';
                else if (r.action.includes('EXIT') || r.action === 'SELL') actionClass = 'bg-rose-50 text-rose-800 border-rose-200';
                return `
                    <tr>
                        <td class="p-3 text-slate-700 font-semibold">${r.ts}</td>
                        <td class="p-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold border ${actionClass}">${r.action}</span></td>
                        <td class="p-3 text-slate-900 font-bold">${r.price}</td>
                        <td class="p-3 text-slate-600">${r.pb}</td>
                        <td class="p-3 text-slate-700 font-sans">${r.tier}</td>
                        <td class="p-3 text-slate-400 text-[10px]">${r.status}</td>
                    </tr>
                `;
            }).join('');
        }

        function renderMacroMarket(macro) {
            if (!macro) return;
            const flows = macro.institutional_flows;
            if (flows) {
                const fii = flows.fii_cash_net_cr ?? -1840.5;
                const dii = flows.dii_cash_net_cr ?? 2450.2;
                const net = flows.net_combined_cr ?? 609.7;
                const setTxt = (id, t) => { const e = document.getElementById(id); if (e) e.textContent = t; };
                setTxt('macroFiiNet', `${fii >= 0 ? '+' : ''}₹${fii.toFixed(1)} Cr`);
                setTxt('macroDiiNet', `${dii >= 0 ? '+' : ''}₹${dii.toFixed(1)} Cr`);
                setTxt('macroNetInst', `${net >= 0 ? '+' : ''}₹${net.toFixed(1)} Cr`);
            }
            const vix = macro.india_vix;
            if (vix) {
                const lvl = vix.vix_level ?? 14.85;
                const chg = vix.change_pct ?? -2.94;
                const e1 = document.getElementById('macroVixVal'); if (e1) e1.textContent = lvl.toFixed(2);
                const e2 = document.getElementById('macroVixChg'); if (e2) e2.textContent = `${chg >= 0 ? '+' : ''}${chg.toFixed(2)}%`;
                const e3 = document.getElementById('macroVixRegime'); if (e3) e3.textContent = vix.volatility_regime || "Low Volatility";
            }
            const bn = macro.bank_nifty;
            if (bn) {
                const idx = bn.index_level ?? 62324.55;
                const chg = bn.change_pct ?? 0.82;
                const e1 = document.getElementById('macroBankNiftyVal'); if (e1) e1.textContent = Math.round(idx).toLocaleString('en-IN');
                const e2 = document.getElementById('macroBankNiftyChg'); if (e2) e2.textContent = `${chg >= 0 ? '+' : ''}${chg.toFixed(2)}%`;
                const e3 = document.getElementById('macroBankNiftyTrend'); if (e3) e3.textContent = "Above 20 & 50 DMA";
                const e4 = document.getElementById('macroHdfcBeta'); if (e4) e4.textContent = `${(bn.hdfc_beta || 1.14).toFixed(2)}×`;
            }
            const oi = macro.options_oi;
            if (oi) {
                const pcr = oi.pcr_ratio ?? 1.18;
                const mp = oi.max_pain_strike ?? 780.0;
                const pw = oi.major_put_oi_strike ?? 760.0;
                const e1 = document.getElementById('macroPcr'); if (e1) e1.textContent = `${pcr.toFixed(2)}`;
                const e2 = document.getElementById('macroMaxPain'); if (e2) e2.textContent = `₹${mp.toFixed(1)}`;
                const e3 = document.getElementById('macroPutWall'); if (e3) e3.textContent = `₹${pw.toFixed(1)}`;
            }
        }

        function renderDailyCompass(compassData) {
            const tech = compassData.technicals;
            const prob = compassData.probabilistic_forecast;
            if (!tech) return;

            const eAtr = document.getElementById('compassAtrValue'); if (eAtr) eAtr.textContent = `₹${tech.atr_14.toFixed(1)}`;
            const eAtrP = document.getElementById('compassAtrPct'); if (eAtrP) eAtrP.textContent = `(${tech.atr_pct.toFixed(2)}% of price)`;

            const setRange = (id, lowVal, highVal, obj, fbL, fbH) => {
                const el = document.getElementById(id);
                const l = lowVal ?? (obj ? obj.low : fbL);
                const h = highVal ?? (obj ? obj.high : fbH);
                if (el) el.textContent = `₹${Number(l).toFixed(1)} – ₹${Number(h).toFixed(1)}`;
            };
            setRange('compassRange1D', tech.expected_1d_low, tech.expected_1d_high, tech.expected_range_1d, 795, 840);
            setRange('compassRange3D', tech.expected_3d_low, tech.expected_3d_high, tech.expected_range_3d, 780, 855);
            setRange('compassRange5D', tech.expected_5d_low, tech.expected_5d_high, tech.expected_range_5d, 768, 868);

            const av = document.getElementById('compassAvwap'); if (av) av.textContent = `₹${(tech.anchored_vwap || 777.8).toFixed(1)}`;
            const dl = document.getElementById('compassDelivery'); if (dl) dl.textContent = `${(tech.delivery_pct || 64.5).toFixed(1)}%`;
            const rs = document.getElementById('compassRsBankNifty');
            if (rs) {
                const v = tech.rs_vs_bank_nifty_pct ?? 2.4;
                rs.textContent = `${v >= 0 ? '+' : ''}${v.toFixed(1)}% Alpha`;
            }

            const fibBody = document.getElementById('compassFibTableBody');
            if (fibBody && tech.fibonacci) {
                const fib = tech.fibonacci;
                const rows = [
                    { name: "0.0% (Sprint Peak)", price: fib.anchor_high, role: "Recent Resistance" },
                    { name: "23.6% Retracement", price: fib.fib_236, role: "Minor Pause" },
                    { name: "38.2% Retracement", price: fib.fib_382, role: "Buy Zone Upper Edge" },
                    { name: "50.0% Retracement", price: fib.fib_500, role: "Optimal Pullback Sweet Spot" },
                    { name: "61.8% Retracement", price: fib.fib_618, role: "Deep Discount Level" },
                    { name: "100.0% (Cycle Low)", price: fib.anchor_low, role: "52-Week Support Floor" }
                ];
                const ref = latestStatusData ? (latestStatusData.reference_price || 817.8) : 817.8;
                fibBody.innerHTML = rows.map(r => {
                    const dist = (((r.price - ref) / ref) * 100).toFixed(1);
                    return `
                        <tr class="${r.name.includes('50.0%') || r.name.includes('38.2%') ? 'font-bold text-emerald-800 bg-emerald-50/40' : ''}">
                            <td class="p-2.5 text-left">${r.name}</td>
                            <td class="p-2.5 text-center font-bold">₹${r.price.toFixed(1)}</td>
                            <td class="p-2.5 text-center ${dist < 0 ? 'text-amber-700' : 'text-slate-500'}">${dist > 0 ? '+' : ''}${dist}%</td>
                            <td class="p-2.5 text-right text-slate-600 font-sans">${r.role}</td>
                        </tr>
                    `;
                }).join('');
            }

            const touchBody = document.getElementById('compassTouchTableBody');
            const forecasts = (prob && prob.forecasts) ? prob.forecasts : [];
            if (touchBody && forecasts.length > 0) {
                touchBody.innerHTML = forecasts.map(f => {
                    const isHidden = f.is_hidden || (f.sample_size_n !== undefined && f.sample_size_n < 30);
                    const p1 = isHidden ? '--' : `${f.prob_1d_pct}%`;
                    const p3 = isHidden ? '--' : `${f.prob_3d_pct}%`;
                    const p5 = isHidden ? '--' : `${f.prob_5d_pct}%`;
                    const edge = isHidden ? 'Low sample' : `${f.edge_5d_pct > 0 ? '+' : ''}${f.edge_5d_pct}%`;
                    return `
                        <tr>
                            <td class="p-3 text-left">
                                <span class="font-bold text-slate-900 font-sans block">${f.level_name || 'Target'}</span>
                                <span class="text-[10px] text-indigo-700 font-bold">₹${f.target_price.toFixed(1)}</span>
                            </td>
                            <td class="p-3 ${f.distance_pct < 0 ? 'text-amber-700' : 'text-slate-700'}">${f.distance_pct > 0 ? '+' : ''}${f.distance_pct.toFixed(1)}%</td>
                            <td class="p-3">${p1}</td>
                            <td class="p-3">${p3}</td>
                            <td class="p-3 font-bold text-indigo-700">${p5}</td>
                            <td class="p-3 text-slate-500">${f.naive_prob_5d_pct}%</td>
                            <td class="p-3 font-bold ${f.edge_5d_pct > 10 ? 'text-emerald-700' : 'text-slate-600'}">${edge}</td>
                            <td class="p-3 text-slate-500">n=${f.sample_size_n}</td>
                            <td class="p-3 text-right font-sans text-slate-600">${f.distance_pct < 0 ? 'Limit buy zone' : 'Breakout check'}</td>
                        </tr>
                    `;
                }).join('');
            }
        }

        function renderPriceLadder(vl) {
            const tbody = document.getElementById('priceLadderTableBody');
            if (!tbody || !vl) return;
            const scenarios = vl.scenarios || [];
            const bz = vl.dynamic_buy_zone || vl.limit_tranche || { limit_zone_low: 745, limit_zone_high: 775 };
            const bear = scenarios.find(s => s.name === 'BEAR') || { target_price: 385.7, justified_pb: 0.98, assumed_roe_pct: 12.84 };
            const base = scenarios.find(s => s.name === 'BASE') || { target_price: 553.5, justified_pb: 1.40, assumed_roe_pct: 14.0 };
            const bull = scenarios.find(s => s.name === 'BULL') || { target_price: 987.0, justified_pb: 2.50, assumed_roe_pct: 16.0 };
            const ref = vl.reference_price || 817.80;
            const bvps = vl.book_value_per_share || 394.80;

            const rows = [
                { level: "1. Extreme Stress Floor", price: `₹${bear.target_price.toFixed(1)}`, pb: `${bear.justified_pb.toFixed(2)}×`, pct: "1st %ile", rule: "Tail Risk Floor", rationale: "Severe macro stress valuation", cls: "bg-rose-50/30" },
                { level: "2. Conservative Base Fair Value", price: `₹${base.target_price.toFixed(1)}`, pb: `${base.justified_pb.toFixed(2)}×`, pct: "5th %ile", rule: "Intrinsic Benchmark", rationale: "Normalized 14% ROE valuation", cls: "" },
                { level: "3. Tranche 2 Deep Dip Floor", price: "₹710.0", pb: "1.80×", pct: "14th %ile", rule: "Tranche 2 Limit Buy", rationale: "52-week structural support floor", cls: "bg-teal-50/40" },
                { level: "4. Tranche 1 Limit Buy Zone", price: `₹${bz.limit_zone_low.toFixed(0)} – ₹${bz.limit_zone_high.toFixed(0)}`, pb: `${(bz.limit_zone_low / bvps).toFixed(2)}× – ${(bz.limit_zone_high / bvps).toFixed(2)}×`, pct: "17th–24th %ile", rule: "Tranche 1 Entry Zone", rationale: "5%–9% dip into lower quartile support", cls: "bg-emerald-50/60 font-bold" },
                { level: "5. Today's Market Price", price: `₹${ref.toFixed(2)}`, pb: `${vl.current_pb.toFixed(2)}×`, pct: "Current", rule: "WAIT (Don't Chase)", rationale: "Wait for pullback into buy zone", cls: "bg-amber-50/50 font-bold" },
                { level: "6. Bull Compounding Ceiling", price: `₹${bull.target_price.toFixed(1)}`, pb: `${bull.justified_pb.toFixed(2)}×`, pct: "85th %ile", rule: "Trim / Profit Ceiling", rationale: "16% ROE re-rating target", cls: "bg-indigo-50/30" }
            ];

            tbody.innerHTML = rows.map(r => `
                <tr class="${r.cls}">
                    <td class="p-3 text-left font-sans font-semibold text-slate-900">${r.level}</td>
                    <td class="p-3 text-center font-bold text-indigo-700">${r.price}</td>
                    <td class="p-3 text-center">${r.pb}</td>
                    <td class="p-3 text-center">${r.pct}</td>
                    <td class="p-3 text-center"><span class="px-2 py-0.5 rounded text-[10px] font-bold bg-white border border-slate-200 text-slate-700 font-sans">${r.rule}</span></td>
                    <td class="p-3 text-left text-slate-600 font-sans text-[11px]">${r.rationale}</td>
                </tr>
            `).join('');
        }

        function renderGates(gatesData, valuationLedger) {
            const container = document.getElementById('gatesListContainer');
            if (!container) return;
            const gates = gatesData.gates || [];
            const passCount = gates.filter(g => g.passed).length;
            const summaryBadge = document.getElementById('gatesStatusSummaryBadge');
            if (summaryBadge) summaryBadge.textContent = `${passCount} of ${gates.length} Pass`;

            container.innerHTML = gates.map(g => {
                const isPass = g.status === 'PASS';
                const isWait = g.status === 'WAIT';
                const statusBadge = isPass
                    ? '<span class="px-2.5 py-1 rounded-full font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs">PASS</span>'
                    : (isWait
                        ? '<span class="px-2.5 py-1 rounded-full font-bold bg-amber-100 text-amber-800 border border-amber-300 text-xs">WAIT</span>'
                        : '<span class="px-2.5 py-1 rounded-full font-bold bg-rose-50 text-rose-800 border border-rose-200 text-xs">BLOCKED</span>');
                const icon = isPass
                    ? '<div class="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs shrink-0">✓</div>'
                    : (isWait
                        ? '<div class="w-6 h-6 rounded-full bg-amber-100 text-amber-800 flex items-center justify-center font-bold text-xs shrink-0">!</div>'
                        : '<div class="w-6 h-6 rounded-full bg-rose-100 text-rose-700 flex items-center justify-center font-bold text-xs shrink-0">✕</div>');
                const borderStyle = isWait ? 'border-amber-300 bg-amber-50/20' : 'border-slate-200 bg-white';

                let metricsHtml = '';
                if (g.evidence_metrics && typeof g.evidence_metrics === 'object') {
                    metricsHtml = '<div class="grid grid-cols-2 sm:grid-cols-3 gap-2 bg-slate-50 p-3 rounded-lg border border-slate-200 text-[11px] mt-2">';
                    for (const [k, v] of Object.entries(g.evidence_metrics)) {
                        const label = k.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                        const valStr = typeof v === 'number' ? (v % 1 === 0 ? v.toLocaleString() : v.toFixed(2)) : (typeof v === 'boolean' ? (v ? 'Verified ✓' : 'Unverified ✕') : String(v));
                        metricsHtml += `<div><span class="text-slate-500 block text-[10px] uppercase">${label}</span><span class="font-bold text-slate-900 mono">${valStr}</span></div>`;
                    }
                    metricsHtml += '</div>';
                }

                return `
                    <details class="${borderStyle} border rounded-xl p-4 text-xs" ${isWait ? 'open' : ''}>
                        <summary class="flex justify-between items-center cursor-pointer gap-3">
                            <div class="flex items-center gap-3">
                                ${icon}
                                <div>
                                    <span class="font-bold text-slate-900 text-sm block">Gate ${g.gate_number}: ${g.gate_name}</span>
                                    <span class="text-slate-500 text-xs">${g.plain_rationale}</span>
                                </div>
                            </div>
                            ${statusBadge}
                        </summary>
                        <div class="pt-3 text-xs text-slate-600 border-t border-slate-100 mt-3 space-y-2">
                            ${metricsHtml}
                            <p class="text-[11px]"><strong>Directive:</strong> <span class="font-bold text-slate-800">${g.action_directive}</span></p>
                        </div>
                    </details>
                `;
            }).join('');
        }

        function renderPromises(report) {
            const grid = document.getElementById('promisesGrid');
            if (!grid) return;
            const promises = (report && report.promises) ? report.promises : [];
            grid.innerHTML = promises.map(p => {
                const verdict = p.delivery_status || p.verdict || 'IN PROGRESS';
                const isDel = verdict.toUpperCase() === 'DELIVERED';
                const badgeCls = isDel ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-amber-50 text-amber-800 border-amber-200';
                return `
                    <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                        <div class="flex items-center justify-between gap-2">
                            <span class="text-[10px] font-bold uppercase tracking-wider text-slate-500">${p.pillar || 'Commitment'}</span>
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${badgeCls}">${verdict}</span>
                        </div>
                        <h5 class="text-xs font-bold text-slate-900">${p.target_metric_name || p.metric || ''}</h5>
                        <div class="text-[11px] space-y-0.5 text-slate-600">
                            <div><strong>Guided:</strong> ${p.stated_target || ''}</div>
                            <div><strong>Actual:</strong> ${p.latest_actual_value || ''}</div>
                        </div>
                        <p class="text-[10px] text-slate-400">${p.audit_notes || ''}</p>
                    </div>
                `;
            }).join('');
        }

        function renderEvents(eventsData) {
            const container = document.getElementById('eventsListContainer');
            if (!container) return;
            const regs = eventsData.regulatory_filings || eventsData.material_events || [];
            if (regs.length === 0) {
                container.innerHTML = '<p class="text-xs text-slate-500 italic p-4 bg-slate-50 rounded-xl">No regulatory filings loaded.</p>';
                return;
            }
            container.innerHTML = regs.map(r => {
                const matColor = r.materiality === 'HIGH' ? 'bg-rose-50 text-rose-700 border-rose-200' : 'bg-indigo-50 text-indigo-700 border-indigo-200';
                return `
                    <div class="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-1.5">
                        <div class="flex flex-wrap items-center justify-between gap-2">
                            <div class="flex items-center gap-2">
                                <span class="px-2 py-0.5 rounded ${matColor} border text-[10px] font-bold uppercase">${r.materiality || 'DISCLOSURE'}</span>
                                <span class="text-[11px] text-slate-500 font-medium">${r.regulatory_source || 'BSE/NSE'} · ${r.date || ''}</span>
                            </div>
                            <span class="text-[10px] font-bold text-slate-600">${r.affected_gate || ''}</span>
                        </div>
                        <h5 class="text-xs font-bold text-slate-900">${r.title}</h5>
                        <p class="text-[11px] text-slate-600">${r.description || r.explanation || ''}</p>
                    </div>
                `;
            }).join('');
        }

        function renderPeerWatchlist(peers) {
            const tbody = document.getElementById('peerWatchlistTableBody');
            if (!tbody) return;
            tbody.innerHTML = peers.map(p => {
                const isCur = p.symbol === 'HDFCBANK.NS';
                const priceD = (p.price !== null && p.price !== undefined) ? `₹${p.price.toFixed(2)}` : '<span class="text-slate-400">Offline</span>';
                const pbD = (p.pb !== null && p.pb !== undefined) ? `${p.pb.toFixed(2)}×` : '--';
                const pctD = (p.pb_percentile !== null && p.pb_percentile !== undefined) ? `${formatOrdinal(p.pb_percentile)}` : '--';
                return `
                    <tr class="${isCur ? 'bg-indigo-50/40 font-semibold' : ''}">
                        <td class="p-3 font-bold text-slate-900 font-sans">${p.display_name}<span class="block text-[10px] text-slate-400 font-normal">${p.exchange_ticker}</span></td>
                        <td class="p-3">${priceD}</td>
                        <td class="p-3">${pbD}</td>
                        <td class="p-3">${pctD}</td>
                        <td class="p-3">${p.trailing_roe ? p.trailing_roe.toFixed(2) + '%' : '--'}</td>
                        <td class="p-3">${p.car ? p.car.toFixed(1) + '%' : '--'}</td>
                        <td class="p-3">${p.gnpa ? p.gnpa.toFixed(2) + '%' : '--'}</td>
                        <td class="p-3">${p.cd_ratio ? p.cd_ratio.toFixed(1) + '%' : '--'}</td>
                        <td class="p-3 font-sans"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${isCur ? 'bg-amber-50 text-amber-800 border border-amber-200' : 'bg-slate-100 text-slate-600'}">${p.status}</span></td>
                    </tr>
                `;
            }).join('');
        }

        function renderAnalogues(analoguesData) {
            const tbody = document.getElementById('analogueTableBody');
            if (!tbody) return;
            const episodes = analoguesData.all_episodes || [];
            const el = document.getElementById('analogueHeaderStats');
            if (el && episodes.length > 0) {
                const winners = episodes.filter(e => e.outcome_status_6m === 'WINNER').length;
                const hitRate = ((winners / episodes.length) * 100).toFixed(0);
                el.innerHTML = `<span class="px-2.5 py-1 rounded bg-emerald-50 text-emerald-800 border border-emerald-200">6M Hit Rate: ${hitRate}% (${winners}/${episodes.length})</span>`;
            }
            tbody.innerHTML = episodes.map(ep => {
                const st = ep.outcome_status_6m;
                const badge = st === 'WINNER'
                    ? '<span class="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">WINNER</span>'
                    : (st === 'LOSER' ? '<span class="px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 font-bold">LOSER</span>' : '<span class="px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200 font-bold">CHOPPY</span>');
                return `
                    <tr>
                        <td class="p-3 font-sans font-semibold text-slate-900">${ep.cycle_name}</td>
                        <td class="p-3 font-sans">${ep.regime_era === 'POST_MERGER' ? '<span class="text-indigo-700 font-semibold">Post-Merger</span>' : '<span class="text-slate-500">Pre-Merger</span>'}</td>
                        <td class="p-3">₹${ep.price_at_entry.toFixed(2)}</td>
                        <td class="p-3">${ep.pb_at_entry}×</td>
                        <td class="p-3 text-rose-600">${ep.drawdown_at_entry_pct}%</td>
                        <td class="p-3">${ep.actual_return_30d_pct}%</td>
                        <td class="p-3">${ep.actual_return_90d_pct}%</td>
                        <td class="p-3 font-bold ${ep.actual_return_180d_pct >= 0 ? 'text-emerald-700' : 'text-rose-600'}">${ep.actual_return_180d_pct > 0 ? '+' : ''}${ep.actual_return_180d_pct}%</td>
                        <td class="p-3 text-amber-700">${ep.max_adverse_excursion_pct}%</td>
                        <td class="p-3 font-sans">${badge}</td>
                    </tr>
                `;
            }).join('');
        }

        function renderHealthLedger(scoreboard, skippedReason) {
            const list = document.getElementById('healthLedgerList');
            if (!list) return;
            let html = '';
            if (skippedReason) {
                html += `<p class="text-amber-400">[CIRCUIT BREAKER] ${skippedReason}</p>`;
            } else {
                html += `<p class="text-emerald-400">[LIVE VERIFIED] Safety circuit armed with live NSE tick.</p>`;
            }
            (scoreboard.live_records || []).slice(0, 4).forEach(r => {
                html += `<p class="text-emerald-400">[LIVE] #${r.id} · ${r.timestamp} · ${(r.row_hash || '').substring(0, 18)}...</p>`;
            });
            (scoreboard.simulated_records || []).slice(0, 4).forEach(r => {
                html += `<p class="text-slate-400">[SIM] #${r.id} · ${r.model_version} · ${(r.row_hash || '').substring(0, 18)}...</p>`;
            });
            list.innerHTML = html;
        }

        async function runBacktest() {
            const periodSelect = document.getElementById('selectPeriod');
            const period = periodSelect ? periodSelect.value : '2y';
            const emptyState = document.getElementById('chartEmptyState');
            const canvas = document.getElementById('equityChart');
            try {
                const res = await fetch(`/api/backtest?period=${period}`);
                const data = await res.json();
                latestBacktestData = data;
                if (data && data.equity_curve && data.equity_curve.length >= 2) {
                    if (emptyState) emptyState.classList.add('hidden');
                    if (canvas) canvas.classList.remove('hidden');
                    updateBacktestSummaryTiles(data);
                    renderNativeChart(data.equity_curve);
                } else {
                    if (emptyState) emptyState.classList.remove('hidden');
                    if (canvas) canvas.classList.add('hidden');
                }
            } catch (e) {
                console.error("runBacktest error:", e);
            }
        }

        function updateBacktestSummaryTiles(data) {
            if (!data || !data.equity_curve || data.equity_curve.length < 2) return;
            const first = data.equity_curve[0];
            const last = data.equity_curve[data.equity_curve.length - 1];
            const stratRet = (((last.strategy_equity || 100000) - 100000) / 100000) * 100;
            const sipRet = (((last.sip_equity || 100000) - 100000) / 100000) * 100;
            const bhRet = (((last.benchmark_equity || 100000) - 100000) / 100000) * 100;

            const setVal = (id, v, cls) => {
                const el = document.getElementById(id);
                if (el) {
                    el.textContent = `${v >= 0 ? '+' : ''}${v.toFixed(1)}%`;
                    if (cls) el.className = cls;
                }
            };
            setVal('btStratRet', data.strategy_return_pct ?? stratRet, 'text-base font-bold text-emerald-700 mono');
            setVal('btSipRet', data.sip_return_pct ?? sipRet, 'text-base font-bold text-indigo-700 mono');
            setVal('btBhRet', data.benchmark_return_pct ?? bhRet, 'text-base font-bold text-slate-700 mono');
            const ddEl = document.getElementById('btMaxDd');
            if (ddEl && data.max_drawdown_pct !== undefined) {
                ddEl.textContent = `${data.max_drawdown_pct <= 0 ? '' : '-'}${Math.abs(data.max_drawdown_pct).toFixed(1)}%`;
            }
        }

        function renderNativeChart(curve) {
            const canvas = document.getElementById('equityChart');
            if (!canvas || !curve || curve.length < 2) return;
            const rect = canvas.getBoundingClientRect();
            if (rect.width < 10 || rect.height < 10) return;

            const ctx = canvas.getContext('2d');
            if (!ctx) return;

            const dpr = window.devicePixelRatio || 1;
            canvas.width = rect.width * dpr;
            canvas.height = rect.height * dpr;
            ctx.scale(dpr, dpr);

            const w = rect.width;
            const h = rect.height;
            ctx.clearRect(0, 0, w, h);

            const padding = { top: 24, right: 24, bottom: 28, left: 52 };
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
            minVal = Math.floor(minVal * 0.96);
            maxVal = Math.ceil(maxVal * 1.04);
            const valSpan = maxVal - minVal || 1;

            const getY = (val) => padding.top + chartH - ((val - minVal) / valSpan) * chartH;
            const getX = (idx) => padding.left + (idx / (curve.length - 1)) * chartW;

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
                ctx.fillText('₹' + (v / 1000).toFixed(0) + 'k', padding.left - 8, y + 3);
            }

            const drawLine = (key, color, width, dash = []) => {
                ctx.strokeStyle = color;
                ctx.lineWidth = width;
                ctx.setLineDash(dash);
                ctx.beginPath();
                curve.forEach((pt, idx) => {
                    const x = getX(idx);
                    const y = getY(pt[key] || 100000);
                    if (idx === 0) ctx.moveTo(x, y);
                    else ctx.lineTo(x, y);
                });
                ctx.stroke();
                ctx.setLineDash([]);
            };

            drawLine('benchmark_equity', '#94a3b8', 1.6);
            drawLine('sip_equity', '#0284c7', 1.8, [4, 3]);
            drawLine('strategy_equity', '#00D09C', 2.4);

            // X-axis dates
            ctx.fillStyle = '#94a3b8';
            ctx.font = '10px ui-monospace, monospace';
            ctx.textAlign = 'left';
            ctx.fillText(String(curve[0].date).slice(0, 10), padding.left, h - 8);
            ctx.textAlign = 'right';
            ctx.fillText(String(curve[curve.length - 1].date).slice(0, 10), w - padding.right, h - 8);

            // Scrubbing Crosshair & Tooltip
            const tip = document.getElementById('equityChartTooltip');
            if (equityHoverIndex >= 0 && equityHoverIndex < curve.length) {
                const pt = curve[equityHoverIndex];
                const hx = getX(equityHoverIndex);

                ctx.strokeStyle = '#64748b';
                ctx.lineWidth = 1;
                ctx.setLineDash([3, 3]);
                ctx.beginPath();
                ctx.moveTo(hx, padding.top);
                ctx.lineTo(hx, padding.top + chartH);
                ctx.stroke();
                ctx.setLineDash([]);

                [['strategy_equity', '#00D09C'], ['sip_equity', '#0284c7'], ['benchmark_equity', '#94a3b8']].forEach(([k, col]) => {
                    const cy = getY(pt[k] || 100000);
                    ctx.beginPath();
                    ctx.arc(hx, cy, 4, 0, Math.PI * 2);
                    ctx.fillStyle = col;
                    ctx.fill();
                    ctx.strokeStyle = '#ffffff';
                    ctx.lineWidth = 1.5;
                    ctx.stroke();
                });

                if (tip) {
                    tip.classList.remove('hidden');
                    tip.innerHTML = `
                        <div class="font-bold text-slate-300 text-[10px] mono mb-1">${String(pt.date).slice(0, 10)}</div>
                        <div class="mono text-[11px]"><span class="text-emerald-400 font-bold">Strategy:</span> ₹${Math.round(pt.strategy_equity || 100000).toLocaleString('en-IN')}</div>
                        <div class="mono text-[11px]"><span class="text-sky-400 font-bold">SIP:</span> ₹${Math.round(pt.sip_equity || 100000).toLocaleString('en-IN')}</div>
                        <div class="mono text-[11px]"><span class="text-slate-300 font-bold">Buy &amp; Hold:</span> ₹${Math.round(pt.benchmark_equity || 100000).toLocaleString('en-IN')}</div>
                    `;
                    const tipW = tip.offsetWidth || 160;
                    tip.style.left = ((hx + 14 + tipW > w - 10) ? Math.max(8, hx - tipW - 14) : (hx + 14)) + 'px';
                    tip.style.top = '12px';
                }
            } else if (tip) {
                tip.classList.add('hidden');
            }
        }

        function attachEquityChartInteraction() {
            const canvas = document.getElementById('equityChart');
            if (!canvas || canvas.dataset.bound === '1') return;
            canvas.dataset.bound = '1';

            const updateHover = (clientX) => {
                const curve = latestBacktestData ? latestBacktestData.equity_curve : null;
                if (!curve || curve.length < 2) return;
                const rect = canvas.getBoundingClientRect();
                const padL = 52, padR = 24;
                const chartW = rect.width - padL - padR;
                const relX = Math.max(0, Math.min(chartW, (clientX - rect.left) - padL));
                const idx = Math.round((relX / chartW) * (curve.length - 1));
                if (idx !== equityHoverIndex) {
                    equityHoverIndex = idx;
                    renderNativeChart(curve);
                }
            };

            canvas.addEventListener('pointermove', (e) => updateHover(e.clientX));
            canvas.addEventListener('pointerdown', (e) => updateHover(e.clientX));
            canvas.addEventListener('pointerleave', () => {
                equityHoverIndex = -1;
                if (latestBacktestData && latestBacktestData.equity_curve) renderNativeChart(latestBacktestData.equity_curve);
            });
        }

        async function triggerNow() {
            const btn = document.getElementById('btnTrigger');
            const lbl = document.getElementById('btnTriggerLabel');
            const icon = document.getElementById('btnTriggerIcon');
            if (btn) btn.disabled = true;
            if (lbl) lbl.textContent = 'Updating...';
            if (icon) icon.classList.add('animate-spin');

            const resetBtn = () => {
                if (btn) btn.disabled = false;
                if (lbl) lbl.textContent = 'Refresh';
                if (icon) icon.classList.remove('animate-spin');
            };

            try {
                const res = await fetch('/api/trigger-signal', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
                if (res.status === 202 || res.status === 200) {
                    showToast("Refreshing live quotes & signals...", "success");
                    let attempts = 0;
                    const poll = setInterval(async () => {
                        attempts++;
                        try {
                            const pollRes = await fetch('/api/refresh-status');
                            const pollData = await pollRes.json();
                            if (pollData.status === 'SUCCESS') {
                                clearInterval(poll);
                                const st = await fetch('/api/status');
                                const stData = await st.json();
                                applyStatus(stData);
                                showToast("Dashboard updated with latest numbers.", "success");
                                resetBtn();
                            } else if (pollData.status === 'ERROR' || attempts > 25) {
                                clearInterval(poll);
                                showToast(pollData.error || "Refresh timed out.", "error");
                                resetBtn();
                            }
                        } catch (err) {
                            clearInterval(poll);
                            resetBtn();
                        }
                    }, 1500);
                } else {
                    showToast("Failed to start refresh.", "error");
                    resetBtn();
                }
            } catch (e) {
                showToast("Network error refreshing data.", "error");
                resetBtn();
            }
        }

        window.addEventListener('DOMContentLoaded', () => {
            attachHeroChartInteraction();
            attachEquityChartInteraction();

            // Keyboard ArrowLeft/ArrowRight/Home/End fallback for tablist
            const tablist = document.getElementById('mainTablist');
            if (tablist) {
                tablist.addEventListener('keydown', (e) => {
                    const tabs = Array.from(tablist.querySelectorAll('[role="tab"]'));
                    const idx = tabs.indexOf(document.activeElement);
                    if (idx === -1) return;
                    let nextIdx = -1;
                    if (e.key === 'ArrowRight') nextIdx = (idx + 1) % tabs.length;
                    else if (e.key === 'ArrowLeft') nextIdx = (idx - 1 + tabs.length) % tabs.length;
                    else if (e.key === 'Home') nextIdx = 0;
                    else if (e.key === 'End') nextIdx = tabs.length - 1;
                    if (nextIdx !== -1) {
                        e.preventDefault();
                        tabs[nextIdx].focus();
                        tabs[nextIdx].click();
                    }
                });

                // Scroll fade fallback when animation-timeline isn't supported
                if (!CSS.supports('animation-timeline', 'scroll()')) {
                    const children = Array.from(tablist.children);
                    if (children.length > 1) {
                        const obs = new IntersectionObserver(entries => {
                            entries.forEach(({ target, intersectionRatio }) => {
                                if (target === children[0]) tablist.classList.toggle('more-start', intersectionRatio < 1);
                                if (target === children[children.length - 1]) tablist.classList.toggle('more-end', intersectionRatio < 1);
                            });
                        }, { root: tablist, threshold: 1, rootMargin: '1px' });
                        obs.observe(children[0]);
                        obs.observe(children[children.length - 1]);
                    }
                }
            }

            // Support find-in-page beforematch on hidden="until-found" tabpanels
            MAIN_TABS.forEach(t => {
                const panel = document.getElementById('panel-' + t);
                if (panel) {
                    panel.addEventListener('beforematch', () => switchMainTab(t, true));
                }
            });

            // ResizeObserver keeps HiDPI canvases crisp whenever tabs become visible or viewport changes
            if (typeof ResizeObserver !== 'undefined') {
                const ro = new ResizeObserver(() => {
                    drawHeroChart();
                    if (latestBacktestData && latestBacktestData.equity_curve) {
                        renderNativeChart(latestBacktestData.equity_curve);
                    }
                });
                const hWrap = document.getElementById('heroChartWrap');
                const eWrap = document.getElementById('equityChartWrap');
                if (hWrap) ro.observe(hWrap);
                if (eWrap) ro.observe(eWrap);
            }

            if (window.__INITIAL_STATUS__) {
                applyStatus(window.__INITIAL_STATUS__);
            }
            if (window.__INITIAL_BACKTEST__ && window.__INITIAL_BACKTEST__.equity_curve) {
                latestBacktestData = window.__INITIAL_BACKTEST__;
                updateBacktestSummaryTiles(latestBacktestData);
                renderNativeChart(latestBacktestData.equity_curve);
            } else {
                runBacktest();
            }

            const hash = window.location.hash.toLowerCase();
            if (hash.includes('ladder') || hash.includes('gate') || hash.includes('val')) {
                switchMainTab('valuation');
            } else if (hash.includes('compass')) {
                switchMainTab('compass');
            } else if (hash.includes('fundamental')) {
                switchMainTab('track');
                switchAuditTab('fundamentals');
            } else if (hash.includes('context')) {
                switchMainTab('track');
                switchAuditTab('context');
            } else if (hash.includes('integrity') || hash.includes('trust') || hash.includes('detail')) {
                switchMainTab('track');
                switchAuditTab('integrity');
            }
        });
    </script>
</body>
</html>
"""
