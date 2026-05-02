# step6_drawdown.py
# Computes the lowest drawdown for each list from step4,
# across every reward level R from 1 to max available.
# Output: step6_drawdown_summary.csv

import pandas as pd
import numpy as np
import os
from config import LISTS_FOLDER, DRAWDOWN_FILE, MIN_RR


def get_trade_values(df, reward_level):
    """
    Converts each trade's reward_risk into a numeric score value
    for the given reward level R:
        >= R          → +R
        == "SL"       → -1
        negative float → the negative value itself (e.g. -3.33)
        positive < R  → -1
    """
    numeric_rr = pd.to_numeric(df["reward_risk"], errors="coerce")
    values = np.where(
        df["reward_risk"] == "SL", -1.0,
        np.where(
            numeric_rr < 0, numeric_rr,
            np.where(
                numeric_rr >= reward_level, float(reward_level),
                -1.0
            )
        )
    )
    return values.astype(float)


def get_loss_event_indices(df):
    """
    Returns indices of all trades that are a loss event:
    either "SL" or a negative float (gap SL).
    """
    numeric_rr = pd.to_numeric(df["reward_risk"], errors="coerce")
    is_sl  = df["reward_risk"] == "SL"
    is_gap = numeric_rr < 0
    return np.flatnonzero((is_sl | is_gap).to_numpy())


def compute_lowest_drawdown(values, loss_indices):
    """
    For each loss event position as a starting index,
    slices values from that index to end, computes cumulative sum,
    records the minimum reached. Returns the single lowest value
    across all starting points and the index that produced it.
    """
    if len(loss_indices) == 0:
        return 0.0, None

    lowest = float("inf")
    best_start = None

    for start_idx in loss_indices:
        segment = values[start_idx:]
        cumsum = np.cumsum(segment)
        min_val = float(np.min(cumsum))
        if min_val < lowest:
            lowest = min_val
            best_start = int(start_idx)

    return lowest, best_start


def main():
    if not os.path.exists(LISTS_FOLDER):
        print(f"ERROR: {LISTS_FOLDER} not found. Run step4_lists.py first.")
        return

    summary_rows = []

    for filename in sorted(os.listdir(LISTS_FOLDER)):
        if not filename.startswith("list_rr_") or not filename.endswith(".csv"):
            continue

        T = int(filename.replace("list_rr_", "").replace(".csv", ""))
        filepath = os.path.join(LISTS_FOLDER, filename)
        df = pd.read_csv(filepath).reset_index(drop=True)

        if df.empty:
            continue

        # Reward levels: 1 up to the max integer RR in this list
        numeric_rr = pd.to_numeric(df["reward_risk"], errors="coerce")
        positive_rr = numeric_rr[numeric_rr >= MIN_RR]

        if positive_rr.empty:
            continue

        max_reward = int(np.floor(positive_rr.max()))
        reward_levels = range(1, max_reward + 1)
        loss_indices = get_loss_event_indices(df)

        for R in reward_levels:
            values = get_trade_values(df, R)
            lowest_dd, best_start = compute_lowest_drawdown(values, loss_indices)

            summary_rows.append({
                "rr_threshold"    : T,
                "reward_level"    : R,
                "lowest_drawdown" : round(lowest_dd, 4),
                "starting_index"  : best_start,
                "total_trades"    : len(df),
            })

        print(f"Threshold {T}: reward levels 1–{max_reward} computed.")

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(DRAWDOWN_FILE, index=False)
    print(f"\nStep 6 complete. Summary saved to {DRAWDOWN_FILE}.")


if __name__ == "__main__":
    main()