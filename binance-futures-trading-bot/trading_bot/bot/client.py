"""Binance Futures Testnet client helpers."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"
BINANCE_FUTURES_TESTNET_URL = "https://testnet.binancefuture.com"
REQUEST_TIMEOUT_SECONDS = 10

_BINANCE_IMPORT_ERROR: Exception | None = None

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException, BinanceRequestException
except ImportError as exc:  # pragma: no cover - exercised at runtime if deps are missing.
    Client = None  # type: ignore[assignment]
    BinanceAPIException = Exception  # type: ignore[assignment]
    BinanceRequestException = Exception  # type: ignore[assignment]
    _BINANCE_IMPORT_ERROR = exc


class DependencyError(RuntimeError):
    """Raised when a required third-party package is unavailable."""


class MissingCredentialsError(RuntimeError):
    """Raised when API keys are missing from the environment."""


class BinanceConnectionError(RuntimeError):
    """Raised when Binance connectivity or metadata calls fail."""


def get_futures_client(
    api_key: str | None = None,
    api_secret: str | None = None,
) -> Any:
    """Create a Binance Futures Testnet client from environment variables."""
    _require_binance_dependency()
    load_dotenv(ENV_FILE)

    resolved_api_key = api_key or os.getenv("BINANCE_API_KEY")
    resolved_api_secret = api_secret or os.getenv("BINANCE_API_SECRET")

    if not resolved_api_key or not resolved_api_secret:
        raise MissingCredentialsError(
            "Missing Binance credentials. Create a .env file from .env.example "
            "and set BINANCE_API_KEY and BINANCE_API_SECRET."
        )

    client = Client(
        api_key=resolved_api_key,
        api_secret=resolved_api_secret,
        testnet=True,
        requests_params={"timeout": REQUEST_TIMEOUT_SECONDS},
    )

    LOGGER.info(
        "Binance Futures Testnet client created for %s",
        BINANCE_FUTURES_TESTNET_URL,
    )
    return client


def verify_futures_connectivity(client: Any) -> None:
    """Check that the Binance Futures Testnet endpoint is reachable."""
    try:
        client.futures_ping()
    except BinanceRequestException as exc:
        raise BinanceConnectionError(
            "Network failure while contacting Binance Futures Testnet. "
            "Check your internet connection, proxy, or firewall settings."
        ) from exc
    except BinanceAPIException as exc:
        raise BinanceConnectionError(
            "Binance returned an API error during connectivity verification: "
            f"{format_binance_error(exc)}"
        ) from exc
    except Exception as exc:
        raise BinanceConnectionError(
            f"Unexpected error while connecting to Binance Futures Testnet: {exc}"
        ) from exc


def get_futures_symbol_info(client: Any, symbol: str) -> dict[str, Any] | None:
    """Fetch a symbol definition from Binance Futures exchange metadata."""
    try:
        exchange_info = client.futures_exchange_info()
    except BinanceRequestException as exc:
        raise BinanceConnectionError(
            "Network failure while downloading Binance Futures exchange info."
        ) from exc
    except BinanceAPIException as exc:
        raise BinanceConnectionError(
            "Binance returned an API error while retrieving exchange info: "
            f"{format_binance_error(exc)}"
        ) from exc
    except Exception as exc:
        raise BinanceConnectionError(
            f"Unexpected error while retrieving exchange info: {exc}"
        ) from exc

    for symbol_info in exchange_info.get("symbols", []):
        if symbol_info.get("symbol") == symbol:
            return symbol_info

    return None


def format_binance_error(error: Exception) -> str:
    """Render Binance and HTTP exception details in a compact format."""
    status_code = getattr(error, "status_code", None)
    code = getattr(error, "code", None)
    message = getattr(error, "message", None) or str(error)

    details: list[str] = []
    if status_code:
        details.append(f"HTTP {status_code}")
    if code not in (None, ""):
        details.append(f"code {code}")
    if message:
        details.append(message)

    return " | ".join(details) if details else error.__class__.__name__


def close_client(client: Any) -> None:
    """Close the client session when the library exposes a close hook."""
    if client is None:
        return

    close_connection = getattr(client, "close_connection", None)
    if callable(close_connection):
        close_connection()


def _require_binance_dependency() -> None:
    if _BINANCE_IMPORT_ERROR is not None or Client is None:
        raise DependencyError(
            "python-binance is not installed. Run `pip install -r requirements.txt` "
            "before using the bot."
        ) from _BINANCE_IMPORT_ERROR
