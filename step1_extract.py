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
from datetime import datetime, timedelta

from config import (
    ENTRY_OFFSET,
    SL_OFFSET,
    MIN_RR,
    DAILY_CLOSE_HOUR_EST,
    DAILY_CLOSE_HOUR_EDT,
    RAW_DATA_FILE,
    RAW_TRADES_FILE,
)


# ---------------------------------------------------------------
# DST HELPERS
# ---------------------------------------------------------------

def _nth_weekday_of_month(year, month, weekday, n):
    """
    Returns the nth occurrence (1-indexed) of a weekday in a given month/year.
    weekday: 0=Monday ... 6=Sunday
    """
    first_of_month = datetime(year, month, 1)
    days_until = (weekday - first_of_month.weekday()) % 7
    first_occurrence = first_of_month + timedelta(days=days_until)
    return first_occurrence + timedelta(weeks=(n - 1))


def is_edt(dt):
    """
    Returns True if the given UTC datetime falls within US Eastern Daylight Time.
    EDT runs from the second Sunday of March to the first Sunday of November.
    Clocks change at 02:00 local time = 07:00 UTC.
    """
    year = dt.year
    edt_start = _nth_weekday_of_month(year, 3, 6, 2).replace(hour=7)   # second Sunday March
    edt_end   = _nth_weekday_of_month(year, 11, 6, 1).replace(hour=6)  # first Sunday November
    return edt_start <= dt < edt_end


def get_daily_close_hour(dt):
    """Returns the UTC hour at which the forex daily close occurs on this date."""
    return DAILY_CLOSE_HOUR_EDT if is_edt(dt) else DAILY_CLOSE_HOUR_EST


# ---------------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------------

def load_minute_data(filepath):
    """
    Loads 1-minute OHLCV CSV with no headers.
    Expected column order: date, time, open, high, low, close, volume
    """
    df = pd.read_csv(
        filepath,
        header=None,
        names=["date", "time", "open", "high", "low", "close", "volume"],
    )
    df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"])
    df = df.drop(columns=["date", "time"])
    df = df.set_index("datetime").sort_index()

    # Ensure numeric types
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["open", "high", "low", "close"])
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
# GAP DETECTION
# ---------------------------------------------------------------

def is_market_gap(prev_dt, curr_dt):
    """
    Returns True if the time jump between two consecutive 1-minute
    candle timestamps is larger than 1 minute, indicating the market
    was closed (daily or weekly gap).
    Uses 90 seconds as threshold to avoid floating point edge cases.
    """
    diff_seconds = (curr_dt - prev_dt).total_seconds()
    return diff_seconds > 90


# ---------------------------------------------------------------
# TRADE SIMULATION
# ---------------------------------------------------------------

def simulate_trade(direction, entry, stop_loss, distance, minute_df, candle_close_dt):
    """
    Simulates a trade forward through 1-minute candles starting from
    the 4H candle's close time. Detects gap SLs from market close windows.

    Parameters:
        direction       : "Buy" or "Sell"
        entry           : float, exact entry price
        stop_loss       : float, stop loss price
        distance        : float, abs(entry - stop_loss)
        minute_df       : full 1-minute DataFrame indexed by datetime
        candle_close_dt : datetime, the moment the 4H candle closed

    Returns:
        max_profit   (float) : largest favorable price move before SL hit
        reward_risk  (float or str) :
            positive float  -> ratio >= MIN_RR
            "SL"            -> normal stop loss
            negative float  -> gap stop loss
    """
    # All candles strictly after the 4H candle closed
    future = minute_df[minute_df.index >= candle_close_dt]

    if future.empty:
        return 0.0, "SL"

    max_favorable = 0.0
    # prev_dt starts at the 4H close so the first candle gap is measured correctly
    prev_dt = candle_close_dt

    for curr_dt, row in future.iterrows():

        # ---- Gap check ------------------------------------------------
        # If there is a timestamp jump, price may have gapped past SL.
        # post_gap_price = open of first candle after the gap.
        if is_market_gap(prev_dt, curr_dt):
            post_gap_price = row["open"]

            if direction == "Buy" and post_gap_price < stop_loss:
                gap_value = -((entry - post_gap_price) / distance)
                return round(max_favorable, 6), round(gap_value, 4)

            if direction == "Sell" and post_gap_price > stop_loss:
                gap_value = -((post_gap_price - entry) / distance)
                return round(max_favorable, 6), round(gap_value, 4)

            # Gap did not trigger SL — trade continues from post-gap candle.
            # Fall through to normal SL check below for this same candle.

        # ---- Normal SL check ------------------------------------------
        if direction == "Buy":
            if row["low"] <= stop_loss:
                rr = max_favorable / distance
                rr_value = round(rr, 1) if rr >= MIN_RR else "SL"
                return round(max_favorable, 6), rr_value
            # Track highest favorable point (max high above entry)
            favorable = row["high"] - entry
            if favorable > max_favorable:
                max_favorable = favorable

        elif direction == "Sell":
            if row["high"] >= stop_loss:
                rr = max_favorable / distance
                rr_value = round(rr, 1) if rr >= MIN_RR else "SL"
                return round(max_favorable, 6), rr_value
            # Track lowest favorable point (max drop below entry)
            favorable = entry - row["low"]
            if favorable > max_favorable:
                max_favorable = favorable

        prev_dt = curr_dt

    # End of data reached without SL being hit.
    # Record whatever max_profit was accumulated.
    rr = max_favorable / distance if distance > 0 else 0.0
    rr_value = round(rr, 1) if rr >= MIN_RR else "SL"
    return round(max_favorable, 6), rr_value


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
            minute_df, candle_close_dt,
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
    gap_sl       = df["reward_risk"].apply(
        lambda x: isinstance(x, float) and x < 0
    ).sum()
    wins         = total_trades - normal_sl - gap_sl

    print(f"\n{'=' * 55}")
    print(f"STEP 1 COMPLETE")
    print(f"{'=' * 55}")
    print(f"  Total trades   : {total_trades:,}")
    print(f"  Wins (RR >= 1) : {wins:,}")
    print(f"  Normal SL      : {normal_sl:,}")
    print(f"  Gap SL         : {gap_sl:,}")
    print(f"  Output         : {RAW_TRADES_FILE}")

    # -- Available R/R thresholds for downstream steps --
    numeric_rr = pd.to_numeric(df["reward_risk"], errors="coerce")
    positive_rr = numeric_rr[numeric_rr >= MIN_RR]
    thresholds  = sorted(positive_rr.apply(np.floor).astype(int).unique().tolist())
    print(f"  R/R thresholds : {thresholds}")
    print()

    return df, thresholds


if __name__ == "__main__":
    run()