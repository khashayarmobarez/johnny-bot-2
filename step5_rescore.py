import pandas as pd
import math
import os
from config import LISTS_FOLDER, RESCORE_FILE


def compute_score(df, threshold):
    """
    Compute score for a DataFrame using the formula:
    score = sum(T for reward_risk >= T)
          - sum(1 for reward_risk == "SL")
          + sum(reward_risk for negative reward_risk)
          - floor(total_trades / 10)
    """
    total_trades = len(df)

    numeric_rr = pd.to_numeric(df["reward_risk"], errors="coerce")
    wins = numeric_rr >= threshold
    win_score = wins.sum() * threshold

    sl_trades = df["reward_risk"] == "SL"
    sl_score = -sl_trades.sum()

    negative_rr = numeric_rr[numeric_rr < 0]
    negative_score = negative_rr.sum()

    penalty = math.floor(total_trades / 10)

    score = win_score + sl_score + negative_score - penalty
    return score


def main():
    """
    Step 5 – Re‑score the Lists.
    For each threshold, distance, type, date‑order combination,
    compute the score and write a summary CSV.
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
            # Format: {original_name}_asc.csv or {original_name}_desc.csv
            if filename.endswith("_asc.csv"):
                original_name = filename[:-8]
                date_order = "asc"
            elif filename.endswith("_desc.csv"):
                original_name = filename[:-9]
                date_order = "desc"
            else:
                continue

            # Parse distance and type from original_name
            # Example: Buy_distance_1.csv
            parts = original_name.split("_")
            if len(parts) < 3:
                continue
            direction = parts[0]  # Buy/Sell
            distance_str = parts[2].replace(".csv", "")
            distance = int(distance_str)  # distance number

            filepath = os.path.join(list_subfolder, filename)
            df = pd.read_csv(filepath)
            score = compute_score(df, threshold)

            summary_rows.append({
                "threshold": threshold,
                "distance": distance,
                "type": direction,
                "date_order": date_order,
                "score": score,
                "filename": filename,
                "n_trades": len(df),
            })

    # Write summary CSV
    df_summary = pd.DataFrame(summary_rows)
    df_summary.to_csv(RESCORE_FILE, index=False)
    print(f"Step 5 complete. Summary saved to {RESCORE_FILE}")
    print(f"Total combinations: {len(summary_rows)}")


if __name__ == "__main__":
    main()