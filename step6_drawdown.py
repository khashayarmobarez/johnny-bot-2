import pandas as pd
import os
from config import LISTS_FOLDER, DRAWDOWN_FILE


def compute_drawdown(df, threshold):
    """
    Compute lowest drawdown (most negative) for a list.
    Profit per trade = distance * reward_risk (if numeric)
      If reward_risk == "SL": profit = -distance
      If reward_risk is numeric negative (gap SL): profit = reward_risk * distance (negative)
    """
    profit_series = []
    for _, row in df.iterrows():
        rr = row["reward_risk"]
        distance = row["distance"]
        if rr == "SL":
            profit = -distance
        else:
            profit = float(rr) * distance
        profit_series.append(profit)

    # Cumulative profit
    cumulative = 0
    max_cumulative = 0
    lowest_drawdown = 0
    for profit in profit_series:
        cumulative += profit
        if cumulative > max_cumulative:
            max_cumulative = cumulative
        drawdown = cumulative - max_cumulative  # negative or zero
        if drawdown < lowest_drawdown:
            lowest_drawdown = drawdown

    return lowest_drawdown


def main():
    """
    Step 6 – Lowest Drawdown.
    For each threshold, distance, type, date‑order combination,
    compute the lowest drawdown (most negative) and write summary.
    """
    if not os.path.exists(LISTS_FOLDER):
        print(f"ERROR: {LISTS_FOLDER} not found. Run step4_lists.py first.")
        return

    summary_rows = []

    # Walk through step4_lists folder
    for threshold_dir in os.listdir(LISTS_FOLDER):
        list_subfolder = os.path.join(LISTS_FOLDER, threshold_dir)
        if not os.path.isdir(list_subfolder):
            continue

        threshold = int(threshold_dir)

        # Process each CSV file in the subfolder
        for filename in os.listdir(list_subfolder):
            if not filename.endswith(".csv"):
                continue

            # Extract original grouped file name and date order
            if filename.endswith("_asc.csv"):
                original_name = filename[:-8]
                date_order = "asc"
            elif filename.endswith("_desc.csv"):
                original_name = filename[:-9]
                date_order = "desc"
            else:
                continue

            # Parse distance and type from original_name
            parts = original_name.split("_")
            if len(parts) < 3:
                continue
            direction = parts[0]  # Buy/Sell
            distance_str = parts[2].replace(".csv", "")
            distance = int(distance_str)

            filepath = os.path.join(list_subfolder, filename)
            df = pd.read_csv(filepath)
            lowest_dd = compute_drawdown(df, threshold)

            summary_rows.append({
                "threshold": threshold,
                "distance": distance,
                "type": direction,
                "date_order": date_order,
                "lowest_drawdown": lowest_dd,
                "filename": filename,
                "n_trades": len(df),
            })

    # Write summary CSV
    df_summary = pd.DataFrame(summary_rows)
    df_summary.to_csv(DRAWDOWN_FILE, index=False)
    print(f"Step 6 complete. Summary saved to {DRAWDOWN_FILE}")
    print(f"Total combinations: {len(summary_rows)}")


if __name__ == "__main__":
    main()