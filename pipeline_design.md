# Pipeline Design Document

## Overview

This document details the implementation of Steps 2‑6 of the forex trading strategy backtesting pipeline. The pipeline processes the `trades.csv` file produced by Step 1 (`step1_extract.py`) and produces grouped, filtered, and aggregated outputs for performance analysis.

## Step 2 – Group by Distance and Type

### Input

- `trades.csv` (output of Step 1) with columns:
  - `date`, `time`, `day_of_week`, `type`, `entry`, `stop_loss`, `distance`, `max_profit`, `reward_risk`

### Processing

1. Read `trades.csv` into a pandas DataFrame.
2. Compute integer distance bucket: `distance_bucket = math.floor(distance)`.
3. Split the DataFrame first by `type` (Buy / Sell), then by `distance_bucket`.
4. For each (type, distance_bucket) pair, write a separate CSV file.

### Output

- Folder: `step2_grouped/` (defined in `config.py` as `GROUPED_FOLDER`).
- File naming: `{type}_distance_{bucket}.csv` (e.g., `buy_distance_1.csv`, `sell_distance_3.csv`).
- Each file contains all trades of that type and distance bucket, preserving the original columns.

### Implementation Notes

- Use `math.floor` for consistency with specification.
- Ensure the output directory exists; create it if necessary.
- Handle empty groups (no trades for a given bucket) – skip writing a file for that bucket.

---

## Step 3 – Score and Filter

### Input

- All CSV files from `step2_grouped/`.
- Set of reward/risk thresholds `thresholds` (list of integers) computed in Step 1.

### Processing

For each threshold `T` in `thresholds`:

1. For each grouped CSV file:
   - Load the file.
   - Apply the scoring formula:
     ```
     score = 0
     for each trade:
         if reward_risk >= T:          score += T
         if reward_risk == "SL":       score -= 1
         if reward_risk is negative:   score += reward_risk
     score -= floor(total_trades / 10)
     ```
   - If `score > 0`, the file “survives” for threshold `T`.
2. Record which files survived for each threshold.

### Output

- Folder: `step3_filtered/` (defined as `FILTERED_FOLDER`).
- For each threshold `T`, a subfolder `T/` containing copies of the surviving CSV files, or a manifest file `surviving_files_T.csv` listing the surviving file paths.
- Alternatively, a single JSON or CSV mapping thresholds to surviving files.

### Implementation Notes

- The `reward_risk` column can contain:
  - Positive float (win, ratio ≥ 1)
  - String `"SL"` (normal stop loss)
  - Negative float (gap stop loss)
- Use exact equality for `"SL"` (string comparison).
- Negative floats are already numeric; add them directly to `score`.
- The penalty `floor(total_trades / 10)` uses integer division.

---

## Step 4 – Build Date‑Ordered Lists

### Input

- For each threshold `T`, the set of surviving files from Step 3.

### Processing

For each threshold `T`:

1. Load all surviving CSV files for that threshold.
2. Merge into a single DataFrame.
3. Sort by `date` ascending, then `time` ascending.
4. Write the sorted list to a CSV file.

### Output

- Folder: `step4_lists/` (defined as `LISTS_FOLDER`).
- Files: `list_rr_{T}.csv` (e.g., `list_rr_1.csv`, `list_rr_2.csv`).
- Columns identical to `trades.csv`.

### Implementation Notes

- Ensure the sort uses `date` and `time` together (or a combined datetime column).
- If no files survive for a threshold, produce an empty CSV (or skip).

---

## Step 5 – Re‑score the Lists (Informational)

### Input

- The date‑ordered lists from `step4_lists/`.

### Processing

For each threshold `T`:

1. Load `list_rr_{T}.csv`.
2. Apply the same scoring formula used in Step 3 (with the same threshold `T`).
3. Record `total_trades` and the computed `score`.

### Output

- Single CSV file: `step5_rescore_summary.csv` (defined as `RESCORE_FILE`).
- Columns: `rr_threshold`, `total_trades`, `score`.

### Implementation Notes

- This step is informational; no filtering occurs.
- The same scoring function should be reused to guarantee consistency.

---

## Step 6 – Lowest Drawdown

### Input

- The date‑ordered lists from `step4_lists/`.
- Set of reward levels `R` (integers from 1 up to the maximum reward/risk value present in the data).

### Processing

For each list file (threshold `T`) and for each reward level `R`:

1. Convert each trade to a numeric value:
   - If `reward_risk >= R`: value = +R
   - If `reward_risk == "SL"`: value = -1
   - If `reward_risk` is negative: value = reward_risk (negative float)
2. Compute the running cumulative sum of the value sequence.
3. Identify all positions where `reward_risk == "SL"` or `reward_risk` is negative (loss events).
4. For each such loss‑event index `i`:
   - Slice the cumulative sum from index `i` to the end.
   - Find the minimum value reached after `i`.
   - Record this minimum as the drawdown for that starting point.
5. The overall lowest drawdown for (list, reward level) is the smallest (most negative) value across all loss‑event starting points.

### Output

- Single CSV file: `step6_drawdown_summary.csv` (defined as `DRAWDOWN_FILE`).
- Columns: `rr_threshold`, `reward_level`, `lowest_drawdown`, `starting_index` (the index of the loss event that produced the lowest drawdown).

### Implementation Notes

- The drawdown window is from the loss event to the end of the list (not to the next peak).
- The result is a single number per (threshold, reward level) pair.
- Ensure efficient computation for large lists (potentially thousands of trades).

---

## Common Considerations

### Data Types

- `reward_risk`: mixed type (float, string). Use pandas `to_numeric` with `errors='coerce'` to separate numeric from non‑numeric.
- `distance`: float, convert to integer bucket with `math.floor`.

### Configuration

All folder and file names are defined in `config.py`. Use those constants to maintain consistency.

### Error Handling

- Missing input files should raise a clear error.
- Empty DataFrames should be handled gracefully (skip writing, or write empty file as appropriate).

### Testing

- Create a small synthetic `trades.csv` to verify each step.
- Compare outputs against manually calculated examples.

### Performance

- Use vectorized pandas operations where possible.
- Avoid iterating over rows in Python loops for large datasets.

## Implementation Order

1. Step 2 – Group by Distance and Type
2. Step 3 – Score and Filter
3. Step 4 – Build Date‑Ordered Lists
4. Step 5 – Re‑score the Lists
5. Step 6 – Lowest Drawdown

Each step will be implemented as a standalone Python script (e.g., `step2_grouped.py`, `step3_filtered.py`, …) that can be run independently after its prerequisites are satisfied.
