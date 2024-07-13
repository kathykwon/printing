import json
import logging
from datetime import datetime
from enum import Enum
from pprint import pprint

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession
from yfinance import Ticker

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


class OptionType(Enum):
    CALL = "call"
    PUT = "put"

    @classmethod
    def parse(cls, value: object) -> "OptionType":
        try:
            return cls(value)
        except ValueError as e:
            raise ValueError(f"Option type '{value}' is not supported") from e


class Printing:
    """Wrapper for yfinance API."""

    def __init__(self, symbol: str) -> None:
        self._symbol = symbol.upper()

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

    def display(self, data: DataFrame | dict, count: int | None = None) -> None:
        """Wrapper for outputting data to CLI in a readable manner."""
        if type(data) == dict:
            print(json.dumps(data, indent=4))
        elif type(data) == DataFrame:
            if count is None:
                count = data.count()  # show all rows by default
            data.show(count, False)

    def get_history(self, lookback_months: int = 1) -> DataFrame:
        """Get historical market data."""
        hist = self.ticker.history(period=f"{lookback_months}mo")
        # show meta information about the history (requires history() to be called first)
        self.ticker.history_metadata
        return hist

    @property
    def price(self) -> dict:
        data = {
            "symbol": self._symbol,
            "current_price": self.ticker.info["currentPrice"],
            "open": self.ticker.info["open"],
            "day_high": self.ticker.info["dayHigh"],
            "day_low": self.ticker.info["dayLow"],
            "previous_close": self.ticker.info["previousClose"],
            "volume": self.ticker.info["volume"],
            "target_mean_price": self.ticker.info["targetMeanPrice"],
            "target_median_price": self.ticker.info["targetMedianPrice"],
        }
        self.display(data)
        return data

    @property
    def news(self) -> list[dict]:
        news = []
        for article in self.ticker.news:
            data = {
                "title": article["title"],
                "related_tickers": article["relatedTickers"],
                "url": article["link"],
            }
            news.append(data)

            print(f"{data["title"]}\n")
            print(f"{data["url"]}\n")
            print(f"Related to: {data["related_tickers"]}")
            print("==============================================================================")

        return news

    def get_options(self, type: str, date: str | None, count: int | None) -> DataFrame:
        """Get option chain for specific expiration.

        Defaults to today.
        """
        _date = date or self.today
        options = self.ticker.option_chain(_date)

        option_type = OptionType.parse(type)
        if option_type == OptionType.CALL:
            df = self.spark.createDataFrame(options.calls)
        else:
            df = self.spark.createDataFrame(options.puts)

        df = df.select(
            F.col("contractSymbol").alias("contract"),
            F.col("lastTradeDate").alias("last_trade_date"),
            F.col("strike"),
            F.col("lastPrice").alias("last_price"),
            F.col("bid"),
            F.col("ask"),
            F.col("change").alias("change"),
            F.col("percentChange").alias("percent_change"),
            F.col("volume"),
            F.col("openInterest").alias("open_interest"),
            F.col("impliedVolatility").alias("volatility"),
        )

        self.display(df, count)
        return df

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

        self.display(df, count)
        return df

    def _get_insider_transactions(self, count: int | None) -> DataFrame:
        """Get latest insider transaction data."""
        df = self.spark.createDataFrame(self.ticker.insider_transactions)

        df = df.select(
            F.to_date(F.col("Start Date")).alias("date"),
            F.col("Shares").alias("share_count"),
            F.format_number("Value", 0).alias("USD"),
            F.col("Insider").alias("name"),
            F.col("Position").alias("job_title"),
            F.col("Text").alias("description"),
        )

        self.display(df, count)
        return df

    def get_financials(self, count: int | None, is_quarterly: bool = False) -> None:
        """Show financial data.

        See `Ticker.get_income_stmt()` for more options.
        """
        if is_quarterly:
            income_df = self.spark.createDataFrame(self.ticker.quarterly_income_stmt)
            balance_df = self.spark.createDataFrame(self.ticker.quarterly_balance_sheet)
            cashflow_df = self.spark.createDataFrame(self.ticker.quarterly_cashflow)
        else:
            income_df = self.spark.createDataFrame(self.ticker.income_stmt)
            balance_df = self.spark.createDataFrame(self.ticker.balance_sheet)
            cashflow_df = self.spark.createDataFrame(self.ticker.cashflow)

        print("Income Statement:")
        self.display(income_df, count)

        print("Balance sheet:")
        self.display(balance_df, count)

        print("Cash flow:")
        self.display(cashflow_df, count)

    def get_recommendations(self, count: int | None) -> DataFrame:
        """Show recommendations."""
        # recs summary
        recs_df = self.spark.createDataFrame(self.ticker.recommendations)
        print(f"{self._symbol} Summary:")
        self.display(recs_df, count)

        # upgrades/downgrades
        pdf = self.ticker.upgrades_downgrades.rename_axis(["GradeDate"]).reset_index()
        movement_df = self.spark.createDataFrame(pdf)

        movement_df = movement_df.select(
            F.col("GradeDate").alias("date"),
            F.col("Firm").alias("firm"),
            F.col("FromGrade").alias("from"),
            F.col("ToGrade").alias("to"),
            F.col("Action").alias("action"),
        )

        print(f"{self._symbol} Recommendations:")
        self.display(movement_df, count)
        return movement_df

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
