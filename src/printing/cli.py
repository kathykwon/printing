import argparse
import logging
from pprint import pprint

from printing.printing import Printing

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

DEFAULT = ["MSFT", "AAPL", "TSLA", "NVDA", "AMD"]


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
        self._add_get_options(subparsers)

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
            "-s",
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
            stock.price

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
            "-s",
            required=False,
            help=f"The ticker symbol to look at. Looks at {DEFAULT} if not set.",
        )
        subparser.add_argument(
            "--type",
            required=True,
            help="'transacton' for insider transactions, 'buy' for purchase information.",
        )
        subparser.add_argument(
            "--count",
            "-c",
            type=int,
            required=False,
            help="Max row count to display.",
        )
        subparser.set_defaults(func=self._do_get_insider_info)

    def _do_get_insider_info(self, args: argparse.Namespace) -> None:
        if args.symbol is None:
            symbols = DEFAULT
        else:
            symbols = args.symbol.split(",")

        for symbol in symbols:
            stock = Printing(symbol)
            stock.get_insider_info(args.type, args.count)

    #
    # financials
    # Stock recommendations.
    #

    def _add_get_financials(
        self, subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]"
    ) -> None:
        subparser = subparsers.add_parser("financials", help="Gets financial information.")
        subparser.add_argument(
            "--symbol",
            "-s",
            required=False,
            help=f"The ticker symbol to look at. Looks at {DEFAULT} if not set.",
        )
        subparser.add_argument(
            "--quarterly",
            action="store_true",
            help="Get the quarterly report if set to True.",
        )
        subparser.add_argument(
            "--count",
            "-c",
            type=int,
            required=False,
            help="Max row count to display.",
        )
        subparser.set_defaults(func=self._do_get_financials)

    def _do_get_financials(self, args: argparse.Namespace) -> None:
        if args.symbol is None:
            symbols = DEFAULT
        else:
            symbols = args.symbol.split(",")

        for symbol in symbols:
            stock = Printing(symbol)
            stock.get_financials(args.count, args.quarterly)

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
            "-s",
            required=False,
            help=f"The ticker symbol to look at. Looks at {DEFAULT} if not set.",
        )
        subparser.add_argument(
            "--count",
            "-c",
            type=int,
            required=False,
            help="Max row count to display.",
        )
        subparser.set_defaults(func=self._do_get_recs)

    def _do_get_recs(self, args: argparse.Namespace) -> None:
        if args.symbol is None:
            symbols = DEFAULT
        else:
            symbols = args.symbol.split(",")

        for symbol in symbols:
            stock = Printing(symbol)
            stock.get_recommendations(args.count)

    #
    # options
    # Options information for the stock.
    #

    def _add_get_options(
        self, subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]"
    ) -> None:
        subparser = subparsers.add_parser("options", help="Gets options information.")
        subparser.add_argument(
            "--symbol",
            "-s",
            required=False,
            help=f"The ticker symbol to look at. Looks at {DEFAULT} if not set.",
        )
        subparser.add_argument(
            "--type",
            required=True,
            help="Option type: 'call' or 'put'.",
        )
        subparser.add_argument(
            "--date",
            required=False,
            help="Date in the format of 'YYYY-MM-DD'.",
        )
        subparser.add_argument(
            "--count",
            "-c",
            type=int,
            required=False,
            help="Max row count to display.",
        )
        subparser.set_defaults(func=self._do_get_options)

    def _do_get_options(self, args: argparse.Namespace) -> None:
        if args.symbol is None:
            symbols = DEFAULT
        else:
            symbols = args.symbol.split(",")

        for symbol in symbols:
            stock = Printing(symbol)
            stock.get_options(args.type, args.date, args.count)


def printing_cli() -> None:
    cli = PrintingCli()
    parser = cli.get_arg_parser()
    args = parser.parse_args()
    args.func(args)


def main() -> None:
    printing_cli()
