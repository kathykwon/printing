import argparse
import logging
import os
from datetime import datetime
from enum import Enum
from pprint import pprint

from pandas import DataFrame
from yfinance import Ticker

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

DEFAULT = ["MSFT", "AAPL", "TSLA", "NVDA"]


class OptionType(Enum):
    CALL = "call"
    PUT = "put"


class Printing:
    """Wrapper for yfinance API."""

    def __init__(self, symbol: str) -> None:
        self._symbol = symbol

    @property
    def ticker(self) -> Ticker:
        LOGGER.info(f"Getting stock information for {self._symbol}")
        return Ticker(self._symbol)

    @property
    def today(self) -> str:
        return datetime.today().strftime("%Y-%m-%d")

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
            print(f"{n["title"]}")
            print(f"{n["url"]}")
            print(f"Related to: {n["related_tickers"]}")
            print("===================================================")

        return news

    def get_options_data(self, type: OptionType, date: str | None = None):
        """Get option chain for specific expiration.

        Defaults to today
        """
        _date = date or self.today
        options = self.ticker.option_chain(_date)

        if type == OptionType.CALL:
            return options.calls
        return options.puts

    def full_info(self) -> None:
        """Gets the full information for this company."""
        pprint(self.ticker.info)

    def get_insider_info(self) -> None:
        # pprint(self.ticker.institutional_holders)
        print("Insider purchases:")
        pprint(self.ticker.insider_purchases)

        print("\n\nInsider roster holders:")
        pprint(self.ticker.insider_roster_holders)

        print("\n\nInsider transactions:")
        pprint(self.ticker.insider_transactions)

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


class PrintingCli:

    def get_arg_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(
            metavar="cmd", help="The endpoint to hit.", required=True
        )
        self._add_get_price(subparsers)
        self._add_get_news(subparsers)
        self._add_get_insider_info(subparsers)
        self._add_get_financials(subparsers)
        self._add_get_recs(subparsers)

        return parser

    #
    # price
    # Get stock price information.
    #

    def _add_get_price(
        self, subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]"
    ) -> None:
        subparser = subparsers.add_parser("price", help="Gets the current stock price.")
        subparser.add_argument(
            "--symbol",
            required=False,
            help=f"The ticker symbol to look at. Looks at {DEFAULT} if not set.",
        )
        subparser.set_defaults(func=self._do_get_price)

    def _do_get_price(self, args: argparse.Namespace) -> None:
        if args.symbol is None:
            symbols = DEFAULT
        else:
            symbols = args.symbol.split(",")

        for symbol in symbols:
            stock = Printing(symbol)
            pprint(stock.price)

    #
    # news
    # Latest news on the stock.
    #

    def _add_get_news(
        self, subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]"
    ) -> None:
        subparser = subparsers.add_parser("news", help="Gets latest news.")
        subparser.add_argument(
            "--symbol",
            required=False,
            help=f"The ticker symbol to look at. Looks at {DEFAULT} if not set.",
        )
        subparser.set_defaults(func=self._do_get_news)

    def _do_get_news(self, args: argparse.Namespace) -> None:
        if args.symbol is None:
            symbols = DEFAULT
        else:
            symbols = args.symbol.split(",")

        for symbol in symbols:
            stock = Printing(symbol)
            stock.news

    #
    # insider
    # Latest insider information on the stock.
    #

    def _add_get_insider_info(
        self, subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]"
    ) -> None:
        subparser = subparsers.add_parser("insider", help="Gets insider information.")
        subparser.add_argument(
            "--symbol",
            required=False,
            help=f"The ticker symbol to look at. Looks at {DEFAULT} if not set.",
        )
        subparser.set_defaults(func=self._do_get_insider_info)

    def _do_get_insider_info(self, args: argparse.Namespace) -> None:
        if args.symbol is None:
            symbols = DEFAULT
        else:
            symbols = args.symbol.split(",")

        for symbol in symbols:
            stock = Printing(symbol)
            stock.get_insider_info()

    #
    # financials
    # Stock recommendations.
    #

    def _add_get_financials(
        self, subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]"
    ) -> None:
        subparser = subparsers.add_parser(
            "financials", help="Gets financial information."
        )
        subparser.add_argument(
            "--symbol",
            required=False,
            help=f"The ticker symbol to look at. Looks at {DEFAULT} if not set.",
        )
        subparser.add_argument(
            "--quarterly",
            action="store_true",
            help=f"Get the quarterly report if set to True.",
        )
        subparser.set_defaults(func=self._do_get_financials)

    def _do_get_financials(self, args: argparse.Namespace) -> None:
        if args.symbol is None:
            symbols = DEFAULT
        else:
            symbols = args.symbol.split(",")

        for symbol in symbols:
            stock = Printing(symbol)
            stock.get_financials(args.quarterly)

    #
    # recs
    # Stock recommendations.
    #

    def _add_get_recs(
        self, subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]"
    ) -> None:
        subparser = subparsers.add_parser("recs", help="Gets recs information.")
        subparser.add_argument(
            "--symbol",
            required=False,
            help=f"The ticker symbol to look at. Looks at {DEFAULT} if not set.",
        )
        subparser.set_defaults(func=self._do_get_recs)

    def _do_get_recs(self, args: argparse.Namespace) -> None:
        if args.symbol is None:
            symbols = DEFAULT
        else:
            symbols = args.symbol.split(",")

        for symbol in symbols:
            stock = Printing(symbol)
            stock.get_recommendations()


def printing_cli() -> None:
    cli = PrintingCli()
    parser = cli.get_arg_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    printing_cli()
