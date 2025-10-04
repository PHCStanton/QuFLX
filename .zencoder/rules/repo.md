---
description: Repository Information Overview
alwaysApply: true
---

# QuantumFlux Trading Dashboard Information

## Summary
QuantumFlux is a comprehensive trading dashboard for AI-powered binary options trading with real-time data visualization and strategy testing capabilities. The project is currently in Phase 2.5, with a clean architecture based on capabilities-only approach, ready for Phase 3 development of strategy engine and automation.

## Structure
- **capabilities/**: Core trading capabilities framework
- **src/**: Backend source code with adapter, models, and utilities
- **src_new/**: New architecture with domain-driven design
- **gui/**: Frontend dashboard and data visualization tools
- **tests/**: Test suite for capabilities and API endpoints
- **data/**: Historical and real-time trading data
- **strategies/**: Trading strategies and technical indicators

## Language & Runtime
**Language**: Python 3.11 (specifically 3.11.13)
**Runtime**: FastAPI with Uvicorn
**Build System**: Python setuptools
**Package Manager**: pip

## Dependencies
**Main Dependencies**:
- fastapi>=0.110.0: API framework
- selenium>=4.15.0: Web automation
- pandas>=2.0.0: Data processing
- websocket-client>=1.6.0: WebSocket communication
- numpy>=1.24.0: Numerical operations

**Development Dependencies**:
- pytest>=7.4.0: Testing framework
- black>=23.0.0: Code formatting
- flake8>=6.0.0: Linting
- mypy>=1.5.0: Type checking

## Build & Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Start backend server
python backend.py

# Start frontend (in separate terminal)
cd gui/dashboard
pnpm install
pnpm dev
```

## Docker
**Dockerfile**: Dockerfile (multi-stage build)
**Image**: Python 3.11-slim with Chrome for Selenium
**Configuration**: docker-compose.yml with backend and frontend services
**Run Command**:
```bash
docker-compose up -d
```

## Testing
**Framework**: pytest with asyncio support
**Test Location**: tests/ directory
**Naming Convention**: test_*.py
**Configuration**: pytest.ini with markers and coverage settings
**Run Command**:
```bash
pytest
```

## Frontend
**Framework**: React 18 with Vite
**Package Manager**: pnpm
**UI Libraries**: Tailwind CSS, Material UI, Recharts
**Build Command**:
```bash
cd gui/dashboard
pnpm build
```

## Capabilities Framework
**Core Concept**: Modular trading capabilities
**Main Components**:
- base.py: Foundation with Ctx and CapResult classes
- data_streaming.py: Real-time WebSocket data handling
- trade_click_cap.py: Trade execution
- profile_scan.py: User profile scanning
- timestamp_convert_utc.py: Timestamp conversion utility

## API Endpoints
**Base URL**: http://localhost:8000
**Documentation**: http://localhost:8000/docs
**Key Endpoints**:
- GET /status: Connection status
- GET /api/profile: User profile scanning
- POST /api/operations/trade: Trade execution
- WS /ws/data: Real-time WebSocket data stream