"""
transaction_anomaly_detector.py
--------------------------------
Reads a CSV of financial transactions, flags anomalies using statistical
and rule-based methods, and outputs a clean anomaly report.

Author: Shawn Ghodrati
GitHub: github.com/shawngh
"""

import csv
import statistics
import json
from datetime import datetime


# ── CONFIG ──────────────────────────────────────────────────────────────────

# Variance thresholds by rule
THRESHOLDS = {
    "large_variance_abs":   10000,   # flag if absolute variance > $10,000
    "large_variance_pct":   0.05,    # flag if variance > 5% of expected amount
    "zscore_cutoff":        2.0,     # flag if z-score of variance > 2.0
    "zero_expected":        True,    # flag if expected amount is 0 (returned payment)
    "zero_variance_types":  ["Deposit", "Withdrawal"],  # flag $0 variance on these types
}

RISK_RULES = {
    "High":   lambda abs_var, pct, zscore: abs_var >= 10000 or zscore >= 3.0,
    "Medium": lambda abs_var, pct, zscore: abs_var >= 1000  or zscore >= 2.0,
    "Low":    lambda abs_var, pct, zscore: abs_var > 0,
}


# ── HELPERS ──────────────────────────────────────────────────────────────────

def clean_currency(value):
    """Convert '$1,234.56' or '1234.56' to float."""
    if isinstance(value, (int, float)):
        return float(value)
    return float(str(value).replace("$", "").replace(",", "").strip() or 0)


def assign_risk(abs_variance, pct_variance, zscore):
    if RISK_RULES["High"](abs_variance, pct_variance, zscore):
        return "High"
    if RISK_RULES["Medium"](abs_variance, pct_variance, zscore):
        return "Medium"
    return "Low"


def flag_reasons(row, abs_variance, pct_variance, zscore):
    """Return a list of triggered anomaly flags for a transaction."""
    flags = []
    expected = row["expected_amount"]
    txn_type = row["transaction_type"].strip()

    if abs_variance >= THRESHOLDS["large_variance_abs"]:
        flags.append(f"Large absolute variance: ${abs_variance:,.2f}")

    if expected > 0 and pct_variance >= THRESHOLDS["large_variance_pct"]:
        flags.append(f"Variance exceeds {THRESHOLDS['large_variance_pct']*100:.0f}% of expected ({pct_variance*100:.1f}%)")

    if zscore >= THRESHOLDS["zscore_cutoff"]:
        flags.append(f"Statistical outlier: z-score {zscore:.2f}")

    if THRESHOLDS["zero_expected"] and expected == 0:
        flags.append("Expected amount is $0 — possible returned payment or unrecorded transaction")

    if row["variance"] == 0 and txn_type in THRESHOLDS["zero_variance_types"]:
        flags.append(f"Zero variance on {txn_type} — verify settlement received")

    if not flags:
        flags.append("Minor variance — within normal tolerance")

    return flags


def recommended_action(risk, txn_type, flag_list):
    """Generate a recommended action based on risk and transaction type."""
    if "returned payment" in " ".join(flag_list).lower():
        return "Notify client immediately and verify originating bank details before reprocessing."
    if "zero variance" in " ".join(flag_list).lower():
        return f"Confirm {txn_type.lower()} settlement was received and posted correctly."
    if risk == "High":
        return "Escalate to senior operations immediately — resolve before market open."
    if risk == "Medium":
        return "Review trade confirmation and counterparty details by end of day."
    return "Monitor and document — no immediate action required."


# ── CORE FUNCTIONS ────────────────────────────────────────────────────────────

def load_transactions(filepath):
    """Load transactions from a CSV file."""
    transactions = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                transactions.append({
                    "transaction_id":   row.get("Transaction ID", "").strip(),
                    "date":             row.get("Date", "").strip(),
                    "amount":           clean_currency(row.get("Amount", 0)),
                    "expected_amount":  clean_currency(row.get("Expected Amount", 0)),
                    "variance":         clean_currency(row.get("Variance", 0)),
                    "account_type":     row.get("Account Type", "").strip(),
                    "transaction_type": row.get("Transaction Type", "").strip(),
                    "flag_reason":      row.get("Flag Reason", "").strip(),
                })
            except Exception as e:
                print(f"  Skipping row due to error: {e}")
    return transactions


def compute_statistics(transactions):
    """Compute mean and stdev of absolute variances for z-score calculation."""
    abs_variances = [abs(t["variance"]) for t in transactions]
    mean   = statistics.mean(abs_variances) if abs_variances else 0
    stdev  = statistics.stdev(abs_variances) if len(abs_variances) > 1 else 1
    return mean, stdev


def detect_anomalies(transactions):
    """Run anomaly detection on all transactions."""
    mean, stdev = compute_statistics(transactions)
    anomalies = []

    for txn in transactions:
        abs_var  = abs(txn["variance"])
        pct_var  = abs_var / txn["expected_amount"] if txn["expected_amount"] > 0 else 0
        zscore   = (abs_var - mean) / stdev if stdev > 0 else 0
        flags    = flag_reasons(txn, abs_var, pct_var, zscore)
        risk     = assign_risk(abs_var, pct_var, zscore)
        action   = recommended_action(risk, txn["transaction_type"], flags)

        anomalies.append({
            **txn,
            "abs_variance":   abs_var,
            "pct_variance":   round(pct_var * 100, 2),
            "zscore":         round(zscore, 2),
            "risk":           risk,
            "flags":          flags,
            "action":         action,
        })

    # Sort by risk then abs variance descending
    risk_order = {"High": 0, "Medium": 1, "Low": 2, "Review": 3}
    anomalies.sort(key=lambda x: (risk_order.get(x["risk"], 4), -x["abs_variance"]))
    return anomalies


# ── REPORT OUTPUT ─────────────────────────────────────────────────────────────

def print_report(anomalies):
    """Print a clean, formatted exception report to the console."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total_variance = sum(a["abs_variance"] for a in anomalies)
    high   = [a for a in anomalies if a["risk"] == "High"]
    medium = [a for a in anomalies if a["risk"] == "Medium"]
    low    = [a for a in anomalies if a["risk"] == "Low"]

    print("\n" + "═" * 72)
    print("  DAILY TRANSACTION EXCEPTION REPORT")
    print(f"  Generated: {now}")
    print(f"  Total Transactions Analyzed: {len(anomalies)}")
    print(f"  Total Absolute Variance: ${total_variance:,.2f}")
    print("═" * 72)

    print(f"\n  RISK SUMMARY")
    print(f"  {'High':<12} {len(high):>3} exceptions")
    print(f"  {'Medium':<12} {len(medium):>3} exceptions")
    print(f"  {'Low':<12} {len(low):>3} exceptions")

    print("\n" + "─" * 72)
    print("  EXCEPTION DETAIL  (sorted by risk → variance)")
    print("─" * 72)

    for a in anomalies:
        risk_label = f"[{a['risk'].upper():^8}]"
        print(f"\n  {a['transaction_id']}  {risk_label}  {a['account_type']} | {a['transaction_type']}")
        print(f"  Amount: ${a['amount']:>12,.2f}   Expected: ${a['expected_amount']:>12,.2f}   Variance: ${a['variance']:>10,.2f}")
        print(f"  Z-Score: {a['zscore']:>5.2f}   Pct Variance: {a['pct_variance']:>5.2f}%")
        for flag in a["flags"]:
            print(f"  ⚑  {flag}")
        print(f"  ➤  {a['action']}")

    print("\n" + "─" * 72)
    print("  EXECUTIVE SUMMARY")
    print("─" * 72)
    if high:
        print(f"\n  Top Priority Items:")
        for a in high[:3]:
            print(f"  • {a['transaction_id']} — ${a['abs_variance']:,.2f} variance — {a['flags'][0]}")
    print(f"\n  Overall Assessment:")
    if len(high) >= 3:
        print("  ⚠  ELEVATED RISK — Multiple high-priority exceptions require immediate attention.")
    elif len(high) >= 1:
        print("  ⚠  MODERATE RISK — At least one high-priority item requires same-day resolution.")
    else:
        print("  ✓  NORMAL — No high-priority exceptions. Monitor medium items through EOD.")
    print("\n" + "═" * 72 + "\n")


def save_report_csv(anomalies, output_path="anomaly_report.csv"):
    """Save the full anomaly report to a CSV file."""
    fields = ["transaction_id", "date", "amount", "expected_amount", "variance",
              "abs_variance", "pct_variance", "zscore", "account_type",
              "transaction_type", "risk", "flags", "action"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in anomalies:
            row_out = dict(row)
            row_out["flags"] = " | ".join(row["flags"])
            writer.writerow(row_out)
    print(f"  Report saved to: {output_path}")


def save_report_json(anomalies, output_path="anomaly_report.json"):
    """Save the full anomaly report to a JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(anomalies, f, indent=2, default=str)
    print(f"  Report saved to: {output_path}")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    import sys
    filepath = sys.argv[1] if len(sys.argv) > 1 else "transactions.csv"

    print(f"\n  Loading transactions from: {filepath}")
    transactions = load_transactions(filepath)

    if not transactions:
        print("  No transactions found. Check your CSV file path and format.")
        return

    print(f"  {len(transactions)} transactions loaded. Running anomaly detection...")
    anomalies = detect_anomalies(transactions)

    print_report(anomalies)
    save_report_csv(anomalies)
    save_report_json(anomalies)


if __name__ == "__main__":
    main()
