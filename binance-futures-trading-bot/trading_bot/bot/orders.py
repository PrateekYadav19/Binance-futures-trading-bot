"""Order request builders and Binance Futures submission helpers."""

from __future__ import annotations

import json
import logging
from typing import Any

from .client import format_binance_error
from .validators import OrderRequest, format_decimal

LOGGER = logging.getLogger(__name__)

try:
    from binance.exceptions import BinanceAPIException, BinanceRequestException
except ImportError:  # pragma: no cover - exercised at runtime if deps are missing.
    BinanceAPIException = Exception  # type: ignore[assignment]
    BinanceRequestException = Exception  # type: ignore[assignment]


class OrderPlacementError(RuntimeError):
    """Raised when Binance rejects an order or a request fails."""


def build_request_summary(
    order_request: OrderRequest,
    endpoint: str,
) -> str:
    """Create a human-readable summary that is printed before submission."""
    lines = [
        "Request Summary",
        f"Environment : Binance Futures Testnet",
        f"Endpoint    : {endpoint}",
        f"Symbol      : {order_request.symbol}",
        f"Side        : {order_request.side}",
        f"Order Type  : {order_request.order_type}",
        f"Quantity    : {format_decimal(order_request.quantity)}",
    ]

    if order_request.price is not None:
        lines.append(f"Price       : {format_decimal(order_request.price)}")

    return "\n".join(lines)


def build_order_payload(order_request: OrderRequest) -> dict[str, str]:
    """Convert a validated order request into a Binance API payload."""
    payload = {
        "symbol": order_request.symbol,
        "side": order_request.side,
        "type": order_request.order_type,
        "quantity": format_decimal(order_request.quantity),
        "newOrderRespType": "RESULT",
    }

    if order_request.price is not None:
        payload["price"] = format_decimal(order_request.price)
        payload["timeInForce"] = "GTC"

    return payload


def place_futures_order(
    client: Any,
    order_request: OrderRequest,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    """Submit a validated Futures order to Binance Testnet."""
    active_logger = logger or LOGGER
    payload = build_order_payload(order_request)

    active_logger.info(
        "Submitting Binance Futures order request: %s",
        json.dumps(payload, ensure_ascii=True),
    )

    try:
        response = client.futures_create_order(**payload)
    except BinanceRequestException as exc:
        active_logger.error(
            "Network failure while placing order: %s",
            format_binance_error(exc),
            exc_info=True,
        )
        raise OrderPlacementError(
            "Network failure while submitting the order to Binance Futures Testnet."
        ) from exc
    except BinanceAPIException as exc:
        active_logger.error(
            "Binance API rejected the order: %s",
            format_binance_error(exc),
            exc_info=True,
        )
        raise OrderPlacementError(
            f"Binance API rejected the order: {format_binance_error(exc)}"
        ) from exc
    except OSError as exc:
        active_logger.error("OS/network failure while placing order: %s", exc, exc_info=True)
        raise OrderPlacementError(
            f"Low-level network failure while placing the order: {exc}"
        ) from exc
    except Exception as exc:
        active_logger.error(
            "Unexpected error while placing order: %s",
            exc,
            exc_info=True,
        )
        raise OrderPlacementError(f"Unexpected order placement failure: {exc}") from exc

    active_logger.info(
        "Binance order response: %s",
        json.dumps(response, default=str, ensure_ascii=True),
    )
    return response


def format_order_response(response: dict[str, Any]) -> str:
    """Pretty-print an order response for the CLI."""
    return json.dumps(response, indent=2, sort_keys=True, default=str)
