# QuantumFlux Trading Platform - Clean Architecture Design

## Architecture Overview

This document outlines the Clean Architecture structure for the QuantumFlux trading platform, following Domain-Driven Design (DDD) principles.

**Last Updated**: October 7, 2025 - Reflects recent architectural improvements including asset filtering, encapsulation fixes, and simplified data flow.

## Core Principles

1. **Dependency Inversion**: Dependencies point inward toward the domain
2. **Separation of Concerns**: Clear boundaries between layers
3. **Domain-Driven Design**: Business logic organized by bounded contexts
4. **Testability**: Each layer can be tested independently
5. **Scalability**: Structure supports future growth and feature additions

## Layer Architecture

```
┌─────────────────────────────────────────┐
│              Presentation               │
│         (API, CLI, GUI)                 │
├─────────────────────────────────────────┤
│              Application                │
│        (Use Cases, DTOs)                │
├─────────────────────────────────────────┤
│             Infrastructure              │
│    (Adapters, Repositories, APIs)       │
├─────────────────────────────────────────┤
│               Domain                    │
│   (Entities, Value Objects, Services)   │
└─────────────────────────────────────────┘
```

## Bounded Contexts

### 1. Trading Context
- **Entities**: Trade, Position, Order
- **Value Objects**: TradeDirection, Amount, Timestamp
- **Domain Services**: TradeExecutionService, RiskCalculationService

### 2. Market Data Context
- **Entities**: Asset, Candle, Indicator
- **Value Objects**: Price, Volume, TimeFrame
- **Domain Services**: PriceAnalysisService, IndicatorCalculationService

### 3. Strategy Context
- **Entities**: Strategy, Signal, Backtest
- **Value Objects**: Confidence, Parameters
- **Domain Services**: SignalGenerationService, StrategyValidationService

### 4. Risk Management Context
- **Entities**: RiskProfile, Limit, Exposure
- **Value Objects**: RiskLevel, Percentage
- **Domain Services**: RiskAssessmentService, PositionSizingService

### 5. Analytics Context
- **Entities**: Performance, Report, Metric
- **Value Objects**: Statistics, Period
- **Domain Services**: PerformanceCalculationService, ReportGenerationService

### 6. Platform Integration Context
- **Entities**: Session, Connection, Account
- **Value Objects**: Credentials, Status
- **Domain Services**: AuthenticationService, ConnectionManagementService

## Directory Structure

```
QuantumFlux/
├── src/
│   ├── domain/
│   │   ├── trading/
│   │   │   ├── entities/
│   │   │   ├── value_objects/
│   │   │   ├── services/
│   │   │   ├── repositories/
│   │   │   └── events/
│   │   ├── market_data/
│   │   ├── strategy/
│   │   ├── risk_management/
│   │   ├── analytics/
│   │   ├── platform_integration/
│   │   └── shared/
│   ├── application/
│   │   ├── use_cases/
│   │   ├── dtos/
│   │   ├── interfaces/
│   │   ├── services/
│   │   └── mappers/
│   ├── infrastructure/
│   │   ├── adapters/
│   │   ├── repositories/
│   │   ├── external_services/
│   │   ├── persistence/
│   │   └── messaging/
│   └── presentation/
│       ├── api/
│       ├── cli/
│       ├── gui/
│       └── web/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── fixtures/
├── config/
│   ├── environments/
│   ├── strategies/
│   └── deployment/
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── user_guide/
│   └── development/
├── scripts/
│   ├── deployment/
│   ├── migration/
│   └── utilities/
├── data/
│   ├── historical/
│   ├── real_time/
│   └── exports/
└── logs/
    ├── application/
    ├── trading/
    └── system/
```

## Benefits of This Structure

1. **Maintainability**: Clear separation makes code easier to understand and modify
2. **Testability**: Each layer can be tested independently with proper mocking
3. **Scalability**: New features can be added without affecting existing code
4. **Flexibility**: Infrastructure can be swapped without changing business logic
5. **Team Collaboration**: Different teams can work on different layers/contexts
6. **Production Ready**: Proper configuration and deployment structure

## Recent Architectural Improvements (October 7, 2025)

### Critical Fixes Implemented

1. **Asset Filtering at Source**
   - **Problem**: Asset filtering happened too late, causing unwanted asset switches
   - **Solution**: Moved filtering to START of `_process_realtime_update()` in capability
   - **Benefit**: Prevents processing of unwanted assets before they enter the system

2. **Eliminated Duplicate Candle Formation**
   - **Problem**: Both backend and frontend were forming candles independently
   - **Solution**: Backend emits fully-formed candles via `candle_update`, frontend displays only
   - **Benefit**: Single source of truth, no granularity mismatch, 70+ lines removed

3. **Fixed Broken Encapsulation**
   - **Problem**: Server directly manipulated capability internals
   - **Solution**: Created public API methods:
     - `set_asset_focus(asset)` / `release_asset_focus()`
     - `set_timeframe(minutes, lock)` / `unlock_timeframe()`
     - `get_latest_candle(asset)` / `get_current_asset()`
   - **Benefit**: Clean separation of concerns, maintainable codebase

4. **Simplified Data Flow**
   - **Before**: Complex multi-step process with tick extraction
   - **After**: Capability → Server (emit candles) → Frontend (display)
   - **Benefit**: Single source of truth, easier to debug and maintain

5. **Backpressure Handling**
   - **Problem**: Frontend could overflow with too much data
   - **Solution**: 1000-item buffer limit with auto-truncation
   - **Benefit**: Prevents memory issues during high-frequency data streams

### Architecture Principles Reinforced

- **Dependency Inversion**: Server depends on capability's public API, not internals
- **Single Responsibility**: Capability handles candle formation, server handles communication
- **Don't Repeat Yourself**: Eliminated duplicate candle logic
- **Separation of Concerns**: Clear boundaries between data processing and presentation

## Migration Strategy

1. Create new directory structure
2. Move existing code to appropriate layers
3. Refactor dependencies to follow Clean Architecture
4. Update import statements and routing
5. Implement proper interfaces and abstractions
6. Update tests to match new structure
7. Update documentation and deployment scripts