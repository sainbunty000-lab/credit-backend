from collections import defaultdict
from utils.safe_math import default_zero
import statistics
from datetime import datetime

RISK_KEYWORDS = ["gambling", "crypto", "bet", "casino", "loan settlement"]

def analyze_banking(transactions, months_count=3):
    account_summary = {}
    monthly_data = defaultdict(lambda: {"credit": 0, "debit": 0})

    total_credit = 0
    total_debit = 0
    bounce_count = 0
    fraud_flags = 0
    balances = []

    # --- STEP 1: Account-Level & Monthly Aggregation ---
    for t in transactions:
        credit = default_zero(t.get("credit"))
        debit = default_zero(t.get("debit"))
        desc = str(t.get("desc", "")).lower()
        account = t.get("account", "unknown")
        date_str = t.get("date")

        total_credit += credit
        total_debit += debit

        # Bounce detection
        if "return" in desc or "bounce" in desc:
            bounce_count += 1

        # Fraud keyword detection
        if any(keyword in desc for keyword in RISK_KEYWORDS):
            fraud_flags += 1

        # Monthly grouping
        if date_str:
            month_key = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m")
            monthly_data[month_key]["credit"] += credit
            monthly_data[month_key]["debit"] += debit

        # Account summary
        if account not in account_summary:
            account_summary[account] = {"credit": 0, "debit": 0}
        account_summary[account]["credit"] += credit
        account_summary[account]["debit"] += debit

    # --- STEP 2: Inter-Account Transfer Detection ---
    # Detect matching credit/debit within small range
    inter_account_adjustment = 0
    for t1 in transactions:
        for t2 in transactions:
            if (
                t1 != t2
                and abs(default_zero(t1.get("credit")) - default_zero(t2.get("debit"))) < 5
            ):
                inter_account_adjustment += default_zero(t1.get("credit"))

    total_credit -= inter_account_adjustment
    total_debit -= inter_account_adjustment

    # --- STEP 3: Consolidated Metrics ---
    months = max(1, months_count)
    avg_credit = total_credit / months
    avg_debit = total_debit / months
    net_surplus = avg_credit - avg_debit

    # --- STEP 4: Consistency Score ---
    monthly_surplus_list = [
        m["credit"] - m["debit"] for m in monthly_data.values()
    ]
    consistency_score = 1
    if len(monthly_surplus_list) > 1:
        std_dev = statistics.stdev(monthly_surplus_list)
        consistency_score = max(0, 1 - (std_dev / max(1, avg_credit)))

    # --- STEP 5: Liquidity Score ---
    liquidity_score = 1 if net_surplus > 0 else 0

    # --- STEP 6: Bounce Score ---
    bounce_score = max(0, 1 - (bounce_count / 5))

    # --- STEP 7: Fraud Score ---
    fraud_score = max(0, 1 - (fraud_flags / 3))

    # --- STEP 8: Surplus Score ---
    surplus_score = 1 if net_surplus > 0 else 0

    # --- FINAL HYGIENE SCORE ---
    hygiene_score = round(
        (
            surplus_score * 0.25
            + bounce_score * 0.20
            + consistency_score * 0.15
            + liquidity_score * 0.10
            + fraud_score * 0.10
        )
        * 100,
        2,
    )

    hygiene_status = (
        "Strong" if hygiene_score >= 75
        else "Moderate" if hygiene_score >= 50
        else "Risky"
    )

    return {
        "account_summary": account_summary,
        "consolidated": {
            "avg_monthly_credit": round(avg_credit, 2),
            "avg_monthly_debit": round(avg_debit, 2),
            "net_monthly_surplus": round(net_surplus, 2),
        },
        "monthly_breakdown": monthly_data,
        "bounce_count": bounce_count,
        "fraud_flags": fraud_flags,
        "hygiene_score": hygiene_score,
        "hygiene_status": hygiene_status,
    }
