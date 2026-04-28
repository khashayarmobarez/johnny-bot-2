# Janyar Trade Strategy Pipeline

This project implements a multi‑step pipeline for analyzing forex trading strategies based on 1‑minute EUR/USD data.

## Pipeline Overview

The pipeline consists of six sequential steps:

1. **Base Data Extraction (`step1_extract.py`)**
   - Loads raw 1‑minute data (`data.csv`)
   - Resamples to 4‑hour candles
   - Simulates trades with entry/SL offsets
   - Outputs `trades.csv` with reward/risk ratios

2. **Group by Distance and Type (`step2_grouped.py`)**
   - Splits trades into CSV files per distance and direction (Buy/Sell)
   - Creates `step2_grouped/` folder

3. **Score and Filter (`step3_filtered.py`)**
   - For each reward/risk threshold (positive integer values)
   - Computes a score for each grouped file
   - Keeps only files with score > 0
   - Creates `step3_filtered/` folder with surviving files per threshold

4. **Build Date‑Ordered Lists (`step4_lists.py`)**
   - For each surviving file, creates two date‑ordered lists:
     - Ascending (earliest trades first)
     - Descending (latest trades first)
   - Stores lists in `step4_lists/` folder

5. **Re‑score the Lists (`step5_rescore.py`)**
   - Re‑computes scores for each date‑ordered list
   - Produces `step5_rescore_summary.csv` with threshold, distance, type, date‑order, and score

6. **Lowest Drawdown (`step6_drawdown.py`)**
   - Computes the lowest drawdown (most negative cumulative profit) for each list
   - Produces `step6_drawdown_summary.csv` with threshold, distance, type, date‑order, and drawdown

## Configuration

Constants are centralized in `config.py`:

- `ENTRY_OFFSET`, `SL_OFFSET`: entry and stop‑loss offsets (in pips)
- `MIN_RR`: minimum reward‑risk ratio for a “win”
- Daily/weekly close parameters
- Folder names and output file paths

## Quick‑Start

1. **Prepare data**: Ensure `data.csv` (1‑minute EUR/USD candles) is present.

2. **Run Step 1** (if not already done):

   ```bash
   python step1_extract.py
   ```

   _Note:_ This step may take a long time due to the large dataset. For quick testing, you can use a smaller sample (see below).

3. **Run Steps 2‑6** sequentially:
   ```bash
   python step2_grouped.py
   python step3_filtered.py
   python step4_lists.py
   python step5_rescore.py
   python step6_drawdown.py
   ```

Each step prints progress and writes outputs to the designated folders.

## Testing with a Small Dataset

To verify the pipeline quickly, you can run Step 1 on a reduced dataset:

```bash
# Create a sample of 10,000 rows from data.csv
powershell -command "(Get-Content data.csv -TotalCount 10000) | Set-Content sample_data.csv"

# Temporarily set RAW_DATA_FILE to sample_data.csv in config.py
# Then run step1_extract.py
python step1_extract.py
```

After Step 1 completes, revert `config.py` to `data.csv` and proceed with Steps 2‑6.

## Results

The final summaries (`step5_rescore_summary.csv` and `step6_drawdown_summary.csv`) provide a comprehensive view of which distance‑type‑order combinations perform best under each reward‑risk threshold.

## Dependencies

- Python 3.7+
- pandas
- numpy

## File Structure

```
.
├── data.csv                    # Raw 1‑minute EUR/USD data (≈351 MB)
├── trades.csv                  # Extracted trades (Step 1 output)
├── config.py                   # Shared constants
├── step1_extract.py            # Step 1 – Base extraction
├── step2_grouped.py            # Step 2 – Group by distance/type
├── step3_filtered.py           # Step 3 – Score and filter
├── step4_lists.py              # Step 4 – Date‑ordered lists
├── step5_rescore.py            # Step 5 – Re‑score lists
├── step6_drawdown.py           # Step 6 – Lowest drawdown
├── pipeline_design.md          # Original pipeline specification
├── README.md                   # This file
├── step2_grouped/              # Step 2 output folder
├── step3_filtered/             # Step 3 output folder
├── step4_lists/                # Step 4 output folder
└── step5_rescore_summary.csv   # Step 5 summary
└── step6_drawdown_summary.csv  # Step 6 summary
```

## Notes

- Step 1 uses a loop‑based simulation that can be slow for large datasets. Consider vectorization or parallelization for production‑scale runs.
- The scoring formula includes a penalty of `floor(n_trades / 10)` to discourage over‑fitting.
- Gap‑SL trades are recorded as negative reward‑risk ratios.

## License

Proprietary – For internal use only.
