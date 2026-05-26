# Transaction Anomaly Detector

A Python script that reads a CSV of financial transactions, applies statistical and rule-based anomaly detection, and outputs a formatted exception report — automatically.

Built from 8 years of hands-on financial operations experience at Goldman Sachs.

---

## What It Does

- Reads any CSV of transactions with amount, expected amount, and variance columns
- Flags anomalies using three methods simultaneously:
  - **Absolute variance threshold** — flags transactions above a dollar amount
  - **Percentage variance threshold** — flags transactions where variance exceeds a % of expected
  - **Z-score outlier detection** — flags statistical outliers relative to the full dataset
- Assigns a risk level to each transaction: **High / Medium / Low / Review**
- Generates a specific recommended action for each exception
- Outputs a clean console report, a CSV, and a JSON file

---

## The Problem It Solves

In financial operations, exception reports are typically generated manually — an analyst reviews each transaction, assesses the variance, and writes up a summary. For a 30-transaction daily run, that process takes 2–3 hours.

This script does it in under 2 seconds.

---

## How To Use It

**1. Install Python 3.8+** (no external libraries required — uses only the standard library)

**2. Prepare your CSV** with these columns:
```
Transaction ID, Date, Amount, Expected Amount, Variance, Account Type, Transaction Type, Flag Reason
```

**3. Run the script:**
```bash
python transaction_anomaly_detector.py transactions.csv
```

**4. Check your outputs:**
- Console: formatted exception report with risk levels and actions
- `anomaly_report.csv` — full report in spreadsheet format
- `anomaly_report.json` — full report in JSON format for downstream use

---

## Sample Output

```
════════════════════════════════════════════════════════════════════════
  DAILY TRANSACTION EXCEPTION REPORT
  Generated: 2025-05-01 14:30
  Total Transactions Analyzed: 30
  Total Absolute Variance: $479,990.50
════════════════════════════════════════════════════════════════════════

  RISK SUMMARY
  High            2 exceptions
  Medium          3 exceptions
  Low            25 exceptions

  TXN-021  [  HIGH  ]  BRK | Buy
  Amount: $312,450.00   Expected: $624,900.00   Variance: $312,450.00
  Z-Score: 4.80   Pct Variance: 50.00%
  ⚑  Large absolute variance: $312,450.00
  ⚑  Statistical outlier: z-score 4.80
  ➤  Escalate to senior operations immediately — resolve before market open.
```

---

## Configuration

Edit the `THRESHOLDS` dictionary at the top of the script to adjust detection sensitivity:

```python
THRESHOLDS = {
    "large_variance_abs":   10000,   # flag if absolute variance > $10,000
    "large_variance_pct":   0.05,    # flag if variance > 5% of expected
    "zscore_cutoff":        2.0,     # flag if z-score > 2.0
}
```

---

## Files

| File | Description |
|---|---|
| `transaction_anomaly_detector.py` | Main script |
| `transactions.csv` | Sample dataset with 30 realistic transactions |
| `anomaly_report.csv` | Sample output — CSV format |
| `anomaly_report.json` | Sample output — JSON format |

---

## Author

**Shawn Ghodrati**
Operations & AI Automation | Salt Lake City, UT
[LinkedIn](https://linkedin.com/in/shawngh)
