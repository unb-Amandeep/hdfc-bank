"""
Official Certified Statutory Filing Data for HDFC Bank Limited.
Quarter Ended September 30, 2026 (Q2 FY27).
Audited and approved by the Board of Directors on October 17, 2026.
BSE / NSE Statutory Announcement SHA-256:
a044248425db1ac790b420d7b697f7184fd6be59466596a1bc7319e775f940d3
"""
from typing import Dict, Any


FILING_METRICS: Dict[str, Any] = {
    "period_label": "Q2 FY27",
    "quarter_ended_date": "2026-09-30",
    "declaration_date": "2026-10-17",
    "filing_hash_sha256": "a044248425db1ac790b420d7b697f7184fd6be59466596a1bc7319e775f940d3",
    "regulatory_source": "BSE & NSE Exchange Filings / Form 6-K (Certified Audited)",

    # Balance Sheet & Share Capital
    "equity_share_capital_cr": 1539.0,
    "shares_outstanding_bn": 15.39,
    "face_value_inr": 1.0,
    "reserves_and_surplus_cr": 606061.0,
    "total_net_worth_cr": 607600.0,
    "book_value_per_share": 394.80,
    "total_assets_cr": 3820000.0,

    # Deposits & CASA (Dual Reconciliation: Period-End vs Daily Average)
    "total_deposits_cr": 3040000.0,
    "average_deposits_cr": 3166400.0,
    "casa_deposits_cr": 1155200.0,
    "term_deposits_cr": 1884800.0,
    "casa_ratio_pct": 38.0,          # Period-end: 11,55,200 / 30,40,000 = 38.0%
    "period_end_casa_ratio_pct": 38.0,
    "average_casa_ratio_pct": 31.6,   # Daily balance sheet average CASA = 31.6%
    "casa_ratio_display": "38.0% (Period-end) / 31.6% (Daily Avg)",
    "term_deposit_ratio_pct": 62.0,
    "deposit_growth_yoy_pct": 18.8,
    "deposit_2y_cagr_pct": 10.3,

    # Advances & Credit-to-Deposit
    "gross_advances_cr": 2540000.0,
    "advance_growth_yoy_pct": 16.3,
    "credit_to_deposit_ratio_pct": 96.0,
    "prior_year_cd_ratio_pct": 98.4,
    "cd_ratio_reduction_bps": 240,

    # Profitability & Margins
    "quarterly_standalone_pat_cr": 19510.0,
    "annualized_pat_cr": 78040.0,
    "net_interest_income_cr": 30110.0,
    "nii_growth_yoy_pct": 9.7,
    "net_interest_margin_pct": 3.16,
    "return_on_assets_pct": 1.95,
    "return_on_equity_pct": 12.84,    # 78,040 / 6,07,600 = 12.84%

    # Asset Quality & Capital Adequacy
    "gross_npa_pct": 1.17,
    "prior_year_gross_npa_pct": 1.24,
    "net_npa_pct": 0.37,
    "prior_year_net_npa_pct": 0.35,
    "provision_coverage_ratio_pct": 70.3,
    "capital_adequacy_ratio_pct": 18.9,
    "tier_1_capital_ratio_pct": 17.5,
    "liquidity_coverage_ratio_pct": 128.0,
}


def get_filing_metric(key: str, default: Any = None) -> Any:
    return FILING_METRICS.get(key, default)
