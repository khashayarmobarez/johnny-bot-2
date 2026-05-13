# Janyar Trade Strategy Pipeline

A multi-step pipeline for backtesting a trading strategy on 1-minute XAU/USD candle data.

---

## Pipeline Overview

### Step 1 — Base Data Extraction (`step1_extract.py`)

- Loads raw 1-minute candle data from `XAU_1m_data.csv`
- Filters out all data before 2012
- Resamples to 4-hour candles
- Simulates one trade per candle close based on candle direction (bullish → Buy, bearish → Sell)
- Outputs `trades.csv`

### Step 2 — Group by Distance and Type (`step2_grouped.py`)

- Reads `trades.csv`
- Splits trades by direction (Buy / Sell) and integer distance bucket (`math.floor(distance)`)
- Writes one CSV file per combination
- Output folder: `step2_grouped/`
- File naming: `buy_distance_1.csv`, `sell_distance_3.csv`, etc.

### Step 3 — Score and Filter (`step3_filtered.py`)

- For each reward/risk threshold `T` (every integer from 1 to the max R/R in the data):
  - Scores every grouped file independently using the formula below
  - Keeps files where `score > 0`, drops files where `score <= 0`
  - Each threshold is evaluated independently — a file dropped at `T=1` is re-evaluated fresh at `T=2`
- Output folder: `step3_filtered/{T}/` for each threshold

**Scoring formula:**

```
score = 0
for each trade:
    if reward_risk >= T:      score += T
    if 0 < reward_risk < T:   score -= 1
    if reward_risk == "SL":   score -= 1
score -= floor(total_trades / 10)
```

### Step 4 — Build Date-Ordered Lists (`step4_lists.py`)

- For each threshold `T`:
  - Loads all surviving files from `step3_filtered/{T}/`
  - Merges them into a single DataFrame
  - Sorts by date and time ascending
  - Writes one merged list per threshold
- Output folder: `step4_lists/`
- File naming: `list_rr_1.csv`, `list_rr_2.csv`, etc.

### Step 5 — Re-score the Lists (`step5_rescore.py`)

- Applies the same scoring formula from Step 3 to each merged list from Step 4
- Uses the matching threshold `T` for each list
- No filtering — informational output only
- Output file: `step5_rescore_summary.csv`
- Columns: `rr_threshold`, `total_trades`, `score`

### Step 6 — Lowest Drawdown (`step6_drawdown.py`)

- For each merged list from Step 4, computes the lowest drawdown using the matching threshold as the reward level:
  - Converts each trade to a score value:
    - `reward_risk >= T` → `+T`
    - `reward_risk == "SL"` → `-1`
    - `0 < reward_risk < T` → `-1`
  - Finds all loss-event positions (SL trades)
  - For each loss-event position as a starting index, slices to the end of the list, computes the running cumulative sum, and records the minimum reached
  - The result for threshold `T` is the single lowest value across all starting points
- Results are sorted by `rr_threshold` ascending
- Output file: `step6_drawdown_summary.csv`
- Columns: `rr_threshold`, `lowest_drawdown`, `starting_index`, `total_trades`

---

## Configuration

All constants are centralized in `config.py`. Do not hardcode values in individual step files.

| Constant               | Description                                                |
| ---------------------- | ---------------------------------------------------------- |
| `ENTRY_OFFSET`         | Price offset for trade entry (USD)                         |
| `SL_OFFSET`            | Price offset for stop loss (USD)                           |
| `MIN_RR`               | Minimum R/R ratio to record as a win (below this → `"SL"`) |
| `PENALTY_PER_N_TRADES` | Deduct 1 from score per this many trades                   |
| `RAW_DATA_FILE`        | Input data filename                                        |
| `RAW_TRADES_FILE`      | Step 1 output filename                                     |
| `GROUPED_FOLDER`       | Step 2 output folder                                       |
| `FILTERED_FOLDER`      | Step 3 output folder                                       |
| `LISTS_FOLDER`         | Step 4 output folder                                       |
| `RESCORE_FILE`         | Step 5 output filename                                     |
| `DRAWDOWN_FILE`        | Step 6 output filename                                     |

---

## Quick Start

**1. Install dependencies**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate

pip install -r requirements.txt
```

**2. Place your data file**

Put your 1-minute candle CSV in the project root named `XAU_1m_data.csv`.
Expected format (semicolon-separated, one header row):

```
Date;Open;High;Low;Close;Volume
2012.01.02 00:01;1600.5;1601.0;1600.3;1600.8;12
```

**3. Run each step in order**

```bash
python step1_extract.py
python step2_grouped.py
python step3_filtered.py
python step4_lists.py
python step5_rescore.py
python step6_drawdown.py
```

---

## Testing with a Small Dataset

Step 1 iterates over every 4H candle and simulates each trade forward through 1-minute data. On a large dataset this is slow. To verify the pipeline quickly, create a sample first:

**Windows:**

```powershell
powershell -command "(Get-Content XAU_1m_data.csv -TotalCount 10001) | Set-Content sample_data.csv"
```

The count is 10001 to preserve the header row plus 10000 data rows.

**Mac / Linux:**

```bash
head -n 10001 XAU_1m_data.csv > sample_data.csv
```

Then temporarily set `RAW_DATA_FILE = "sample_data.csv"` in `config.py`, run the pipeline, and revert when done.

---

## File Structure

```
.
├── XAU_1m_data.csv                # Raw 1-minute candle data (input)
├── trades.csv                     # Extracted trades (Step 1 output)
├── config.py                      # Shared constants
├── requirements.txt               # Python dependencies
├── step1_extract.py               # Step 1 — Base extraction
├── step2_grouped.py               # Step 2 — Group by distance and type
├── step3_filtered.py              # Step 3 — Score and filter
├── step4_lists.py                 # Step 4 — Date-ordered lists
├── step5_rescore.py               # Step 5 — Re-score lists
├── step6_drawdown.py              # Step 6 — Lowest drawdown
├── step2_grouped/                 # Step 2 output folder
│   ├── buy_distance_1.csv
│   ├── sell_distance_1.csv
│   └── ...
├── step3_filtered/                # Step 3 output folder
│   ├── 1/                         # Threshold T=1
│   │   ├── buy_distance_1.csv
│   │   └── ...
│   ├── 2/                         # Threshold T=2
│   └── ...
├── step4_lists/                   # Step 4 output folder
│   ├── list_rr_1.csv
│   ├── list_rr_2.csv
│   └── ...
├── step5_rescore_summary.csv      # Step 5 output
└── step6_drawdown_summary.csv     # Step 6 output
```

---

## Dependencies

- Python 3.7+
- pandas >= 2.0.0
- numpy >= 1.24.0

---

## Notes

- Step 1 is the slowest step due to per-trade simulation over 1-minute data. Use the sample dataset approach above for testing.
- The scoring penalty `floor(n_trades / 10)` discourages over-fitting to buckets with very large trade counts.
- All data before 2012 is excluded at load time in Step 1.
- All folder and file names are defined in `config.py`. Change them there, not in individual scripts.

---

\_Proprietary — For internal use only.
