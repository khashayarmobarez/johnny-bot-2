# step1_extract.py
#
# Reads 1-minute forex candle data, resamples to 4H candles,
# simulates one trade per candle close, detects market gap SLs,
# and writes all results to trades.csv.
#
# Output columns:
#   date, time, day_of_week, type, entry, stop_loss,
#   distance, max_profit, reward_risk
#
# reward_risk values:
#   positive float  -> winning trade (ratio >= 1.0)
#   "SL"            -> normal stop loss hit
#   negative float  -> gap stop loss (e.g. -3.33)

import pandas as pd
import numpy as np

from config import (
    ENTRY_OFFSET,
    SL_OFFSET,
    MIN_RR,
    RAW_DATA_FILE,
    RAW_TRADES_FILE,
)


# ---------------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------------


def load_minute_data(filepath):
    df = pd.read_csv(
        filepath,
        sep=";",
        header=None,
        names=["datetime", "open", "high", "low", "close", "volume"],
        skiprows=1,
        low_memory=False,
    )
    df["datetime"] = pd.to_datetime(df["datetime"], format="%Y.%m.%d %H:%M")
    df = df.set_index("datetime").sort_index()

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["open", "high", "low", "close"])

    # Remove all data before 2011.01.03 04:00 (exact start date)
    df = df[df.index >= "2011-01-03 04:00"]

    return df


# ---------------------------------------------------------------
# 4H RESAMPLING
# ---------------------------------------------------------------

def resample_to_4h(minute_df):
    """
    Resamples 1-minute data into 4-hour OHLCV candles.
    Candle label is the START of the 4H period.
    Candle close time = label + 4 hours.
    Drops incomplete candles (e.g. partial periods at start/end of data).
    """
    ohlcv = minute_df.resample("4h", label="left", closed="left").agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
    )
    # Drop candles where we have no data
    ohlcv = ohlcv.dropna(subset=["open", "close"])
    return ohlcv



# ---------------------------------------------------------------
# TRADE SIMULATION
# ---------------------------------------------------------------

def simulate_trade(direction, entry, stop_loss, distance, minute_times, minute_high, minute_low, candle_close_dt):
    start_pos = int(np.searchsorted(minute_times, candle_close_dt.to_datetime64(), side="left"))

    if start_pos >= len(minute_times):
        return 0.0, "SL"

    if direction == "Buy":
        sub_high = minute_high[start_pos:]
        sub_low  = minute_low[start_pos:]
        normal_hits  = np.flatnonzero(sub_low <= stop_loss)
        favorable_arr = sub_high - entry
    else:
        sub_high = minute_high[start_pos:]
        sub_low  = minute_low[start_pos:]
        normal_hits  = np.flatnonzero(sub_high >= stop_loss)
        favorable_arr = entry - sub_low

    if normal_hits.size:
        exit_idx = int(normal_hits[0])
        max_favorable = float(np.max(favorable_arr[:exit_idx])) if exit_idx > 0 else 0.0
        if max_favorable < 0:
            max_favorable = 0.0
        rr = max_favorable / distance
        return round(max_favorable, 6), round(rr, 1) if rr >= MIN_RR else "SL"

    # End of data without SL hit
    max_favorable = float(np.max(favorable_arr)) if len(favorable_arr) else 0.0
    if max_favorable < 0:
        max_favorable = 0.0
    rr = max_favorable / distance if distance > 0 else 0.0
    return round(max_favorable, 6), round(rr, 1) if rr >= MIN_RR else "SL"


# ---------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------

def run():
    print("=" * 55)
    print("STEP 1 — BASE DATA EXTRACTION")
    print("=" * 55)

    # -- Load --
    print(f"\nLoading 1-minute data from '{RAW_DATA_FILE}'...")
    minute_df = load_minute_data(RAW_DATA_FILE)
    minute_times = minute_df.index.values
    minute_high = minute_df["high"].to_numpy()
    minute_low = minute_df["low"].to_numpy()
    print(f"  Loaded   : {len(minute_df):,} 1-minute candles")
    print(f"  From     : {minute_df.index[0]}")
    print(f"  To       : {minute_df.index[-1]}")

    # -- Resample --
    print("\nResampling to 4H candles...")
    candles_4h = resample_to_4h(minute_df)
    print(f"  4H candles : {len(candles_4h):,}")

    # -- Simulate --
    print("\nSimulating trades...")
    trades = []
    total  = len(candles_4h)

    for i, (candle_dt, candle) in enumerate(candles_4h.iterrows()):

        if i % 500 == 0:
            print(f"  [{i:>6} / {total}]  {candle_dt.date()}")

        open_price  = candle["open"]
        close_price = candle["close"]
        high_price  = candle["high"]
        low_price   = candle["low"]

        # Skip doji candles (no directional signal)
        if close_price == open_price:
            continue

        # -- Direction & prices --
        if close_price > open_price:
            direction = "Buy"
            entry     = close_price + ENTRY_OFFSET
            stop_loss = low_price   - SL_OFFSET
        else:
            direction = "Sell"
            entry     = close_price - ENTRY_OFFSET
            stop_loss = high_price  + SL_OFFSET

        distance = abs(entry - stop_loss)

        if distance == 0:
            continue

        # The 4H candle label is the period START.
        # The candle closes 4 hours later.
        candle_close_dt = candle_dt + pd.Timedelta(hours=4)

        # -- Run simulation --
        max_profit, reward_risk = simulate_trade(
            direction, entry, stop_loss, distance,
            minute_times, minute_high, minute_low, candle_close_dt,
        )

        trades.append({
            "date"        : candle_close_dt.strftime("%Y-%m-%d"),
            "time"        : candle_close_dt.strftime("%H:%M"),
            "day_of_week" : candle_close_dt.strftime("%A"),
            "type"        : direction,
            "entry"       : round(entry, 6),
            "stop_loss"   : round(stop_loss, 6),
            "distance"    : round(distance, 6),
            "max_profit"  : max_profit,
            "reward_risk" : reward_risk,
        })

    # -- Save --
    df = pd.DataFrame(trades)
    df.to_csv(RAW_TRADES_FILE, index=False)

    # -- Summary --
    total_trades = len(df)
    normal_sl    = (df["reward_risk"] == "SL").sum()
    wins = total_trades - normal_sl

    print(f"\n{'=' * 55}")
    print(f"STEP 1 COMPLETE")
    print(f"{'=' * 55}")
    print(f"  Total trades   : {total_trades:,}")
    print(f"  Normal SL      : {normal_sl:,}")
    print(f"  Output         : {RAW_TRADES_FILE}")
    print(f"  Wins (RR >= 1) : {wins:,}")

    # -- Available R/R thresholds for downstream steps --
    numeric_rr = pd.to_numeric(df["reward_risk"], errors="coerce")
    positive_rr = numeric_rr[numeric_rr >= MIN_RR]
    thresholds  = sorted(positive_rr.apply(np.floor).astype(int).unique().tolist())
    print(f"  R/R thresholds : {thresholds}")
    print()

    return df, thresholds


if __name__ == "__main__":
    run()