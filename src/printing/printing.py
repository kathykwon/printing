import logging
from datetime import datetime
from enum import Enum
from pprint import pprint

import pandas as pd
import pyspark.sql.functions as F
from pandas import DataFrame
from pyspark.sql import DataFrame, SparkSession
from yfinance import Ticker

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


class OptionType(Enum):
    CALL = "call"
    PUT = "put"


class Printing:
    """Wrapper for yfinance API."""

    def __init__(self, symbol: str) -> None:
        self._symbol = symbol

    @property
    def spark(self) -> SparkSession:
        spark_session = SparkSession.builder.appName(self._symbol).getOrCreate()
        return spark_session

    @property
    def ticker(self) -> Ticker:
        LOGGER.info(f"Getting stock information for {self._symbol}")
        return Ticker(self._symbol)

    @property
    def today(self) -> str:
        return datetime.today().strftime("%Y-%m-%d")

    @staticmethod
    def display_df(df: DataFrame, count: int | None) -> None:
        if count is None:
            count = df.count()  # show all rows by default

        df.show(count, False)

    def get_history(self, lookback_months: int = 1) -> DataFrame:
        """Get historical market data."""
        hist = self.ticker.history(period=f"{lookback_months}mo")
        # show meta information about the history (requires history() to be called first)
        self.ticker.history_metadata
        return hist

    @property
    def price(self) -> dict:
        return {
            "current_price": self.ticker.info["currentPrice"],
            "open": self.ticker.info["open"],
            "day_high": self.ticker.info["dayHigh"],
            "day_low": self.ticker.info["dayLow"],
            "previous_close": self.ticker.info["previousClose"],
            "volume": self.ticker.info["volume"],
            "target_mean_price": self.ticker.info["targetMeanPrice"],
            "target_median_price": self.ticker.info["targetMedianPrice"],
        }

    @property
    def news(self) -> list[dict]:
        news = []
        for article in self.ticker.news:
            news.append(
                {
                    "title": article["title"],
                    "related_tickers": article["relatedTickers"],
                    "url": article["link"],
                }
            )

        for n in news:
            print(f"{n["title"]}\n")
            print(f"{n["url"]}\n")
            print(f"Related to: {n["related_tickers"]}")
            print("===================================================")

        return news

    def get_options_data(self, type: OptionType, date: str | None = None):
        """Get option chain for specific expiration.

        Defaults to today.
        """
        _date = date or self.today
        options = self.ticker.option_chain(_date)

        if type == OptionType.CALL:
            return options.calls
        return options.puts

    def full_info(self) -> None:
        """Gets the full information for this company."""
        pprint(self.ticker.info)

    def get_insider_info(self, type: str | None, count: int | None) -> None:
        if type == "buy":
            LOGGER.info("Getting insider purchases...")
            self._get_insider_purchases(count)

        if type == "transaction":
            LOGGER.info("Getting insider transactions...")
            return self._get_insider_transactions(count)

        # pprint(self.ticker.institutional_holders)
        # print("\n\nInsider roster holders:")
        # pprint(self.ticker.insider_roster_holders)

    def _get_insider_purchases(self, count: int | None) -> DataFrame:
        """Get latest insider transaction data."""
        df = self.spark.createDataFrame(self.ticker.insider_purchases)

        self.display_df(df, count)
        return df

    def _get_insider_transactions(self, count: int | None) -> DataFrame:
        """Get latest insider transaction data."""
        df = self.spark.createDataFrame(self.ticker.insider_transactions)

        df = df.select(
            F.col("Shares").alias("share_count"),
            F.col("Value"),
            F.col("Text").alias("transaction_description"),
            F.col("Insider").alias("name"),
            F.col("Position").alias("job_title"),
            F.col("Start Date").alias("transaction_date"),
        ).withColumn("USD", F.format_number("Value", 0))

        self.display_df(df, count)
        return df

    def get_financials(self, is_quarterly: bool = False) -> None:
        """Show financial data.

        See `Ticker.get_income_stmt()` for more options.
        """
        if is_quarterly:
            print("Quarterly Income Statement:")
            pprint(self.ticker.quarterly_income_stmt)
            print("Quarterly Balance sheet:")
            pprint(self.ticker.quarterly_balance_sheet)
            print("Quarterly Cash Flow:")
            pprint(self.ticker.quarterly_cashflow)
            return

        print("Income Statement:")
        pprint(self.ticker.income_stmt)
        print("Balance sheet:")
        pprint(self.ticker.balance_sheet)
        print("Cash flow:")
        pprint(self.ticker.cashflow)

    def get_recommendations(self):
        """Show recommendations."""
        print("Recommendations:")
        pprint(self.ticker.recommendations)
        print("\n\nRecommendations Summary:")
        pprint(self.ticker.recommendations_summary)
        print("\n\nUpgrades/downgrades:")
        pprint(self.ticker.upgrades_downgrades)

    # def show_actions(self) -> None:
    #     # show actions (dividends, splits, capital gains)
    #     self.ticker.actions
    #     self.ticker.dividends
    #     self.ticker.splits
    #     self.ticker.capital_gains  # only for mutual funds & etfs

    #     # show share count
    #     self.ticker.get_shares_full(start="2022-01-01", end=None)

    # def earnings_date(self):
    #     """Show future and historic earnings dates, returns at most next 4 quarters and last 8 quarters by default."""
    #     self.ticker.earnings_dates
