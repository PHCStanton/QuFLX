# Technical Context

## Technologies Used
- **Python 3.8+**: Core programming language for all components
- **FastAPI**: Modern web framework for REST API backend
- **Selenium WebDriver**: Browser automation for PocketOption interaction
- **Chrome Remote Debugging**: Persistent browser session management
- **WebSocket Interception**: Real-time data collection via performance logs
- **Typer**: Command-line interface framework for CLI tool
- **Pandas**: Data processing and CSV export functionality
- **Uvicorn**: ASGI server for FastAPI backend
- **Pytest**: Testing framework for automated testing

## Development Setup

### Prerequisites
```bash
# Python 3.8+ required
python --version

# Chrome browser installed
# Chrome executable typically at:
# Windows: C:\Program Files\Google\Chrome\Application\chrome.exe
```

### Environment Setup
```bash
# Clone and navigate to project
cd c:\QuFLX

# Install dependencies
pip install -r requirements.txt

# Verify installation
python test_smoke.py
```

### Chrome Session Setup
```bash
# Start persistent Chrome session
python start_hybrid_session.py

# Or use PowerShell launcher
.\scripts\start_all.ps1
```

## Dependencies

### Core Dependencies
- **selenium**: Browser automation and WebDriver management
- **fastapi**: REST API framework and WebSocket support
- **uvicorn**: ASGI server for running FastAPI applications
- **typer**: CLI framework for command-line interface
- **pandas**: Data manipulation and CSV export
- **requests**: HTTP client for API testing
- **redis**: Python Redis client for high-performance data operations
- **mcp**: Model Context Protocol framework for AI tool integration

### Development Dependencies
- **pytest**: Testing framework
- **pytest-asyncio**: Async testing support
- **black**: Code formatting
- **flake8**: Code linting
- **redis-py**: Redis Python client
- **mcp**: Model Context Protocol server framework

## Technical Constraints

### Chrome Session Requirements
- **Remote Debugging Port**: Must use port 9222 for Chrome remote debugging
- **User Data Directory**: Uses workspace `Chrome_profile/` for session persistence
- **PocketOption Login**: Manual login required in Chrome session
- **WebSocket Access**: Requires performance log access for data interception

### System Requirements
- **Windows/Linux**: Cross-platform support with PowerShell/Bash scripts
- **Memory**: Minimum 4GB RAM for Chrome + Python processes
- **Network**: Stable internet connection for PocketOption access
- **Disk Space**: Adequate space for CSV data export and Chrome profile

### API Limitations
- **Rate Limiting**: FastAPI includes basic rate limiting (100 requests/minute)
- **CORS**: Configured for localhost development (ports 3000, 5173)
- **WebSocket Connections**: Single concurrent WebSocket connection supported
- **Session Timeout**: Chrome session requires periodic activity to maintain login

## Coding Standards

### Python Style
- **PEP 8**: Follow Python style guidelines
- **Type Hints**: Use type annotations for function parameters and returns
- **Docstrings**: Document all classes and functions
- **Error Handling**: Use try-catch blocks with specific exception types

### File Organization
```
c:\QuFLX\
├── capabilities/          # Core trading capabilities
├── .agent-memory/         # Agent memory system
├── Historical_Data/       # Data export directory
├── Chrome_profile/        # Chrome session data
├── scripts/              # Automation scripts
├── backend.py            # FastAPI backend
├── qf.py                # CLI interface
└── test_smoke.py        # System verification
```

### Import Conventions
```python
# Standard library imports first
import os
import time
from datetime import datetime

# Third-party imports
from fastapi import FastAPI
from selenium import webdriver

# Local imports
from capabilities.data_streaming import RealtimeDataStreaming
```

## Testing Requirements

### Test Categories
- **Smoke Tests**: Basic system functionality verification
- **Unit Tests**: Individual capability testing
- **Integration Tests**: End-to-end workflow testing
- **API Tests**: REST endpoint and WebSocket testing

### Test Execution
```bash
# Run smoke test
python test_smoke.py

# Run CLI tests
python qf.py attach --port 9222
python qf.py stream snapshot --period 1

# Run API tests
# Start backend: python backend.py
# Test endpoints: curl http://localhost:8000/health
```

### Test Data
- **CSV Export**: Test data saved to `Historical_Data/smoke_test/`
- **Artifacts**: Debug artifacts saved with timestamps
- **Screenshots**: UI interaction screenshots for debugging

## Configuration Management

### Environment Variables
```bash
# Optional environment variables
CHROME_EXECUTABLE_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe
CHROME_USER_DATA_DIR=Chrome_profile
CHROME_DEBUG_PORT=9222
API_HOST=localhost
API_PORT=8000

# Streaming persistence controls (opt-in for strategy/testing sessions)
# Enable both candles and ticks:
QF_PERSIST=1
# Enable only candles:
QF_PERSIST_CANDLES=1
# Enable only ticks:
QF_PERSIST_TICKS=1
```

### Persistence Controls (CLI)
- --save-candles / --save-ticks
- --candle-chunk-size (default: 100 closed candles/file)
- --tick-chunk-size (default: 1000 ticks/file)

Save locations (realtime stream):
- Candles: data/data_output/assets_data/realtime_stream/1M_candle_data
- Ticks:   data/data_output/assets_data/realtime_stream/1M_tick_data

### Configuration Files
- **requirements.txt**: Python dependencies
- **QUICKSTART.md**: User documentation
- **.agent-memory/**: Agent memory system files
- **scripts/start_all.ps1**: PowerShell automation script

## Security Considerations

### Data Protection
- **Local Data Only**: All data stored locally, no external transmission
- **Chrome Profile**: Session data contained in workspace directory
- **API Access**: CORS restricted to localhost development ports
- **No Credentials**: No API keys or passwords stored in code

### Safe Practices
- **Demo Account**: Always use PocketOption demo account for testing
- **Rate Limiting**: API includes request rate limiting
- **Input Validation**: All user inputs validated before processing
- **Error Logging**: Sensitive information excluded from logs
## Technical Decisions and Considerations (2025-10-06)

Frontend
- Add asset gating in DataAnalysis/useWebSocket; ignore mismatched tick_update events. [planned]
- Automatic source sensing mode (auto/historical/streaming) with status badge; default auto. [planned]
- Throttle chart updates to ~10 fps; coalesce ticks per frame; use series.update for latest/new bars. [planned]
- Timeframe aggregation (tick/1s/5s/1m) with bar builder; clear cache on timeframe change. [planned]

Backend
- Stabilize /api/available-csv-files: robust error handling, always valid JSON responses; Windows path-safe handling. [planned]
- Verify tick payload: { asset, timestamp_ms, price }; enforce per-asset monotonic timestamps; optionally buffer/reorder. [planned]
- Socket.IO config: prefer transport=["websocket"], tune pingInterval/pingTimeout, reconnection backoff, and CORS origins. [planned]

Security/Scale (future)
- TLS/WSS for external, tightened CORS/origin, token-based auth, rate limiting.
- Socket.IO rooms per asset; Redis adapter for multi-node broadcasting and sticky sessions.

References
- TradingView Advanced Charts (Streaming Implementation/Datafeed API) — cache reset, symbol/resolution matching, time violation rules.
- Lightweight Charts — real-time series.update semantics; strict ascending time.
- WebSocket best practices (AlgoCademy) — persistent connections, event handling, reconnection/backoff, performance optimization, scaling, security.
