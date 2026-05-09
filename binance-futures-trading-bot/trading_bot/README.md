# Binance Futures Testnet Trading Bot

A clean, modular Python CLI project for placing `MARKET` and `LIMIT` orders on **Binance USDT-M Futures Testnet** using the `python-binance` library.

The bot is designed to be interview-ready and practical:

- Modular project structure
- CLI powered by `argparse`
- Environment-based API key management with `.env`
- Request, response, and error logging
- Validation for symbol, quantity, order type, side, and limit price
- Friendly success and failure output
- Windows-compatible console behavior with optional colored output

Binance Futures Testnet base URL used by this project:

`https://testnet.binancefuture.com`

When `python-binance` is initialized with `testnet=True`, Futures requests are routed to Binance's Futures Testnet endpoint.

## Project Structure

```text
trading_bot/
│
├── bot/
│   ├── __init__.py
│   ├── client.py
│   ├── orders.py
│   ├── validators.py
│   └── logging_config.py
│
├── logs/
│   └── trading.log
│
├── cli.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Features

- Places `MARKET` and `LIMIT` futures orders
- Supports both `BUY` and `SELL`
- Validates required CLI inputs before sending requests
- Confirms the symbol exists on Binance USDT-M Futures Testnet
- Validates quantity and price against exchange filters when metadata is available
- Logs all requests, responses, and errors with timestamps
- Handles common failures including invalid symbols, invalid quantities, network issues, and Binance API rejections

## Requirements

- Python 3.10+
- A Binance Futures Testnet account
- Binance Futures Testnet API key and secret

## Setup

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root by copying `.env.example` and then replace the values with your Binance Futures Testnet keys:

```env
BINANCE_API_KEY=your_real_testnet_api_key
BINANCE_API_SECRET=your_real_testnet_api_secret
```

## Usage

Run commands from inside the `trading_bot` directory.

### Place a MARKET order

```powershell
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### Place a LIMIT order

```powershell
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 90000
```

### Enable verbose logging

```powershell
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001 --verbose
```

## Sample CLI Output

### MARKET order request summary

```text
Request Summary
Environment : Binance Futures Testnet
Endpoint    : https://testnet.binancefuture.com
Symbol      : BTCUSDT
Side        : BUY
Order Type  : MARKET
Quantity    : 0.001
```

### Sample successful order response

```json
{
  "avgPrice": "0.00",
  "clientOrderId": "x-Cb7ytekJ2f4d7b8a1c2d3e",
  "cumQuote": "95.43210",
  "executedQty": "0.001",
  "orderId": 12837465,
  "origQty": "0.001",
  "price": "0",
  "reduceOnly": false,
  "side": "BUY",
  "status": "FILLED",
  "symbol": "BTCUSDT",
  "timeInForce": "GTC",
  "type": "MARKET",
  "updateTime": 1778319035123
}
```

### Sample validation failure

```text
Validation error: Price is required.
```

### Sample exchange rejection

```text
Order placement failed: Binance API rejected the order: HTTP 400 | code -1111 | Precision is over the maximum defined for this asset.
```

## Logging

Logs are written to:

`logs/trading.log`

The bot logs:

- Incoming CLI request details
- Order submission payloads
- Binance order responses
- Validation failures
- Network issues and API errors

Example log entries:

```text
2026-05-09 10:30:12 | INFO | trading_bot.cli | CLI request received for symbol=BTCUSDT side=BUY type=MARKET quantity=0.001 price=None
2026-05-09 10:30:13 | INFO | trading_bot.cli | Submitting Binance Futures order request: {"symbol": "BTCUSDT", "side": "BUY", "type": "MARKET", "quantity": "0.001", "newOrderRespType": "RESULT"}
2026-05-09 10:30:14 | INFO | trading_bot.cli | Binance order response: {"orderId": 12837465, "symbol": "BTCUSDT", "status": "FILLED"}
```

## Error Handling

The project explicitly handles:

- Invalid symbol format
- Symbols not listed on Binance USDT-M Futures Testnet
- Invalid quantity values
- Missing price for `LIMIT` orders
- Price supplied to `MARKET` orders
- Network failures while contacting Binance
- Binance API errors returned during order placement
- Missing API credentials

## Notes

- This bot uses real order endpoints on the **Binance Futures Testnet**, not local mock data.
- Testnet balances and permissions must be configured in your Binance Testnet account.
- For `LIMIT` orders, the project automatically sends `timeInForce=GTC`.
- The bot validates inputs locally first, then validates them against Binance exchange metadata before placing the order.

## Quick Interview Talking Points

- Separation of concerns: CLI, client management, validators, order submission, and logging are split into dedicated modules.
- Safer trading workflow: local validation reduces avoidable API calls and improves user feedback.
- Production-style logging: both console and rotating file handlers are configured.
- Testnet-first design: the project is wired for Binance USDT-M Futures Testnet from the start.
