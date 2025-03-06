# 💰 Trading Configuration
USDC_ADDRESS = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # Never trade or close
SOL_ADDRESS = "So11111111111111111111111111111111111111111"  # Never trade or close

# Create a list of addresses to exclude from trading/closing
EXCLUDED_TOKENS = [USDC_ADDRESS, SOL_ADDRESS]

# # # Token List for Trading 📋
# MONITORED_TOKENS = [
#     "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump",  # 🌬️ FART
#     # 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',    # 💵 USDC
#     "HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC",  # 🤖 AI16Z
#     # 'v62Jv9pwMTREWV9f6TetZfMafV254vo99p7HSF25BPr',     # 🎮 GG Solana
#     # 'KENJSUYLASHUMfHyy5o4Hp2FdNqZg1AsUPhfH2kYvEP',   # GRIFFAIN
#     # '8x5VqbHA8D7NkD52uNuS5nnt3PwA3pLD34ymskeSo2Wn',    # 🧠 ZEREBRO
#     # 'Df6yfrKC8kZE3KNkrHERKzAetSxbrWeniQfyJY4Jpump',    # 😎 CHILL GUY
#     # 'ED5nyyWEzpPPiWimP8vYm7sD7TD3LAt3Q3gRTWHzPJBY',    # MOODENG
#     # 'EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm',    # 🐕 WIF
# ]

MONITORED_TOKENS = []



# Position sizing 🎯
usd_size = 1.5  # 25  # Size of position to hold
max_usd_order_size = 3  # Max order size
tx_sleep = 30  # Sleep between transactions
slippage = 199  # Slippage settings

# Risk Management Settings 🛡️
CASH_PERCENTAGE = 20  # Minimum % to keep in USDC as safety buffer (0-100)
MAX_POSITION_PERCENTAGE = 1  # 30  # Maximum % allocation per position (0-100)
STOPLOSS_PRICE = 0.1  # 1 # NOT USED YET 1/5/25
BREAKOUT_PRICE = 0.0001  # NOT USED YET 1/5/25
SLEEP_AFTER_CLOSE = 600  # Prevent overtrading

# MAX_LOSS_GAIN_CHECK_HOURS = (
#     12  # How far back to check for max loss/gain limits (in hours)
# )

SLEEP_BETWEEN_RUNS_MINUTES = 15  # How long to sleep between agent runs 🕒


# Max Loss/Gain Settings FOR RISK AGENT 1/5/25
USE_PERCENTAGE = (
    False  # If True, use percentage-based limits. If False, use USD-based limits
)

# USD-based limits (used if USE_PERCENTAGE is False)
MAX_LOSS_USD = 25  # Maximum loss in USD before stopping trading
MAX_GAIN_USD = 25  # Maximum gain in USD before stopping trading

# USD MINIMUM BALANCE RISK CONTROL
MINIMUM_BALANCE_USD = (
    50  # If balance falls below this, risk agent will consider closing all positions
)
USE_AI_CONFIRMATION = True  # If True, consult AI before closing positions. If False, close immediately on breach

# Percentage-based limits (used if USE_PERCENTAGE is True)
MAX_LOSS_PERCENT = 5  # Maximum loss as percentage (e.g., 20 = 20% loss)
MAX_GAIN_PERCENT = 5  # Maximum gain as percentage (e.g., 50 = 50% gain)

# Transaction settings ⚡
slippage = 199  # 500 = 5% and 50 = .5% slippage
PRIORITY_FEE = 100000  # ~0.02 USD at current SOL prices
orders_per_open = 3  # Multiple orders for better fill rates

# Market maker settings 📊
buy_under = 0.0946
sell_over = 1

# Data collection settings 📈
DAYSBACK_4_DATA = 3
DATA_TIMEFRAME = "1H"  # 1m, 3m, 5m, 15m, 30m, 1H, 2H, 4H, 6H, 8H, 12H, 1D, 3D, 1W, 1M
SAVE_OHLCV_DATA = False  # Set to True to save data permanently, False will only use temp data during run

# AI Model Settings 🤖
AI_MODEL = "claude-3-haiku-20240307"  # Model Options:
# - claude-3-haiku-20240307 (Fast, efficient Claude model)
# - claude-3-sonnet-20240229 (Balanced Claude model)
# - claude-3-opus-20240229 (Most powerful Claude model)
AI_MAX_TOKENS = 1024  # Max tokens for response
AI_TEMPERATURE = 0.7  # Creativity vs precision (0-1)

# Trading Strategy Agent Settings - MAY NOT BE USED YET 1/5/25
ENABLE_STRATEGIES = True  # Set this to True to use strategies
STRATEGY_MIN_CONFIDENCE = 0.7  # Minimum confidence to act on strategy signals

# Sleep time between main agent runs
SLEEP_BETWEEN_RUNS_MINUTES = 15  # How long to sleep between agent runs 🕒

# in our nice_funcs in token over view we look for minimum trades last hour
MIN_TRADES_LAST_HOUR = 2


# Future variables (not active yet) 🔮
sell_at_multiple = 3
USDC_SIZE = 1
limit = 49
timeframe = "15m"
stop_loss_perctentage = -0.24
EXIT_ALL_POSITIONS = False
DO_NOT_TRADE_LIST = ["777"]
CLOSED_POSITIONS_TXT = "777"
minimum_trades_in_last_hour = 777
