"""Validation helpers for CLI arguments and Binance Futures rules."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re
from typing import Any, Mapping

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{5,20}$")


class ValidationError(ValueError):
    """Raised when user input does not satisfy local or exchange rules."""


@dataclass(frozen=True)
class OrderRequest:
    """Normalized order parameters used throughout the application."""

    symbol: str
    side: str
    order_type: str
    quantity: Decimal
    price: Decimal | None = None


def normalize_symbol(symbol: str) -> str:
    """Validate and normalize the trading symbol."""
    normalized = symbol.strip().upper()
    if not normalized:
        raise ValidationError("Symbol is required.")
    if not SYMBOL_PATTERN.fullmatch(normalized):
        raise ValidationError(
            "Symbol format is invalid. Use a Binance Futures symbol such as BTCUSDT."
        )
    return normalized


def normalize_side(side: str) -> str:
    """Validate and normalize the order side."""
    normalized = side.strip().upper()
    if normalized not in VALID_SIDES:
        raise ValidationError("Side must be BUY or SELL.")
    return normalized


def normalize_order_type(order_type: str) -> str:
    """Validate and normalize the order type."""
    normalized = order_type.strip().upper()
    if normalized not in VALID_ORDER_TYPES:
        raise ValidationError("Order type must be MARKET or LIMIT.")
    return normalized


def parse_positive_decimal(raw_value: str | None, field_name: str) -> Decimal:
    """Parse numeric user input while preserving decimal precision."""
    if raw_value is None:
        raise ValidationError(f"{field_name} is required.")

    candidate = raw_value.strip()
    if not candidate:
        raise ValidationError(f"{field_name} is required.")

    try:
        value = Decimal(candidate)
    except InvalidOperation as exc:
        raise ValidationError(f"{field_name} must be a valid number.") from exc

    if value <= 0:
        raise ValidationError(f"{field_name} must be greater than zero.")

    return value.normalize()


def build_order_request(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: str | None,
) -> OrderRequest:
    """Create a strongly validated order request object."""
    normalized_symbol = normalize_symbol(symbol)
    normalized_side = normalize_side(side)
    normalized_order_type = normalize_order_type(order_type)
    normalized_quantity = parse_positive_decimal(quantity, "Quantity")
    normalized_price = None

    if normalized_order_type == "LIMIT":
        normalized_price = parse_positive_decimal(price, "Price")
    elif price is not None:
        raise ValidationError("Price can only be supplied for LIMIT orders.")

    return OrderRequest(
        symbol=normalized_symbol,
        side=normalized_side,
        order_type=normalized_order_type,
        quantity=normalized_quantity,
        price=normalized_price,
    )


def validate_symbol_metadata(symbol_info: Mapping[str, Any] | None, symbol: str) -> None:
    """Ensure the symbol exists and is tradable on USDT-M Futures Testnet."""
    if not symbol_info:
        raise ValidationError(
            f"Symbol '{symbol}' was not found on Binance USDT-M Futures Testnet."
        )

    status = symbol_info.get("status", "UNKNOWN")
    if status != "TRADING":
        raise ValidationError(
            f"Symbol '{symbol}' is not currently tradable. Binance status: {status}."
        )

    quote_asset = symbol_info.get("quoteAsset")
    if quote_asset != "USDT":
        raise ValidationError(
            f"Symbol '{symbol}' is not a USDT-M futures contract. Quote asset: {quote_asset}."
        )


def validate_order_against_symbol_filters(
    order_request: OrderRequest,
    symbol_info: Mapping[str, Any],
) -> None:
    """Validate quantity and price against Binance exchange filters."""
    filters = {
        exchange_filter["filterType"]: exchange_filter
        for exchange_filter in symbol_info.get("filters", [])
    }

    quantity_filter = filters.get("LOT_SIZE")
    if order_request.order_type == "MARKET":
        quantity_filter = filters.get("MARKET_LOT_SIZE", quantity_filter)

    if quantity_filter:
        min_qty = Decimal(quantity_filter["minQty"])
        max_qty = Decimal(quantity_filter["maxQty"])
        step_size = Decimal(quantity_filter["stepSize"])

        _validate_min_value("Quantity", order_request.quantity, min_qty)
        _validate_max_value("Quantity", order_request.quantity, max_qty)
        _validate_step_size("Quantity", order_request.quantity, step_size)

    if order_request.price is not None:
        price_filter = filters.get("PRICE_FILTER")
        if price_filter:
            min_price = Decimal(price_filter["minPrice"])
            max_price = Decimal(price_filter["maxPrice"])
            tick_size = Decimal(price_filter["tickSize"])

            _validate_min_value("Price", order_request.price, min_price)
            _validate_max_value("Price", order_request.price, max_price)
            _validate_step_size("Price", order_request.price, tick_size)


def format_decimal(value: Decimal) -> str:
    """Return a Binance-friendly decimal string without scientific notation."""
    rendered = format(value.normalize(), "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered or "0"


def _validate_min_value(field_name: str, value: Decimal, minimum: Decimal) -> None:
    if minimum > 0 and value < minimum:
        raise ValidationError(
            f"{field_name} must be at least {format_decimal(minimum)}."
        )


def _validate_max_value(field_name: str, value: Decimal, maximum: Decimal) -> None:
    if maximum > 0 and value > maximum:
        raise ValidationError(
            f"{field_name} must be at most {format_decimal(maximum)}."
        )


def _validate_step_size(field_name: str, value: Decimal, step_size: Decimal) -> None:
    if step_size <= 0:
        return

    step_units = value / step_size
    if step_units != step_units.to_integral_value():
        raise ValidationError(
            f"{field_name} must align with the exchange increment of "
            f"{format_decimal(step_size)}."
        )
