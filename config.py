# All shared constants. Change values here only.

ENTRY_OFFSET    = 0.3
SL_OFFSET       = 0.3
MIN_RR          = 1.0

# Forex daily close (UTC)
DAILY_CLOSE_DURATION_MIN    = 60
POST_OPEN_LOCKOUT_MIN       = 15
DAILY_ILLIQUID_MIN          = 75   # 60 + 15

WEEKLY_CLOSE_WEEKDAY        = 4    # Friday
WEEKLY_REOPEN_WEEKDAY       = 6    # Sunday

PENALTY_PER_N_TRADES        = 10

RAW_DATA_FILE       = "XAU_1m_data.csv"
RAW_TRADES_FILE     = "trades.csv"
GROUPED_FOLDER      = "step2_grouped"
FILTERED_FOLDER     = "step3_filtered"
LISTS_FOLDER        = "step4_lists"
RESCORE_FILE        = "step5_rescore_summary.csv"
DRAWDOWN_FILE       = "step6_drawdown_summary.csv"