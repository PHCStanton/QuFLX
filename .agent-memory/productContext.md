# Product Context

## Project Purpose
QuantumFlux is a sophisticated automated trading platform for PocketOption that leverages WebSocket data streaming, Selenium automation, and AI-driven trading strategies. The platform uses a hybrid Chrome session approach for persistent connections and real-time market data collection.

## Problem Statement
- **Manual Trading Limitations**: Manual trading on PocketOption is time-consuming and prone to human error
- **Data Collection Challenges**: Real-time market data collection requires complex WebSocket interception
- **Session Management**: Maintaining persistent browser sessions for continuous trading operations
- **Strategy Execution**: Need for automated signal generation and trade execution based on technical analysis
- **Backend Integration**: Complex architectural challenges in integrating multiple trading capabilities

## Intended Users
- **Algorithmic Traders**: Developers and traders who want to automate their PocketOption trading strategies
- **Data Analysts**: Users who need real-time market data collection and analysis
- **Trading System Developers**: Engineers building automated trading systems
- **Quantitative Researchers**: Researchers analyzing market patterns and developing trading algorithms

## Core Functionality
- **Real-time Data Streaming**: WebSocket data collection with candle formation and configurable persistence (chunked CSV rotation: candles=100, ticks=1000) with clear session roles (collector ON by default; strategy sessions OFF by default with opt-in controls)
- **Chrome Session Management**: Persistent browser sessions with remote debugging
- **Trading Operations**: Profile scanning, favorites management, session monitoring, and trade execution
- **Signal Generation**: Technical analysis with SMA, RSI, MACD indicators
- **API Interface**: FastAPI backend with REST endpoints and WebSocket streaming
- **CLI Tools**: Command-line interface for all trading operations
- **Strategy Management**: A/B testing, automated trading, and strategy performance tracking

## Success Metrics
- **Data Collection Reliability**: >99% uptime for WebSocket data streaming
- **Trade Execution Success**: >95% successful trade execution rate
- **API Response Time**: <500ms for all API endpoints
- **Session Persistence**: Stable Chrome session management across restarts
- **CSV Data Export**: Automatic persistence with chunked rotation to:
  - Candles: data/data_output/assets_data/realtime_stream/1M_candle_data
  - Ticks:   data/data_output/assets_data/realtime_stream/1M_tick_data
- **System Integration**: Clean, working backend without architectural conflicts
## Product Direction Addendum (2025-10-06)

- Align data visualization with Pocket Option UI: strict per-asset isolation; ensure live stream and historical data sources match the selected asset.
- Automatic source sensing preferred over manual dropdown: seamlessly use streaming when available; fallback to historical without user friction; display source status.
- Support timeframe controls consistent with trading platforms; ensure cache resets on resolution change to maintain integrity.
