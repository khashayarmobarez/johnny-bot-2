# Forex Trading Strategy Backtesting Pipeline

## Project Overview

This project implements a systematic pipeline for backtesting forex trading strategies using 1-minute candle data. The pipeline processes raw market data, simulates trades based on 4-hour candle signals, and evaluates performance metrics including gap stop-loss detection and reward/risk analysis.

The pipeline consists of six sequential steps:

1. **Base Data Extraction** - Resamples 1-minute data to 4-hour candles and simulates trades
2. **Grouping** - Groups trades by reward/risk thresholds
3. **Filtering** - Applies filtering criteria to select optimal trade sets
4. **Lists Generation** - Creates trade lists for further analysis
5. **Rescoring** - Recalculates performance metrics
6. **Drawdown Analysis** - Evaluates portfolio drawdown characteristics

## Project Structure

```
├── .gitignore               # Python and project-specific ignores
├── config.py                # Configuration constants and file paths
├── requirements.txt         # Python dependencies
├── step1_extract.py         # Step 1: Data extraction and trade simulation
├── README.md                # This file
├── data.csv                 # Raw 1-minute forex data (not in repo)
├── trades.csv               # Output of step 1 (generated)
├── step2_grouped/           # Output folder for step 2 (generated)
├── step3_filtered/          # Output folder for step 3 (generated)
├── step4_lists/             # Output folder for step 4 (generated)
├── step5_rescore_summary.csv # Output of step 5 (generated)
└── step6_drawdown_summary.csv # Output of step 6 (generated)
```

## Installation and Requirements

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd project
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

### Dependencies

- pandas>=2.0.0
- numpy>=1.24.0

## Usage

### Step 1: Base Data Extraction

Run the initial extraction and trade simulation:

```bash
python step1_extract.py
```

This will:

- Load 1-minute OHLCV data from `data.csv`
- Resample to 4-hour candles
- Simulate trades (Buy/Sell) at each candle close
- Detect normal and gap stop-losses
- Output results to `trades.csv`

### Output Format (trades.csv)

| Column      | Description                                                                                        |
| ----------- | -------------------------------------------------------------------------------------------------- |
| date        | Trade date (YYYY-MM-DD)                                                                            |
| time        | Trade time (HH:MM)                                                                                 |
| day_of_week | Day of week                                                                                        |
| type        | "Buy" or "Sell"                                                                                    |
| entry       | Entry price                                                                                        |
| stop_loss   | Stop loss price                                                                                    |
| distance    | Absolute difference between entry and stop loss                                                    |
| max_profit  | Maximum favorable price movement before SL hit                                                     |
| reward_risk | Trade outcome: positive float (win ≥ 1.0), "SL" (normal stop loss), negative float (gap stop loss) |

### Subsequent Steps

Steps 2-6 are not yet implemented but are planned as part of the pipeline:

- **Step 2**: Group trades by reward/risk thresholds
- **Step 3**: Filter trades based on performance criteria
- **Step 4**: Generate trade lists for portfolio construction
- **Step 5**: Rescore selected trades
- **Step 6**: Analyze portfolio drawdown

## Configuration

Edit `config.py` to adjust trading parameters:

| Parameter                | Description                                 | Default                      |
| ------------------------ | ------------------------------------------- | ---------------------------- |
| ENTRY_OFFSET             | Offset from candle close for entry price    | 0.3                          |
| SL_OFFSET                | Offset from candle high/low for stop loss   | 0.3                          |
| MIN_RR                   | Minimum reward/risk ratio to count as a win | 1.0                          |
| DAILY_CLOSE_HOUR_EST     | Daily close hour (UTC) during EST period    | 22                           |
| DAILY_CLOSE_HOUR_EDT     | Daily close hour (UTC) during EDT period    | 21                           |
| DAILY_CLOSE_DURATION_MIN | Duration of daily close window (minutes)    | 60                           |
| POST_OPEN_LOCKOUT_MIN    | Lockout period after market open (minutes)  | 15                           |
| DAILY_ILLIQUID_MIN       | Total illiquid period (minutes)             | 75                           |
| WEEKLY_CLOSE_WEEKDAY     | Weekly close weekday (0=Monday, 4=Friday)   | 4                            |
| WEEKLY_REOPEN_WEEKDAY    | Weekly reopen weekday (0=Monday, 6=Sunday)  | 6                            |
| PENALTY_PER_N_TRADES     | Penalty factor for trade frequency          | 10                           |
| RAW_DATA_FILE            | Input 1-minute data file                    | "data.csv"                   |
| RAW_TRADES_FILE          | Output trades file                          | "trades.csv"                 |
| GROUPED_FOLDER           | Folder for step 2 output                    | "step2_grouped"              |
| FILTERED_FOLDER          | Folder for step 3 output                    | "step3_filtered"             |
| LISTS_FOLDER             | Folder for step 4 output                    | "step4_lists"                |
| RESCORE_FILE             | Step 5 output file                          | "step5_rescore_summary.csv"  |
| DRAWDOWN_FILE            | Step 6 output file                          | "step6_drawdown_summary.csv" |

## Input Data Format

Place your 1-minute forex data in `data.csv` with the following format (no headers):

```
date,time,open,high,low,close,volume
2025-01-01,00:00,1.23456,1.23478,1.23412,1.23445,1000
2025-01-01,00:01,1.23446,1.23489,1.23411,1.23467,1200
...
```

Columns:

1. Date (YYYY-MM-DD)
2. Time (HH:MM)
3. Open price
4. High price
5. Low price
6. Close price
7. Volume

## License

This project is for educational and research purposes.
