"""CLI entrypoint for the Binance Futures Testnet trading bot."""

from __future__ import annotations

import argparse
import logging
import sys

try:
    from colorama import Fore, Style, just_fix_windows_console
except ImportError:  # pragma: no cover - exercised at runtime if deps are missing.
    class _PlainColor:
        RED = ""
        GREEN = ""
        CYAN = ""
        YELLOW = ""
        RESET_ALL = ""

    Fore = Style = _PlainColor()  # type: ignore[assignment]

    def just_fix_windows_console() -> None:
        return None

from bot.client import (
    BINANCE_FUTURES_TESTNET_URL,
    BinanceConnectionError,
    DependencyError,
    MissingCredentialsError,
    close_client,
    get_futures_client,
    get_futures_symbol_info,
    verify_futures_connectivity,
)
from bot.logging_config import setup_logging
from bot.orders import (
    OrderPlacementError,
    build_request_summary,
    format_order_response,
    place_futures_order,
)
from bot.validators import (
    ValidationError,
    build_order_request,
    validate_order_against_symbol_filters,
    validate_symbol_metadata,
)


def parse_args() -> argparse.Namespace:
    """Define and parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Place MARKET or LIMIT orders on Binance Futures Testnet (USDT-M).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--symbol",
        required=True,
        help="USDT-M futures symbol, for example BTCUSDT.",
    )
    parser.add_argument(
        "--side",
        required=True,
        help="Order side: BUY or SELL.",
    )
    parser.add_argument(
        "--type",
        dest="order_type",
        required=True,
        help="Order type: MARKET or LIMIT.",
    )
    parser.add_argument(
        "--quantity",
        required=True,
        help="Order quantity, for example 0.001.",
    )
    parser.add_argument(
        "--price",
        help="Limit price. Required only for LIMIT orders.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level logging.",
    )
    return parser.parse_args()


def print_info(message: str) -> None:
    print(f"{Fore.CYAN}{message}{Style.RESET_ALL}")


def print_success(message: str) -> None:
    print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")


def print_warning(message: str) -> None:
    print(f"{Fore.YELLOW}{message}{Style.RESET_ALL}")


def print_error(message: str) -> None:
    print(f"{Fore.RED}{message}{Style.RESET_ALL}", file=sys.stderr)

def main() -> int:
    """Run the CLI workflow."""
    just_fix_windows_console()
    args = parse_args()
    log_level = logging.DEBUG if args.verbose else logging.INFO
    log_file = setup_logging(log_level)
    logger = logging.getLogger("trading_bot.cli")

    client = None

    try:
        order_request = build_order_request(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
        )

        logger.info(
            "CLI request received for symbol=%s side=%s type=%s quantity=%s price=%s",
            order_request.symbol,
            order_request.side,
            order_request.order_type,
            args.quantity,
            args.price,
        )

        print_info(build_request_summary(order_request, BINANCE_FUTURES_TESTNET_URL))

        client = get_futures_client()
        verify_futures_connectivity(client)

        symbol_info = get_futures_symbol_info(client, order_request.symbol)
        validate_symbol_metadata(symbol_info, order_request.symbol)
        validate_order_against_symbol_filters(order_request, symbol_info)

        response = place_futures_order(client, order_request, logger=logger)

        print_success("\nSuccess: Order accepted by Binance Futures Testnet.")
        print_info("\nOrder Response")
        print(format_order_response(response))
        print_info(f"\nLogs written to: {log_file}")
        return 0

    except ValidationError as exc:
        logger.warning("Validation failed: %s", exc)
        print_error(f"Validation error: {exc}")
        print_warning(f"See log file for details: {log_file}")
        return 1
    except MissingCredentialsError as exc:
        logger.error("Missing credentials: %s", exc)
        print_error(str(exc))
        return 2
    except DependencyError as exc:
        logger.error("Dependency issue: %s", exc)
        print_error(str(exc))
        return 3
    except BinanceConnectionError as exc:
        logger.error("Connectivity error: %s", exc, exc_info=True)
        print_error(f"Connectivity error: {exc}")
        print_warning(f"See log file for details: {log_file}")
        return 4
    except OrderPlacementError as exc:
        logger.error("Order placement failed: %s", exc, exc_info=True)
        print_error(f"Order placement failed: {exc}")
        print_warning(f"See log file for details: {log_file}")
        return 5
    except KeyboardInterrupt:
        logger.warning("Execution interrupted by user.")
        print_warning("\nExecution cancelled by user.")
        return 130
    except Exception as exc:  # pragma: no cover - defensive safety net.
        logger.exception("Unexpected application error: %s", exc)
        print_error(f"Unexpected error: {exc}")
        print_warning(f"See log file for details: {log_file}")
        return 99
    finally:
        close_client(client)


if __name__ == "__main__":
    raise SystemExit(main())
