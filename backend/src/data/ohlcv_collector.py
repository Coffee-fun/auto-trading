import os

import pandas as pd
from termcolor import cprint

from src import nice_funcs as n
from src.config import *


def get_wallet_owned_tokens(wallet_address: str):
    """Get tokens owned by a wallet"""
    response: pd.DataFrame = n.fetch_wallet_holdings_og(wallet_address)
    if response.empty:
        return []
    return [x for x in response["Mint Address"].tolist() if x not in EXCLUDED_TOKENS]


def collect_token_data(
    token, days_back=DAYSBACK_4_DATA, timeframe=DATA_TIMEFRAME, logger=None
):
    if not logger:

        def logger(message, *ignore):
            print(message)

    """Collect OHLCV data for a single token"""
    logger(f"fetching data for {token}", "white", "on_blue")

    try:
        # Get data from Birdeye
        data = n.get_data(token, days_back, timeframe)

        if data is None or data.empty:
            logger(
                f"Couldn't fetch data for {token}",
                "white",
                "on_red",
            )
            return None

        logger(
            f"processed {len(data)} candles for analysis",
            "white",
            "on_blue",
        )

        # Save data if configured
        if SAVE_OHLCV_DATA:
            save_path = f"data/{token}_latest.csv"
        else:
            save_path = f"temp_data/{token}_latest.csv"

        # Ensure directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # Save to CSV
        data.to_csv(save_path)
        logger(f"cached data for {token[:4]}", "white", "on_green")

        return data

    except Exception as e:
        cprint(f"encountered an error: {str(e)}", "white", "on_red")
        return None


def collect_all_tokens(user_tokens, logger=None):
    """Collect OHLCV data for all monitored tokens"""
    market_data = {}

    if logger is None:

        def logger(message, *ignore):
            print(message)

    logger(
        "starting market data collection...",
        "white",
        "on_blue",
    )

    for token in user_tokens:
        data = collect_token_data(token, logger=logger)
        if data is not None:
            market_data[token] = data

    logger(
        "completed market data collection!",
        "white",
        "on_green",
    )

    return market_data
